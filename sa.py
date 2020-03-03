#!/usr/bin/env python

"This module is a collection of functions to perform Static Analysis."
#
# author: siasi@cisco.com
# Date: August 2012
#

import sys
import os

from cc import runCommand, askConfirmation, runInCcViewOrDie, getChangeSet
from cc import readLazyJackViewAudit, buildDiff
from subprocess import call
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE
from sa_diff import Report
from optparse import OptionParser
import pysa

reportFile = '/vob/visionway/ctm/tools/pmd/report/report.html'

def checkNoSaInDiff(cs, audit, forceDiff=True, partialDiff=False):
    runPmd()
    report = Report(reportFile)
    
    if not report.issues:
        return
    
    if forceDiff:
        print "[ ... ] Building diff to verify no SA issues will be injected ..."
        buildDiff(audit.diffFile, partialDiff)
	    
    if report.issuesIn(audit.diffFile):
        
        reportForDiff = report.keepIssuesIn(audit.diffFile)
	
	r = open(audit.saDiffReport, "w")
	r.write(reportForDiff)
	r.close()
        print "[ ... ] WARNING: You are going to inject one ore more SA issues."
        reviewReport(audit.saDiffReport)
    else:
        print "[ ... ] No new Static Analysis issues injected"

    # SA for python is not (yet) on diff
    files = cs.getPySourceFiles()
    if files:
        runPySa(files)

def countSaViolations():
    f = open(reportFile)
    lines = f.readlines()
    f.close()
    return [line for line in lines if line.count('rules')]

def reviewReport(htmlFile):
    while True:
        choice = raw_input("[  ?  ] Do you want to review Static Analysis violations (Y/N)? [Y] ")
        if choice == "" or choice == "Y" or choice == "y":
            runLinks(htmlFile)
            if not askConfirmation("[  ?  ] Do you want to continue?"):
                sys.exit(0)
            else:
                break
        else:
            break

def askToReview(violations, htmlFile=reportFile, code="Java"):
    if len(violations) == 1:
        print "[ ... ] WARNING: There is", len(violations), "Static Analysis violation in %s code.\n" % code,
    else:
        print "[ ... ] WARNING: There are", len(violations), "Static Analysis violations in %s code.\n" % code,
    
    reviewReport(htmlFile)

    

def review(violations):
    runLinks()

def runLinks(htmlFile=reportFile):
    try:
        cmd = "links " + htmlFile
        retcode = call(cmd, shell=True)
        if retcode != 0:
            print >> sys.stderr, "Failed execution of " + cmd
            sys.exit(retcode)
    except OSError, e:
        print >> sys.stderr, "Failed execution of " + cmd, e
        sys.exit(-1)

def runPmd():
    cmd = "(cd /vob/visionway/ctm/tools/pmd; make)"
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    (stdoutdata, stderrdata) = proc.communicate()
    if proc.poll() != 0:
        print 'Execution failed for command "' + cmd + '"'
        print stderrdata
        sys.exit(1)

def passSaOrDie():
    runPmd()
    violations = countSaViolations()
    if violations:
        askToReview(violations)

def addSaReport(identifier, htmlFile=reportFile):
    cmd = "addfile -m " + identifier + ' "static-analysis.html" ' + htmlFile
    runCommand(cmd)

def addSaNotNeededNote(identifier):
    note = NamedTemporaryFile(delete=False)
    noteContent = "Static Analysis not executed because no java file has been modified"
    note.write(noteContent)
    note.close()

    try:
        retcode = call("addnote -m -t Static-analysis " + identifier + ' "static-analysis" ' + note.name, shell=True)
        if retcode != 0:
            print >> sys.stderr, "Attaching of SA note failed"
            sys.exit(retcode)
        else:
            print >> sys.stderr, "Attaching of SA note successful"
    except OSError, e:
        print >> sys.stderr, "Attaching of SA note failed:", e
        sys.exit(-1)
    finally:
        os.remove(note.name)


def savePySaFile(textLines, fileName):
    "Save html and text file for python SA."
    text = '\n'.join(textLines)
    issuesFile = open(fileName, "w")
    issuesFile.write(text)
    issuesFile.close()

def runPySa(files):
    "Executes static analysis on Python code."
    issues = pysa.run_pylint(files)
    if issues:
        viewName = runInCcViewOrDie()
        aud = readLazyJackViewAudit(viewName)
        savePySaFile(pysa.convert_to_html_table(issues), aud.pysahtml)
        savePySaFile(issues, aud.pysatxt)
        askToReview(issues, aud.pysahtml, "Python")

def runSa(cs):
    if cs.needStaticAnalysis():
        passSaOrDie()
    #else:
    #    print "[ ... ] Skipping Static Analysis (no modified Java files in the changeset)."
	
    files = cs.getPySourceFiles()
    if files:
        runPySa(files)
    #else:
    #    print "[ ... ] Skipping Static Analysis (no modified Python files in the changeset)."


#
# BEGIN
#
if __name__ == "__main__":
    viewName = runInCcViewOrDie()
    
    import __init__ as lazyjack
    parser = OptionParser(prog="sa", usage="%prog [options]", description=__doc__, version=lazyjack.opt_ver)
    parser.add_option("-d", "--diff", action="store_true", dest="diff",
                      help="Run Static Analysis on diff", metavar="FILE")

    (opts, args) = parser.parse_args()
    
    cs = getChangeSet()
    if cs.isEmpty():
        print "Changeset is empty: cannot run Static Analysis."
        sys.exit(-1)

    if opts.diff:
        audit = readLazyJackViewAudit(viewName)
        checkNoSaInDiff(cs, audit)
    else:
        runSa(cs)
