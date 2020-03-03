#!/usr/bin/env python

"This module contains utilities for interaction with ClearCase."
#
# author: siasi@cisco.com
#

import sys, os, socket
import reindent
from subprocess import Popen, PIPE, STDOUT
from subprocess import call
from ConfigParser import SafeConfigParser, NoOptionError
from getpass import getuser
from scan_view import search_new_elems

class ViewAudit:

    def __init__(self, viewName, auditLocation):
        self.viewName = viewName
        userId = viewName.split('-')[0]

        viewPath = self._getViewPath(viewName)
        if viewPath == None:
            print "Unable to get view path for view name " + viewName
            sys.exit(1)

        self.ccViewFile = viewPath + auditLocation
        self.folder = os.path.split(self.ccViewFile)[0]
        self.initParser()

    def initParser(self):
        self.config = SafeConfigParser()
        if os.path.exists(self.ccViewFile):
            f = open(self.ccViewFile)
            self.config.readfp(FakeSecHead(f))
            f.close()

    def init(self):
        self.createFolder()
        self.config = SafeConfigParser()
        if os.path.exists(self.ccViewFile):
            mode = "r"
        else:
            mode = "w+"
        f = open(self.ccViewFile, mode)
        self.config.readfp(FakeSecHead(f))
        f.close()


    def exists(self):
        return os.path.exists(self.ccViewFile)


    def createFolder(self):
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def _getViewPath(self, viewName):
        viewFolder = None

        cmd = "/usr/atria/bin/cleartool lsview | grep " + viewName
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)

        for line in proc.stdout.readlines():
            line = line.strip()
            tokens = line.split()
            if tokens[1] == viewName:
                viewFolder = tokens[2]

        #print "View folder is ", viewFolder
        return viewFolder

    def getValue(self, name):
        if not self.exists():
            return None

        try:
            value = self.config.get('asection', name, "").strip(' \t\n')
            if value != "":
                return value
        except NoOptionError, e:
            pass
        return None

    def setValue(self, name, value):
        self.config.set('asection', name, value)
        with open(self.ccViewFile, "w") as configfile:
            self.config.write(configfile)
            configfile.close()

class ReviewArguments():
    pass

class LazyJackAudit(ViewAudit):

    def __init__(self, viewName):
        ViewAudit.__init__(self, viewName, "/cisco/lazyjack/ViewAudit")
        self.commentFile = self.folder + "/reviewComment.txt"
        self.diffFile = self.folder + "/code.diff"
        self.partial = self.folder + "/commit.partial"
        self.pysahtml = self.folder + "/pysa.html"
        self.pysatxt = self.folder + "/pysa.txt"
        self.saDiffReport = self.folder + "/sa_diff_report.html"

    def getComment(self):
        if os.path.exists(self.commentFile):
            f = open(self.commentFile)
            comment = f.read()
            f.close()
            return comment
        else:
            return None

    def destroy(self):
        if os.path.exists(self.commentFile):
            os.remove(self.commentFile)
        if os.path.exists(self.ccViewFile):
            os.remove(self.ccViewFile)
        if os.path.exists(self.diffFile):
            os.remove(self.diffFile)
        if os.path.exists(self.partial):
            os.remove(self.partial)
        if os.path.exists(self.pysahtml ):
            os.remove(self.pysahtml)
        if os.path.exists(self.pysatxt):
            os.remove(self.pysatxt)
	if os.path.exists(self.saDiffReport):
            os.remove(self.saDiffReport)

    def reviewRequested(self):
        return self.exists() and (self.getValue("review") == "OPEN" or self.getValue("review") == "ASSIGNED")

    def getReviewParameters(self):
        params = ReviewArguments()
        params.bugId = self.getValue('bugId')
        params.reviewers = self.getValue('reviewers')
        params.queue = self.getValue('queue')
        params.commentFile = self.commentFile

        params.view = self.viewName
        params.owner = getuser()
        params.viewServer = socket.gethostname()
        return params


class FakeSecHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[asection]\n'
    def readline(self):
        if self.sechead:
            try: return self.sechead
            finally: self.sechead = None
        else: return self.fp.readline()


def readClearCaseViewAudit(viewName):
    audit = ViewAudit(viewName, "/cisco/audit/ViewAudit")

    bugId = audit.getValue('bugid')
    comment = audit.getValue('change_comment')
    return (bugId, comment)


