"""This script is a wrapper of the commit CC tools script.
It allows to commit performing all steps required by quality process.
It is supposed to run in a Clear Case view from which diff for the review are collected.

The script performs following steps:

  - ask to review diff and check the branch
  - check for missing cc_mkelem (list private files for which the user is probably missing cc_mkelem or cc_mkdir)
  - run static analysis for Java code and show results
  - format the Java code
  - run the commit CC tools script
  - attach the Static Analysis enclosure to the commit bug
  - attach the Unit Test enclsure to the commit bug

This script is part of the Lazy Jack suite.

Author: siasi@cisco.com
Contributors: ceplacan@cisco.com

Date: November 2012

"""

import sys
import re

from ConfigParser import SafeConfigParser, NoOptionError
from optparse import OptionParser
import os
from cc import *
from sa import *
from build import build
from subprocess import Popen, PIPE, STDOUT

from cdets import EnclosureTest, CdetsDefect
from subprocess import call

#def commit():
#  proc = Popen("/usr/cisco/bin/commit", shell=True, stdout=PIPE, stderr=STDOUT)
#
#  commitId = parseCommitId(proc)
#  retcode = proc.wait()

#  if retcode != 0:
#    print >>sys.stderr, "Commit command failed"
#    sys.exit(retcode)
#  else:
#    print >>sys.stderr, "Commit command successful"
#
#  return commitId


#def parseCommitId(proc):
#  bugId = None
#  commitId = None
#  print "In parseCommit"
#  output = proc.communicate()[0]
#  print output

    #line = line.strip()
    #if line.startswith("Your review has been created successfully and"):
    #  tokens = line.split()
    #  print "Tokens are ", len(tokens)
    #  if len(tokens) >= 23:
    #    bugId = tokens[22]
    #   bugId = bugId[1:-1]

#  return ("CSCua19000", "commitId")

def addUtManualNote(identifier):
    note = NamedTemporaryFile(delete=False)
    noteContent = "Unit Test executed manually:"
    note.write(noteContent)
    note.close()

    try:
        retcode = call("addnote -m -t Unit-test " + identifier + ' "unit-test" ' + note.name, shell=True)
        if retcode != 0:
            print >>sys.stderr, "Attaching of UT note failed"
            sys.exit(retcode)
        else:
            print >>sys.stderr, "Attaching of UT note successful"
    except OSError, e:
        print >>sys.stderr, "Attaching of UT note failed:", e
        sys.exit(-1)
    finally:
        os.remove(note.name)

def prepareUtAutomaticNoteContent(changeSet):
    noteValues = {}
    noteValues['autModules'] = "\n".join(sorted(changeSet.moduleToTestSuite.keys()))
    autSuites = []
    for l in changeSet.moduleToTestSuite.values():
        autSuites.extend(l)
    noteValues['autSuites'] = "\n".join(sorted(autSuites))
    noteValues['manualModules'] = "\n".join(sorted(changeSet.impactedModules - set(changeSet.moduleToTestSuite.keys())))

    noteTemplate = ""
    if noteValues['autModules']:
        noteTemplate = noteTemplate + """- Changes in following modules have been tested in automatic mode:
      %(autModules)s"""

    if noteValues['autSuites']:
        noteTemplate = noteTemplate + """\n\n- Automatic Test Suites added/updated:
      %(autSuites)s"""

    if noteValues['manualModules']:
        noteTemplate = noteTemplate + """\n\n- Changes in following modules have been tested in manual mode:
      %(manualModules)s"""

    return noteTemplate % noteValues


def addUtAutomaticNote(identifier, changeSet):
    noteContent = prepareUtAutomaticNoteContent(changeSet)

    note = NamedTemporaryFile(delete=False)
    note.write(noteContent)
    note.close()

    try:
        retcode = call("addnote -m -t Unit-test " + identifier + ' "unit-test" ' + note.name, shell=True)
        if retcode != 0:
            print >>sys.stderr, "[  E  ] Attaching of UT note failed"
            sys.exit(retcode)
        else:
            print >>sys.stderr, "[ ... ] Attaching of UT note successful"
    except OSError, e:
        print >>sys.stderr, "[  E  ] Attaching of UT note failed:", e
        sys.exit(-1)
    finally:
        os.remove(note.name)

def runCommit(commitArgs):
    try:
        cmd = "/usr/cisco/bin/commit -d -f " + commitArgs

        retcode = call(cmd, shell=True)
        if retcode != 0:
            print >>sys.stderr, "Commit failed"
            sys.exit(retcode)
        else:
            print >>sys.stderr, "Commit passed"
    except OSError, e:
        print >>sys.stderr, "Commit execution failed:", e
        sys.exit(-1)


def passUtOrDie(changeSet, buildDependents):
    build(changeSet, buildDependents)

def showDiff(opts, diffFile):
    #if not askConfirmation("[ ... ] Do you want to review diff?"):
    #  return

    print "[ ... ] Calculating diff ..."
    buildDiff(diffFile, opts.partial)

    try:
        cmd = "more " + diffFile
        retcode = call(cmd, shell=True)
        if retcode != 0:
            print >>sys.stderr, "Execution of command ", cmd , "failed"
            sys.exit(retcode)
    except OSError, e:
        print >>sys.stderr, "Diff execution failed:", e
        sys.exit(-1)


