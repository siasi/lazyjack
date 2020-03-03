#!/usr/bin/env python


from getpass import getpass,getuser
from subprocess import Popen, PIPE
from collections import namedtuple

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.Utils import formatdate
from email.Encoders import encode_base64
from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT

from rally import RallyService
from cdets import EnclosureTest, CdetsDefect, getCdetsDefects


import smtplib
import sys, re, os

class Logger():
    def __init__(self):
        self.on = True
        self.isVerbose = True

    def turnOn(self):
        self.on = True

    def turnOff(self):
        self.off = False

    def log(self, string):
        if self.on:
	    print string.encode('utf-8').strip()

    def logVerbose(self, string):
        if self.isVerbose:
	    print string.encode('utf-8').strip()

    def isVerboseOn(self):
        return self.isVerbose

logger = Logger()

def log(string):
    logger.log(string)

def logVerbose(string):
    logger.logVerbose(string)


class UserStory():
    def __init__(self, rallyUs):
        self.rallyUs = rallyUs
        self.notComplianceReasons = []

    def isAccepted(self):
        return self.rallyUs.ScheduleState == "Accepted"

    def isCompliant(self, iterationAccepted=True):
        if self.isAccepted():
            logVerbose("US" + self.rallyUs.FormattedID + " is Accepted")
            if self.rallyUs.DefinitionOfDone == None:
                self.notComplianceReasons.append('DoD not set')
                return False
            if self.rallyUs.DefinitionOfDone == "Product Changed":
                return self.auditProductChanged()
            elif self.rallyUs.DefinitionOfDone == "No Product Change":
                return self.auditProductNotChanged()
        else:
            logVerbose("Iteration Accepted but US" +  self.rallyUs.FormattedID + " not")
            self.notComplianceReasons.append('US should be Accepted')
            return False
        return True
	
    def isScheduled(self):
        if not self.rallyUs.Release:
	    logVerbose("WARNING: " + self.rallyUs.FormattedID + " has not Release field set")
	    self.notComplianceReasons.append('US has not Release field set')
	    return False
	    
	return True
		
    def isScheduledFor(self, releaseName):
	return self.rallyUs.Release.Name == releaseName
	
    def mustBeIgnored(self):
        #print "Ignoring ", self.rallyUs.FormattedID, " - ", self.rallyUs.Name
        return self.rallyUs.Name.strip().startswith("[A--]")

    def checkAllTasksCompleted(self):
        allTasksCompleted = True
        #print self.rallyUs.FormattedID
        for task in self.rallyUs.Tasks:

            if task.State == "Completed":
                state = "COMPLETE"
            else:
                state = "** NOT COMPLETE **"
                allTasksCompleted = False

            logVerbose("  " + task.FormattedID + "[" + state + "]:" + task.Name)

        if not allTasksCompleted:
            self.notComplianceReasons.append("Some tasks not completed")

        return allTasksCompleted

    def checkTasksDefinedAndAllCompleted(self):
        if not us.Tasks:
            logVerbose("  [ ** MISSING TASKS ** ] ")
            self.notComplianceReasons.append("Missing tasks")
            return False

        return self.checkAllTasksCompleted()

    def checkAllTestCasesPassed(self):
        allTestCasesPassed = True

        for tc in self.rallyUs.TestCases:
            if tc.LastVerdict == "Pass":
                verdict = "PASSED"
            else:
                verdict = "** FAILED **"
                allTestCasesPassed = False
            logVerbose("  " + tc.FormattedID + "[" + verdict + "]:" + tc.Name)

        if not allTestCasesPassed:
            self.notComplianceReasons.append("Some test cases not passed")

        return allTestCasesPassed

    def checkTestCasesDefinedAndPassed(self):
        if not self.rallyUs.TestCases:
            logVerbose("  [ ** MISSING TEST CASES ** ] ")
            self.notComplianceReasons.append("Missing test cases")
            return False

        return self.checkAllTestCasesPassed()

    def auditProductChanged(self):
        logVerbose(self.rallyUs.FormattedID + ": %s" %(self.rallyUs.Name))

        tasksOK = self.checkAllTasksCompleted()
        testCasesOK = self.checkTestCasesDefinedAndPassed()

        return tasksOK and testCasesOK

    def auditProductNotChanged(self):
        logVerbose(self.rallyUs.FormattedID + ": %s" %(self.rallyUs.Name))
        return self.checkAllTasksCompleted()

