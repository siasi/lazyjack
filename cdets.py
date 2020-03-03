"""This module contains utilities for interaction with Cdets.

   Author: siasi@cisco.com

"""

import re
from cc import runCommand
from subprocess import Popen, PIPE, STDOUT
    
def getCdetsDefects(cdetsIds):
    "Return the list of CdetsDefect corresponding to the passed list of CDETS Bug IDs."

    command = "findcr -D \$ -w Identifier,Status,Note-title,Attachment-title,To-be-fixed,Engineer -i " + ','.join(cdetsIds)

    proc = runCommand(command)
    return [lineToBug(line) for line in  proc.stdout.readlines() if line.startswith('CSC')]

def lineToBug(line):
    fields = line.split("$")
    bug = CdetsDefect(fields[0])
    bug.status = fields[1]
    bug.notes = fields[2]
    bug.attachments = fields[3]
    bug.toBeFixed = fields[4]
    bug.engineer = fields[5]
    return bug

class Version():
    def __init__(self, maj, min, pat, bui):
        self.val = {}
        self.val['major'] = int(maj)
	self.val['minor'] = int(min)
	self.val['patch'] = int(pat)
	self.val['build'] = int(bui)

    def __rsub__(self, other):
        majorDiff = self.val['major'] - other.val['major']
        if majorDiff:
            return majorDiff
	
	minorDiff = self.val['minor'] - other.val['minor']
        if minorDiff:
            return minorDiff
	    
	patchDiff = self.val['patch'] - other.val['patch']
        if patchDiff:
            return patchDiff
	    
        buildDiff = self.val['build'] - other.val['build']
        if buildDiff:
            return buildDiff
	    
        return 0
	
    def __repr__(self):
        return self.__str__()
	
    def __str__(self):
        return "%(major)03d.%(minor)03d(%(patch)03d.%(build)03d)" % self.val
        #return str(self.major) + '.' + str(self.minor) + '(' + str(self.patch) + '.' + str(self.build) + ')'
     

def toVersion(line):
    line = line.replace('(', '.')
    line = line.replace(')', '.')
    v = line.split('.')

    return Version(v[0], v[1], v[2], v[3])

def compareVersions(first, second):
    "Sort the files by score."

    return first - second
    	    

class CdetsService():
    cmdFindValues = "cdets -p CSC.embu -r ctm -m "
    VERSION_PATTERN = re.compile("\d{3}\.\d{3}\(\d{3}\.\d{3}\)")
    
    def getBug(self, id):
        return getCdetsDefects([id])[0]

    def getLatestApplyTo(self, n):
        cmd = self.__class__.cmdFindValues + "Apply-to"
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        (stdoutdata, stderrdata) = proc.communicate()
        #print stdoutdata
        if proc.poll() == 0:
            res = [toVersion(line) for line in stdoutdata.split('\n') if re.match(self.__class__.VERSION_PATTERN, line)]
            res.sort(compareVersions)
            return  [str(v) for v in res[:n]]
	    
        return []
	
    def getValidValues(self, field):
        cmd = self.__class__.cmdFindValues + field
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        (stdoutdata, stderrdata) = proc.communicate()
	
        if proc.poll() == 0:
            res = [line for line in stdoutdata.split('\n') if len(line) > 0]
            res.sort()
            return  res
	         
        return []
	
    def getDevEscapeActivityValues(self, isDevEscape):
        allValues = self.getValidValues('Dev-escape-activity')
        if isDevEscape:
            return filter(lambda value: value.startswith('Not'), allValues)
        else:
            return filter(lambda value: not value.startswith('Not'), allValues)

    def resolveBug(self, cdetsDefect, params):
        cmd = self.__prepareUpdateCommand(cdetsDefect, params)
        runCommand(cmd)

    def __prepareUpdateCommand(self, cdetsDefect, params):
        #load data
        applyTo = '"009.006(003.247)"'
        toBeFixed = "009.006(003.247)"
        origin = '"Code / Implementation"'
        devEscape = "N"
        dEActivity = '"Not-A-Dev-Escape"'
        inReleased = "Y"
        softChanged = "Y"
        releasedCode = "Y"
        breakage = "N"
        status = "R"

        #run command
        cmdTokens = [];
        cmdTokens.append("fixcr -i")
        cmdTokens.append(cdetsDefect.cdetsId)
        cmdTokens.append("Apply-to")
        cmdTokens.append('"' + params.applyTo + '"')
        cmdTokens.append("Bug-origin")
        cmdTokens.append('"' + params.origin + '"')
        cmdTokens.append("Software-changed")
        cmdTokens.append("Y")
        cmdTokens.append("Released-code")
        cmdTokens.append('"' + params.inReleasedCode + '"')
        cmdTokens.append("Breakage")
        cmdTokens.append('"' + params.breackage + '"')
        cmdTokens.append("Dev-escape-resolver-opinion")
        cmdTokens.append('"' + params.isDevEscape + '"')
        cmdTokens.append("Dev-escape-activity")
        cmdTokens.append('"' + params.devEscapeActivity + '"')
        cmdTokens.append("Status")
        cmdTokens.append(status)
        
        if not cdetsDefect.isReadyToMoveToRState():
            #print "Adding Engineer and tobefixed"
            cmdTokens.append("Engineer")
            cmdTokens.append(getuser())
            cmdTokens.append("To-be-fixed")
            cmdTokens.append('"' + params.applyTo + '"')

        return " ".join(cmdTokens)