def confirmBranch():
    branchInfo = {}
    if not fillBranchInfo(branchInfo):
        return askConfirmation("[ ... ] Error getting the branch data. Do you want to continue anyway?")

    return askConfirmation("[ ... ] You are going to commit changes to branch " + branchInfo['BRANCH_NAME']+ ". Do you confirm?")

def validateDiffAndBranch(opts, diffFile):
    showDiff(opts, diffFile)

    if not confirmBranch():
        sys.exit(0)

def ccUpdateRunOrDie():
    (bugId, comment) = readClearCaseViewAudit(viewName)

    if bugId == None or comment == None:
        print """ERROR: missing comment in view audit record:
      You may need to run prepare.
      commit failed."""
        sys.exit(1)
    return bugId

def parseArguments():
    import __init__ as lazyjack
    parser = OptionParser(prog="commit", usage="%prog [options]", description=__doc__, version=lazyjack.opt_ver)
    parser.add_option("-s", "--silent", action="store_true", dest="silent",
                      help="Commit in silent mode. Not shows diff and branch.", metavar="FILE")
    parser.add_option("-d", "--build-dependents", action="store_true", dest="buildDependents",
                      help="Build changed Maven projects and dependents projects.", metavar="FILE")
    parser.add_option("-b", "--build-changed", action="store_true", dest="buildChanged",
                      help="Build changed Maven projects.", metavar="FILE")
    parser.add_option("-p", "--partial", dest="partial",
                      help="Run CC commit with -p option.", metavar="file containing list of files to commit")


    return parser.parse_args()

def changeSetNotEmptyOrDie():
    cs = getChangeSet()

    if cs.isEmpty():
        print "Changeset is empty: nothing to commit."
        sys.exit(-1)

    return cs

def toCommitArgs(opts, args, ljAudit):
    if opts.partial:
        return "-p " + opts.partial
    else:
        return ""


def commit(cs, bugId, opts, args, ljAudit):
    if not opts.silent:
        print "[ 1/8 ] Validate diff and branch ..."
        validateDiffAndBranch(opts, ljAudit.diffFile)
    else:
        print "[ 1/8 ] Validate diff and branch ... (SKIPPED)"

    print "[ 2/8 ] Check missing cc_mkelem ..."
    checkMissingCcMkElem()
    print "[ 3/8 ] Run Static Analysis ..."
    forceDiff = opts.silent
    checkNoSaInDiff(cs, ljAudit, forceDiff, opts.partial)
    print "[ 4/8 ] Format Code ..."
    formatCode(cs)

    if opts.buildDependents or opts.buildChanged:
        print "[ 5/8 ] Run private Build ... "
        passUtOrDie(cs, opts.buildDependents)
    else:
        print "[ 5/8 ] Run private Build ... (SKIPPED)"

    print "[ 6/8 ] Commit changeset on bug", bugId, "..."
    print
    runCommit(toCommitArgs(opts, args, ljAudit))
    print

    if cs.needStaticAnalysis():
        print "[ 7/8 ] Attach Static Analysis report ..."
        addSaReport(bugId)
    elif cs.getPySourceFiles():
        print "[ 7/8 ] Attach Static Analysis report ..."
        addSaReport(bugId, ljAudit.pysahtml)
    else:
        print "[ 7/8 ] Attach Static Analysis note ..."
        addSaNotNeededNote(bugId)

    if cs.needUnitTest():
        print "[ 8/8 ] Attach Unit Test enclosure ..."
        addUtAutomaticNote(bugId, cs)
    else:
        print "[ 8/8 ] Attach Unit Test enclosure ... (SKIPPED)"
        print "        No Automatic Tests found in checkedout files: "
        print "        REMEMBER TO ADD UT NOTE BEFORE MOVING THE BUG IN R STATE!"

    print "[ ... ] Done."



def checkReviewOpen():
    ljAudit = readLazyJackViewAudit(viewName)
    if not ljAudit.reviewRequested():
        if not askConfirmation("It seems you did not reviewed the code changes: do you want to commit anyway?"):
            sys.exit(0)
    return ljAudit

def isAValidFileList(partialFile):
    if not os.path.exists(partialFile):
        print "File", partialFile, "does not exists."
        return False

    pf = open(partialFile)

    notValidFiles = [f.strip() for f in pf.readlines() if not os.path.exists(f.strip())]
    if notValidFiles:
        print "ERROR"

    for f in notValidFiles:
        print "File", f, "is not a valid file"

    return not notValidFiles

#
# BEGIN
#
if __name__ == "__main__":
    viewName = runInCcViewOrDie()

    (opts, args) = parseArguments()

    if opts.partial and not isAValidFileList(opts.partial):
        sys.exit(1)

    bugId = ccUpdateRunOrDie()
    
    cs = changeSetNotEmptyOrDie()

    ljAudit = checkReviewOpen()

    commit(cs, bugId, opts, args, ljAudit)

    audit = LazyJackAudit(viewName)
    audit.destroy()