def runInCcViewOrDie():
    cmdTokens = [];
    cmdTokens.append('/usr/atria/bin/cleartool')
    cmdTokens.append('pwv')

    cmd = " ".join(cmdTokens)

    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    viewInfo = [info.strip().split(':')[1].strip() for info in proc.stdout.readlines()]

    if not all(map(lambda x: x != "** NONE **", viewInfo)):
        print "Not in a ClearCase view: abort."
        sys.exit(-1)

    return viewInfo[0]

def getCoFilesOrDie():
    cmdTokens = [];
    cmdTokens.append('/usr/atria/bin/cleartool')
    cmdTokens.append('lsco')
    cmdTokens.append('-cvi')
    cmdTokens.append('-a')
    cmdTokens.append('-s')

    cmd = " ".join(cmdTokens)

    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    coFiles = [fname.strip() for fname in proc.stdout.readlines()]

    #if not coFiles:
    #  print "Changeset is empty: nothing to commit."
    #  sys.exit(0)

    return coFiles


def getModuleToFiles(files, pattern):
    "Create the list of tuples with the filename at position 0 and the index of string '/src/main/java/' at position 1"
    fileWithPosition = filter(lambda fname: fname[1] != -1, zip(files, map(lambda s: s.find(pattern), files)))
    # Use the index at position 2 to calculate the name of the module for each file
    moduleToFile = map(lambda fname: (fname[0][:fname[1]], fname[0]), fileWithPosition)
    result = {}
    for fname in moduleToFile:
        if fname[0] not in result:
            result[fname[0]] = []
        result[fname[0]].append(fname[1])
    return result


class ChangeSet:

    def __init__(self, coFiles):
        self.coFiles = coFiles
        self.javaFiles = [fname for fname in coFiles if fname.endswith('.java')]
        self.testSuites = [fname for fname in self.javaFiles if fname.endswith('Test.java')]
        self.pyFiles = [fname for fname in coFiles if fname.endswith('.py')]

        self.moduleToSrcFile = getModuleToFiles(self.javaFiles, '/src/main/java/')
        self.moduleToTestSuite = getModuleToFiles(self.testSuites, '/src/test/java/')
        self.impactedModules = set(self.moduleToSrcFile.keys()) | set(self.moduleToTestSuite.keys())

    def isEmpty(self):
        return not self.coFiles

    def needStaticAnalysis(self):
        "Returns True if a SA is necessary."
        return self.moduleToSrcFile

    def needCodeFormatting(self):
        return self.javaFiles

    def getPySourceFiles(self):
        "Returns the list of python source files."
        return self.pyFiles

    def needUnitTest(self):
        return self.moduleToTestSuite

    def filterForSql(self):
        "Force change set to contain only sql files."
        sqlFiles = (fname for fname in self.coFiles if fname.endswith('.sql'))
        # remove the sql files used in Junit
        sqlFiles = [fname for fname in sqlFiles if 'src/test/resources' not in fname]
        if sqlFiles:
            # if a sql file is present reset state
            self.coFiles = sqlFiles
            self.javaFiles = []
            self.testSuites = []
            self.pyFiles = []
            self.moduleToSrcFile = {}
            self.moduleToTestSuite = {}
            self.impactedModules = set()
        return sqlFiles

    def printDetails(self):
        print "Modified Modules:"
        print self.impactedModules

        print "Modified Source Files:"
        print self.moduleToSrcFile

        print "Modified Test Suites:"
        print self.moduleToTestSuite

    def printSummary(self):
        print "* Modified Maven Projects: ", len(self.impactedModules)
        print "* Modified Java Source Files: ", len(self.moduleToSrcFile)
        print "* Modified Java Test Suites: ", len(self.moduleToTestSuite)

def getChangeSet():
    return ChangeSet(getCoFilesOrDie())

def runJalopy():
    runCommand("/vob/visionway/ctm/tools/scripts/javafmtco")

def formatpyfiles(filelist):
    "Indent filenames in filelist."
    for filename in filelist:
        reindent.check(filename)

def test_formatpyfiles():
    "py.test testcase."
    formatpyfiles([__file__])