class CdetsDefect:
    """Represents a defect in CDETS"""
    def __init__(self, cdetsId):
        self.cdetsId = cdetsId
        self.enclosures = []
        #self.validated = False
        self.status = ""
        self.notes = ""
        self.attachments = ""
        self.notComplianceReasons = []
	self.toBeFixed = ""
	self.engineer = ""

    def __validateEnclosures(self):
        """Analyize enclosures and validate their compliance with DPAI requirements."""
        
        enclosureTitles = self.notes + " " + self.attachments
        #print enclosureTitles
        self.enclosures = []
        self.enclosures.append(EnclosureTest('Code Review', '[cC]ode-[rR]eview', enclosureTitles))
        self.enclosures.append(EnclosureTest('Static Analysis', '[sS]tatic-[aA]nalysis', enclosureTitles))
        self.enclosures.append(EnclosureTest('Unit Test', '[uU]nit-[tT]est', enclosureTitles))
        #self.enclosures.append(EnclosureTest('R Comment', '[rR][-]{0,1}[Cc]omment[s]{0,1}.*', enclosureTitles))
        if self.getMissingEnclosures():
            names = [enclosure.name for enclosure in self.getMissingEnclosures()]
            self.notComplianceReasons = ["Missing Enclosures: " + ", ".join(names)]

    def isResolved(self):
        "Return true if the bug is in R, V or M state."
        return "RVM".count(self.status)

    def hasAllRequiredEnclosureForRState(self):
        "Return true is the bug is has all enclosures required to move the bug in R state."
        self.__validateEnclosures()
        return len(self.getMissingEnclosures()) == 0
	
    def isReadyToMoveToRState(self):
        return self.toBeFixed != "" and self.engineer != ""

    def getMissingEnclosures(self):
        "Return the list of DPAI enclosures that are missing."
        return [enclosure for enclosure in self.enclosures if enclosure.absent()]

    def isCompliantWithDoD(self):
        "Return true is the bug is compliant with the Definition of Done."
        self.__validateEnclosures()
        if self.isResolved():
            #print "Bug " + self.cdetsId + " is resolved"
            return len(self.getMissingEnclosures()) == 0

        elif "DJHCU".count(self.status):
            #print "Bug " + self.cdetsId + " is DJH"
            return True

        else:
            self.notComplianceReasons.append("Bug not in final state")
            #print "Bug " + self.cdetsId + " is not in final state DJH"
            return False

class EnclosureTest(object):
    "Represent a test on a DPAI enclosure."
    
    def __init__(self, name, pattern, text):
        self.name = name
        self.pattern = re.compile(pattern)
        self.text = text

    def absent(self):
        "Return True if the enclosure is absent, False otherwise."
        return not self.present()

    def present(self):
        "Return True if the enclosure is present, False otherwise."
        return self.pattern.search(self.text) != None