pattern = re.compile("CSC[a-z][a-z][0-9][0-9][0-9][0-9][0-9]")

def defectWithoutCdetsId(defect):
    #print "Type is", type(defect.Name) 
    name = defect.Name#.encode('utf-8','ignore').strip()
    return pattern.search(name)







class Iteration():

    def __init__(self, iteration, team, releaseName):
        self.iteration = iteration
        self.team = team
        self.notCompliantUs = []
        self.notCompliantDefects = []
        self.invalidDefects = []
	self.releaseName = releaseName

    def get_name(self):
        return self.iteration.Name
	
	
    name = property(get_name)

    def audit(self):
        logger.log("Audit User Stories")
        usInIteration = rally.getUsForIteration(self.iteration, self.releaseName)
        self.notCompliantUs = self.auditUserStories(usInIteration)
        
	logger.log("Audit Defects")
        defectsInIteration = rally.getDefectsForIteration(self.iteration)
        self.notCompliantDefects, self.invalidDefects = self.auditDefects(defectsInIteration)
	
        self.passed = len(self.notCompliantDefects) == 0 and len(self.invalidDefects) == 0 and len(self.notCompliantUs) == 0

    def auditUserStories(self, usInIteration, mustBeAccepted=True):
        if usInIteration.errors:
            print "Error getting data from Rally", usInIteration.errors
            for error in usInIteration.errors:
                print error
            sys.exit(1);

        notCompliantUs=set()
        for rallyUs in usInIteration:
            us = UserStory(rallyUs)
	    if us.mustBeIgnored():
	        continue
		
	    if not us.isScheduled():
	        logVerbose(rallyUs.FormattedID + " [ NOT SCHEDULED ] " + rallyUs.Name)
	        notCompliantUs.add(us)
		continue
		
	    if not us.isScheduledFor(self.releaseName):
	        logVerbose(rallyUs.FormattedID + " [ NOT SCHEDULED FOR RELEASE ] " + rallyUs.Name)
	        continue
		
            if not us.isCompliant():
	        str = rallyUs.FormattedID + " [ NOT COMPLIANT ] " + rallyUs.Name
                logVerbose(str)
                notCompliantUs.add(us)
            else:
                logVerbose(rallyUs.FormattedID + " [ COMPLIANT ] " + rallyUs.Name)
        return notCompliantUs
	
    def auditDefects(self, defects):
        cdetsIdToDefect = {}
        invalidDefects=[]
        notCompliantDefects=set()
        for defect in defects:
	    #print defect.Release.Name
            if defect.Release != None and defect.Release.Name != self.releaseName:
	        continue
            #print "Formatted ID:" + defect.FormattedID
	    #print "Name:", defect.Name
	    if defect.Name.strip().startswith("[A--]"):
                print "Ignoring defect", defect.FormattedID
	        continue
	    
            cdetsIdFound = defectWithoutCdetsId(defect)
            if not cdetsIdFound:
                print "Missing CDETS ID in name of defect " + defect.FormattedID
                invalidDefects.append(defect)
            else:
                #print defect.Name.encode().strip()
                #print re.findall(pattern, defect.Name.encode().strip())
                cdetsId = re.findall(pattern, defect.Name)[0]

                cdetsIdToDefect[cdetsId] = defect

        if not cdetsIdToDefect:
            return (set(), set())

        cdetsIds = cdetsIdToDefect.keys()
        for bug in  getCdetsDefects(cdetsIds):

            bug.rallyDefect = cdetsIdToDefect[bug.cdetsId]

            if bug.rallyDefect.ScheduleState != "Accepted":
                bug.notComplianceReasons = ["Rally defect should be in Accpeted state"]
                notCompliantDefects.add(bug)
                result = " NOT VALID "
                #print "Bug " + bug.cdetsId + " is not valid"
            elif not bug.isCompliantWithDoD():
                notCompliantDefects.add(bug)
                result = " NOT VALID "
                #print "Bug " + bug.cdetsId + " is not VALID"
            else:
                result = " VALID "
                #print "Bug " + bug.cdetsId + " is VALID"

            defect = cdetsIdToDefect[bug.cdetsId]
	    #msg = u' '.join([defect.FormattedID, " [", result, "] ", defect.Name]).encode('utf-8').strip()
	    msg = u' '.join([defect.FormattedID, " [", result, "] ", defect.Name]).strip()
            logVerbose(msg)

        return notCompliantDefects, invalidDefects

    def auditResult(self):
        result = ""
        if self.notCompliantDefects or self.notCompliantUs:
            result = "NOT PASSED"
        else:
            result = "PASSED"

        if self.invalidDefects:
            result = result + " [ INVALID ]"

        return result

    def __dodToStr(self, dod):
        if dod == None:
            return "NOT SET"
        else:
            return str(dod)

    def printReport(self, out):

        if self.notCompliantUs:
            #out.dump("")
            #out.dump("Following US are not compliant to TL9K: ")
            #out.dump("")
            for us in self.notCompliantUs:
                out.dump("")
                out.dump("  " + us.rallyUs.FormattedID + ": %s" %(us.rallyUs.Name))
                out.dump("    DOD: " + self.__dodToStr(us.rallyUs.DefinitionOfDone))
                out.dump("    STATE: " + us.rallyUs.ScheduleState)
                out.dump("    REASONS:")
                for reason in us.notComplianceReasons:
                    out.dump("      - " + reason)

        if self.notCompliantDefects:
            #out.dump("")
            #out.dump("Following Defects are not compliant to TL9k: ")
            #out.dump("")
            for defect in self.notCompliantDefects:
                out.dump("")
                out.dump("  " + defect.rallyDefect.FormattedID + ": %s" %(defect.rallyDefect.Name))
                out.dump("    STATE: " + defect.rallyDefect.ScheduleState)
                out.dump("    REASONS:")
                for reason in defect.notComplianceReasons:
                    out.dump("      - " + reason)

        if logger.isVerboseOn() and self.invalidDefects:
            #out.dump("")
            #out.dump("Following defects does not have a refecence to a CDEST bug: ")
            #out.dump("")
            for rallyDefect in self.invalidDefects:
                out.dump("")
                out.dump("  " + rallyDefect.FormattedID + ": %s" %(rallyDefect.Name))
		out.dump("    REASONS: Defect Name has not a reference to a valid CDETS ID")