def formatCode(cs):
    if cs.needCodeFormatting():
        runJalopy()
    pyfiles = cs.getPySourceFiles()
    if pyfiles:
        formatpyfiles(pyfiles)

def readLazyJackViewAudit(viewName):
    audit = LazyJackAudit(viewName)
    audit.init()
    return audit

def storeBranchProperty(line, branchInfo):
    tokens = line.split('=')
    branchInfo[tokens[0].strip()] = tokens[1].strip()

def fillPrrqFromBranch(branchInfo):
    branchName = branchInfo['BRANCH_NAME']
    proc = Popen("updbranch -p -b " + branchName, shell=True, stdout=PIPE, stderr=PIPE)
    if proc.wait():
        return False
    for line in  proc.stdout.readlines():
        if line.startswith('PRRQ_QUEUE'):
            storeBranchProperty(line, branchInfo)
    return True

def fillBranchInfo(branchInfo, getPrrqQueue=False):
    print "[ ... ] Get branch data ..."
    proc = Popen("updbranch -p", shell=True, stdout=PIPE, stderr=PIPE)
    if proc.wait():
        return False

    for line in  proc.stdout.readlines():
        if line.startswith('Branch'):
            tokens = line.split()
            branchInfo['NAME'] = tokens[1]
        elif line.startswith('PARENT_BRANCH') or line.startswith('TASK_BRANCH') or line.startswith('PRRQ_QUEUE'):
            storeBranchProperty(line, branchInfo)

    if branchInfo['TASK_BRANCH'] == 'TRUE':
        branchInfo['BRANCH_NAME'] = branchInfo['PARENT_BRANCH']
    else:
        branchInfo['BRANCH_NAME'] = branchInfo['NAME']

    if getPrrqQueue and branchInfo['TASK_BRANCH'] == 'TRUE':
        return fillPrrqFromBranch(branchInfo)

    return True

def runCcMkElem(files):
    runCommand("cc_mkelem " + files)

def runCcMkElems(files):
    runCcMkElem("cc_mkelem " + " ".join(files))

def askActionForMissingElements():
    while True:
        choice = raw_input("[ ... ] Do you want to run the cc_mkelem for (A)ll the file above, (S)kip this step or (E)xit? (A/S/E) [E]")
        create = (choice == 'a' or choice == 'A')
        skip = (choice == 's' or choice == 'S')
        exit = (choice == 'e' or choice == 'E' or choice == "")
        if create or skip or exit:
            return (create, exit)


def checkMissingCcMkElem():
    newElems = search_new_elems()
    if (newElems):
        print "        WARNING: It seems you are missing to run the cc_mkelem command for following files:"
        for elem in newElems:
            print "        " + elem

        while True:
            choice = raw_input("[ ... ] Do you want to (S)kip this step or (E)xit? (S/E) [E]")
            skip = (choice == 's' or choice == 'S')
            exit = (choice == 'e' or choice == 'E' or choice == "")
            if exit:
                sys.exit(0)
            else:
                break


        #if len(newElems) == 1:
        #    if askConfirmation("[ ... ] Do you want to run the cc_mkelem for " + os.path.basename(newElems[0]) + "?"):
        #        runCcMkElem(newElems[0])
        #else:
        #    (create, exit) = askActionForMissingElements()
        #    if create:
        #        runCcMkElems(newElems)
        #    elif exit:
        #        sys.exit(0)

#
# Common features should be moved out
#

def askConfirmation(question):
    while True:
        confirm = raw_input(question + " (Y/N) [Y]").strip()
        if confirm == 'y' or confirm == 'Y' or confirm == "n" or confirm == "N" or confirm == "":
            return confirm == 'y' or confirm == 'Y' or confirm == ""

def runCommand(cmd, failFast=True):
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    if proc.wait() and failFast:
        print 'Execution failed for command "' + cmd + '"'
        for line in  proc.stdout.readlines():
            print line.strip()
        sys.exit(1)
    return proc
    
    
def buildDiff(diffFile, partial=False):
    if os.path.exists(diffFile):
        os.remove(diffFile)

    if partial:
        cmd = "/usr/cisco/bin/cc_diff -f " + partial + " >> " + diffFile
    else:
        cmd = "/usr/cisco/bin/cc_diff >> " + diffFile

    runCommand(cmd)
