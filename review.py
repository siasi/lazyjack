"""This script can open a code review in PRRQ.
It allows to open a review performing all steps required by quality process.
It is supposed to run in a Clear Case view from which diff for the review are collected.
   
The script performs following steps:
   
 - check for missing cc_mkelem (list private files for which the user is probably missing cc_mkelem or cc_mkdir)
 - run static analysis for Java code and show results
 - format the Java code
 - open review in PRRQ
 - assign reviewers

This script is pare of the Lazy Jack suite.

Author: siasi@cisco.com 
Contributors: ceplacan@cisco.com
  
Date: November 2012

"""

import sys
import re

from sa import *
from cc import *

from subprocess import Popen, PIPE
from subprocess import call
from optparse import OptionParser

import requests, json

def parseReviewId(proc):
    bugId = None
    for line in proc.stdout.readlines():
        #print line
        line = line.strip()
        if line.startswith("Your review has been created successfully and"):
            tokens = line.split()
            #print "Tokens are ", len(tokens)
            if len(tokens) >= 23:
                bugId = tokens[22]
                bugId = bugId[1:-1]
    return bugId

def openReviewOrDie(params):

    cmdTokens = [];
    cmdTokens.append('prrq-new')
    cmdTokens.append('-q')
    cmdTokens.append(params.queue)
    cmdTokens.append('-b')
    cmdTokens.append(params.bugId)
    cmdTokens.append('-o')
    cmdTokens.append(params.owner)
    cmdTokens.append('-v')
    cmdTokens.append(params.view)
    cmdTokens.append('-s')
    cmdTokens.append(params.viewServer)
    cmdTokens.append('-c')
    cmdTokens.append('-vn')
    cmdTokens.append('/vob/visionway')
    cmdTokens.append('-scm')
    cmdTokens.append('CC-Tools')
    cmdTokens.append('-d')
    cmdTokens.append(params.commentFile)

    cmd = " ".join(cmdTokens)
    proc = runCommand(cmd)
    return parseReviewId(proc)


def assignReviewersOrDie(bugid, reviewers):
    cmdTokens = [];
    cmdTokens.append('prrq-revaction')
    cmdTokens.append('-a')
    cmdTokens.append('assign')
    cmdTokens.append('-b')
    cmdTokens.append(bugid)
    cmdTokens.append('Reviewers')
    cmdTokens.append(reviewers)

    cmd = " ".join(cmdTokens)
    runCommand(cmd)

def updateDescriptionWithBugPredition(descriptionFile):
    with open(descriptionFile, "r+") as f:
        old = f.read()
        if not old.startswith("WARNING: review this changes carefully"):
            f.seek(0)
	    f.write("WARNING: Review this changes carefully!\n")
	    f.write("         Probability to inject a bug is very high!\n\n")
	    f.write("")
            #f.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            #f.write("!!!!!!!!                    WARNING              !!!!!!!\n")
            #f.write("!!!!!!! PROBABILITY TO INJECT A BUG IS VERY HIGH !!!!!!!\n")
            #f.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            f.write(old)
        f.close()

def parseBugPrediction(riskToInjectABug, descriptionFile):
    if riskToInjectABug:
        print "[ ... ] There is HIGH RISK to inject a bug with this changes: reviewers will be notified."
	updateDescriptionWithBugPredition(descriptionFile)
    #else:
    #    print "[ ... ] There is low risk to inject a bug."

def bugPrediction(cs, description):
    url = "http://gpk-nmtg-cpo03:8089/prediction"
    payload = {'change_set': cs.coFiles}
    headers = {'content-type': 'application/json'}

    try:
        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        if resp.status_code == 200:
	    #print "Respons is", resp.content
            parseBugPrediction(bool(int(resp.content)), description)
        else:
            print "[ ... ] Error in Prediction Service response"
            print resp.content
    except requests.exceptions.ConnectionError: 
        print "[ ... ] Error contacting the Prediction Service"
        #Should notify the administrator
    

def createReview(cs, viewName, ljAudit):

    print "[ 1/5 ] Check missing cc_mkelem ..."
    checkMissingCcMkElem()
    print "[ 2/5 ] Run Static Analysis ..."
    #runSa(cs)
    checkNoSaInDiff(cs, ljAudit)
    print "[ 3/5 ] Format Code ..."
    formatCode(cs)
    
    params = ljAudit.getReviewParameters()
    bugPrediction(cs, params.commentFile)
    
    print "[ 4/5 ] Open review, please wait ..."
    reviewId = openReviewOrDie(params)

    ljAudit.setValue('reviewId', reviewId)
    ljAudit.setValue('review', "OPEN")

    print "[ ... ] Review open. Review ID =", reviewId
    if params.reviewers != None and (reviewId == None):
        print "Unable to parse the review Id: cannot assing reviewers."
        sys.exit(-1)

    #if prediction == "VERY HIGH":
    #  sendReport("siasi@cisco.com", "[WARNING] Review " + reviewId + " Requires Highest Attention", "/users/siasi/attention.txt", reviewId)

    if params.reviewers != None:
        print "[ 5/5 ] Assign reviewers, please wait ..."
        assignReviewersOrDie(reviewId, params.reviewers)
        ljAudit.setValue('review', "ASSIGNED")
    else:
        print "[ 5/5 ] No reviewers to assign. Please connect to PRRQ and assign the reviewers."

def editComment(descriptionFile):

    try:
        retcode = call("vi " + descriptionFile, shell=True)
        if retcode != 0:
            print >>sys.stderr, "Editing of review comment failed"
            sys.exit(retcode)
        #else:
        #  print >>sys.stderr, "Editing of review comment successful"
    except OSError, e:
        print >>sys.stderr, "Editing of review comment failed:", e
        sys.exit(-1)

    return descriptionFile