def itId(n):
    if n  < 10:
        return '0' + str(n)
    else:
        return str(n)


class GroupResult():

    def __init__(self, mail):
        self.mail = mail
        self.fileName = mail.split('@')[0]
        if os.path.exists(self.fileName):
            os.remove(self.fileName)

        self.file = open(self.fileName, "w")

    def dump(self, str):
	str = str.encode('utf-8').strip()
        self.file.write(str + "\n")

    def close(self):
        self.file.close()

def sendReport(send_to, subject, reportFile, zipFile=""):
    '''Send a HTML report by mail.

    send_to is the address of the mail
    subject is the subject of the mail
    reportFile is the HTML report sent as body of the mail
    zipFile is the name of an optional zip file that is attached to the mail

    The mail is sent from the email address of the user running the function.

    An error message is printed in case of issues sending the mail.
    '''

    send_from = os.getenv('USER') + "@cisco.com"
    
    msg = MIMEMultipart()
    msg["From"] = send_from
    msg["To"] = send_to
    msg["Cc"] = "siasi@cisco.com"
    #msg["Bcc"] = "siasi@cisco.com"
    msg["Subject"] = subject
    msg['Date'] = formatdate(localtime=True)

    body = MIMEText(open(reportFile).read(), 'plain')
    body['Content-Transfer-Encoding']='quoted-printable'

    msg.attach(body)

    if zipFile != "":
        attachment = MIMEBase('application', 'x-zip-compressed', name=os.path.basename(zipFile))
        attachment.set_payload(open(zipFile).read())
        encode_base64(attachment)
        msg.attach(attachment)


    server = smtplib.SMTP('localhost')

    try:
        print "Going to send email from", send_from, " to ", send_to 
        failed = server.sendmail(send_from, [send_to, "siasi@cisco.com"], msg.as_string())
        server.close()
    except Exception, e:
        errorMsg = "Unable to send email. Error: %s" % str(e)
        print errorMsg

	
def brush(domains, opt):
    
    for domain in domains:
        outfile = GroupResult(domain.email)
        iterations = [Iteration(rallyIteration, rallyIteration.Project.Name, opt.releaseName) for rallyIteration in domain.iterations]
	
	print "For group", domain.email, "going to audit", len(iterations), "iterations"
	
        for it in iterations:
            print "AUDIT ITERATION: " + it.name + " "
            it.audit()
            print "AUDIT COMPLETED ITERATION: " + it.name + " " + it.auditResult()
            it.printReport(outfile)
        outfile.close()

    if opt.suppressMail:
        return
	
    for domain in domains:
        fileName = domain.email.split('@')[0]
        if os.path.exists(fileName) and os.stat(fileName).st_size > 0:
            print "Sending report to " + domain.email
            sendReport(domain.email, "Audit Result for release " + opt.releaseName + " group " + domain.email, fileName)
        #sendReport("siasi@cisco.com", "Audit Result for group " + domain.email, fileName)

if __name__ == "__main__":
    
    import __init__ as lazyjack
    parser = OptionParser(prog="review", usage="%prog [options] defectId", description="", version=lazyjack.opt_ver)
    parser.add_option("-s", "--suppress", action="store_true", dest="suppressMail",
                      help="Suppress mail notification")
    parser.add_option("-r", "--release-name", action="store", dest="releaseName",
                      help="The name of the release to be audited")
    (opt, args) = parser.parse_args()
    
    rally = RallyService()
    "Drake - 9.6.3"
    #
    # There is the need to filter the iterations by project name.
    # This is bcause iterations related to containers projects (DE Team) is returned.
    #
    
    teamsCri = ["CM Functional Team"]#, "NE/FM/PM Functional Team"]
    teamsMax = ["NET Functional Team", "GW Functional Team"]
    teamsGio = ["Software Platform Functional Team", "System Platform Functional Team"]
    allTeams = teamsCri + teamsMax + teamsGio
    
    Group = namedtuple('Group', 'email teams')
    groups = [Group("gregorim@cisco.com", teamsMax), Group("gguerrer@cisco.com", teamsGio), Group("clapicci@cisco.com", teamsCri)]
    
    Domain = namedtuple('Domain', 'email iterations')
    domains = []
    for group in groups:
        iterations = set([it for it in rally.getPastIterations(opt.releaseName, group.teams) if it.Project.Name in  group.teams])
	print "There are", len(iterations), "iterations to audit for group", group.email
	#for iteration in iterations:
	#    print iteration.FormattedID, iteration.Name, iteration.Project.Name
	domains.append(Domain(group.email, iterations))
    
    #print "Going to audit", len(iterations), "iterations"
    #for iteration in iterations:
    #    print iteration.Name
    #sys.exit(1)
    brush(domains, opt)
    print "Audit completed"