def createCommentFile(descriptionFile, comment):
    file = open(descriptionFile, "w")
    file.write(comment)
    file.close()
    return descriptionFile

def parseArguments():
    parser = OptionParser("usage: %prog [options] <CDETS BugId> [reviewers list (csv)]")
    parser.add_option("-d", "--description", action="store_true", dest="description",
                    help="provide a description", metavar="FILE")

    (options, args) = parser.parse_args()

    if len(args) >= 1:
        bugId = args[0]
        #parser.error("incorrect number of arguments: missing CDETS BugId")
        #sys.exit(-1)
    else:
        bugId = None

    if len(args) >= 2:
        reviewers = args[1]
    else:
        reviewers = None

    return (bugId, reviewers)

def editIsRequired(comment):
    if comment != None:
        print "[ ... ] Current review comment is the following:"
        print "[ ... ]"
	for line in comment.split('\n'):
            print "[ ... ]   ", line
        print "[ ... ]"

        if len(comment) < 10:
            print "[ ... ] The comment must be at least 10 characters long."
            raw_input("[ ... ] Press Enter to start editing the review comment.")
            return True

        return askConfirmation("[  ?  ] Do you want to edit the comment?")
        #wantToEdit = raw_input("Do you want to edit the comment? (Y/N) [Y]")
        #return wantToEdit == 'y' or wantToEdit == 'Y' or wantToEdit == ""
    else:
        raw_input("[ ... ] Press enter to start editing the review comment")
    return True

def askParameter(message, defaultValue):
    if defaultValue == None:
        defaultValue = raw_input(message + ": ")
    else:
        newValue = raw_input(message + " [%s]: " % (defaultValue))
        if newValue != "":
            defaultValue = newValue
    return defaultValue

def isUserValid(id):
    proc = Popen("id " + id, shell=True, stdout=PIPE, stderr=PIPE)
    return proc.wait() == 0

def askReviewers(reviewers):
    while True:
        #reviewers = raw_input("Please provide reviewers (list of user id separated by comma): ")
        reviewers = askParameter("[ ... ] Please provide reviewers (list of user id separated by comma)", reviewers)
        if reviewers.startswith(',') or reviewers.endswith(','):
            print "[ ... ] Cannot start or end with comma."
            continue
        ids = [id.strip() for id in reviewers.split(',')]
        invalidIds = [id for id in ids if not isUserValid(id)]
        if invalidIds:
            print "[ ... ] Following user id are not valid: ", invalidIds
        else:
            return ','.join(ids)

def askBugId(bugId):
    while True:
        bugId = askParameter("[  ?  ] Please provide Bug ID", bugId)
        command = "findcr -w Identifier,Headline -i " + bugId
        proc = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        if proc.wait():
            print "[ ... ] " + bugId + " is not a valid Bug ID."
            bugId = None
            continue
        pattern = re.compile("^No ")
        message = proc.stdout.readlines()[0].strip()
        match_noexistid = pattern.search(message)
        if match_noexistid:
            print "[ ... ] Bug ID not exist ", message 
            continue
        print "[ ... ] Bug ID is valid: ", message
        #if askConfirmation("Bug ID is correct?"):
        return bugId


def getDefaultQueue(audit):
    defaultQueue = audit.getValue('queue')
    if audit.getValue('queue') == None:
        branchInfo = {}
        if fillBranchInfo(branchInfo, True) and 'PRRQ_QUEUE' in branchInfo:
            defaultQueue = branchInfo['PRRQ_QUEUE']
    return defaultQueue

def getReviewParameters(viewName):
    ljAudit = readLazyJackViewAudit(viewName)
    ljAudit.setValue('review', "STARTED")

    (commitBugId, commitComment) = readClearCaseViewAudit(viewName)

    if commitBugId != None:
        bugId = commitBugId
    else:
        bugId = ljAudit.getValue('bugId')

    bugId = askBugId(bugId)
    ljAudit.setValue('bugId', bugId)

    if commitComment != None:
        createCommentFile(ljAudit.commentFile, commitComment)

    while editIsRequired(ljAudit.getComment()):
        editComment(ljAudit.commentFile)

    defaultQueue = getDefaultQueue(ljAudit)
    queue = askParameter("[  ?  ] Please provide PRRQ queue", defaultQueue)
    ljAudit.setValue('queue', queue)

    reviewers = ljAudit.getValue('reviewers')
    reviewers = askReviewers(reviewers)
    ljAudit.setValue('reviewers', reviewers)
    return ljAudit


def createReviewForSql(changeSet, view, audit):
    "Create a new review on sql specific queue."
    sqlFiles = changeSet.filterForSql()
    if sqlFiles:
        print "[ ... ] Cloning review for DB migration. Please wait."
        oldQueue = audit.getValue("queue")
        audit.setValue("queue", "cpo-dbmigration")
        createReview(changeSet,view, audit)
        audit.setValue("queue", oldQueue)

#
# BEGIN
#
if __name__ == "__main__":
    viewName = runInCcViewOrDie()

    import __init__ as lazyjack
    parser = OptionParser(prog="review", usage="%prog [options]", description=__doc__, version=lazyjack.opt_ver)
    (opt, args) = parser.parse_args()	   
    cs = getChangeSet()
    if cs.isEmpty():
        print "Changeset is empty: nothing to review."
        sys.exit(-1)

    #(bugId, reviewers) = parseArguments()

    ljAudit = getReviewParameters(viewName)
    createReview(cs, viewName, ljAudit)
    createReviewForSql(cs ,viewName, ljAudit)
    print "[ ... ] Done. Good luck!"
