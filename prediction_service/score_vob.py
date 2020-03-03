
"""Prediction engine.

Authors: siasi@cisco.com
         ceplacan@cisco.com
"""

import csv
import os
import re
import scan_view
import time
import commands
import sys
import math
#import requests
from subprocess import Popen, PIPE
from datetime import datetime
from cc import runCommand,runInCcViewOrDie
from bugprediction import Classification, DefectsCache
from optparse import OptionParser


PATTERN = re.compile("CSC[a-z]{2}\d{5}")
CFG_FOLDER = "/opt/dev-tools/lazyjack/cfg"
RANKFILE = os.path.join(CFG_FOLDER, "rankedVob.csv")
CACHE_FILE = os.path.join(CFG_FOLDER, "cdets.cache.csv")
EPOC = datetime(2000, 1, 1)
INTERVAL = datetime.today() - EPOC
ROOT_DIR = '/vob/visionway/ctm'



def countBugs(filename):
    "Retrieves the bug count of filename."
    bugs = set()
    cmd = "/usr/atria/bin/cleartool lshistory " + filename + " | awk /CSC/"
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    for line in proc.stdout.readlines():
        match = PATTERN.search(line)
        if match:
            bugs.add(match.group(0))
    result = [filename]
    result.extend(list(bugs))    
    return result

def compareScoredFiles(first, second):
    "Sort the files by score."

    if first[1] > second[1]:
        return -1
    elif first[1] < second[1]:
        return 1
    else: 
        return 0

def toBugAge(date):
    """Return the normalized age of the bug.
       The normalized age is a value in the ranee (0, 1). It is computed by considering 
       EPOC as the start date of the INTERVAL, and today as the last day.
    """
    return float((date - EPOC).days) / float(INTERVAL.days)

def parseDate(strDate):
    "Parse a date from the input string."

    return datetime.strptime(strDate.split()[0], "%m/%d/%Y")

def computeScore(partialScore, age):
    """Compute the partial score of a file.
       Add the score for a specific bug (calculated from the age of the bug) to the current partial score.
       The score of the bug is computed by using an exponential function that return a value from 0 to 0.5 
       for the possible input range (0 - 1).
    """
    #print "partial score is", partialScore
    return partialScore + (float(1) / (float(1) + math.exp(-12 * age + 12)))

def chunks(bugIds, requestedSize):
    """This function is a generator. 
    Take as input the set of bug IDs and the requestedSize of the sublist.
    Return a list of list. Each element of the list contain a subset of bug IDs 
    of the passed set. Each list is a maximum size of requestedSize.  
    """

    l = list(bugIds)
    for i in xrange(0, len(l), requestedSize):
        yield l[i:i+requestedSize]

def getCommand(bugIds):
    "Return the CDETS query command to get data for the passed bugIds."

    return 'findcr -w "Identifier,Severity,Submitted-on" -D , -i ' + ",".join(bugIds) #+ ' "Severity<=3"'

def cacheBugInfo(line):
    "Update the defects repository cache with the data in line."

    tokens = line.split(',')

    bugId = tokens[0]
    severity = tokens[1]
    date = tokens[2]
    
    if int(severity) <= 3:
      cache.addValidBug(bugId, toBugAge(parseDate(date)))
    else:
      cache.addNotValidBug(bugId)
      
    return cache.getAge(bugId)  

def getAge(bugsToCheck):
    "Return the age for each bugId in the passed iterable."

    # Create the query commands to get data for the bugId.
    # Due to limited lenght of the command that can be passed to the shell
    # we need to split the input list and generated a command for each sublist.
    commands = [getCommand(bugIdsChunk) for bugIdsChunk in chunks(bugsToCheck, 20)]

    # Run the commands and cache the bug data for each bug in the output command.
    return [cacheBugInfo(line[:-1]) for cmd in commands for line in runCommand(cmd, False).stdout.readlines() if line.find(',') != -1]

def toAges(bugIds):
    """Convert input bugIds to the corresponding ages. 
    Bugs ignored are converted to an age equal to 0."""
    
    # Determine bugs to check comparing input list with the defect cache.
    bugs = set(bugIds)
    unknownBugs = bugs - cache.knownBugs
    knownBugs = bugs - unknownBugs
    
    #print "There are ", len(unknownBugs), "bugs to check:", str(unknownBugs)
    #print "There are ", len(knownBugs), "bugs to not check", str(knownBugs)
    
    ages = getAge(unknownBugs)
    knownAges = [cache.getAge(bugId) for bugId in knownBugs]
    ages.extend(knownAges)
    
    return [age for age in ages if age > 0]
    
def scoreFile(scannedFile):
    """The input parameter is a list containing the name of the file as first element, followed by the list of bug IDs.
       The bug IDs are the bug required a fix in the file to resolve the bug.
       
       This functions removes the bugs whiah have severity less than "Severe". 
       Then return a weight for the file considering the normalized age of each bug.
       The weight is the wieghted sum of the normalized age of all the bugs, according to an exponential distribution.
       
       The function return a list where the first element is the name of the file, and the second element
       is the weight for the file.
    """

    ages = toAges(scannedFile[1:])
    return [scannedFile[0], reduce(computeScore, ages, 0)] 
        
def hasBugs(file):
    return len(file) > 1
   
def scoreVob():
    "Browses a view and calculates bug count."
    
    print "Scanning files for dir ", ROOT_DIR
    startScan = datetime.today()
    files = scan_view.search_source_elems(ROOT_DIR)
    print "Selected", len(files), "source files in", str(datetime.today() - startScan)
    
    print "Start files scanning"
    startCount = datetime.today()
    scannedVob = [countBugs(srcFile) for srcFile in files]
    print "Scanned files for bugs in", str(datetime.today() - startCount) 
    
    print "Start files scoring"
    startWeigh = datetime.today()
    scoredVob = [scoreFile(scannedFile) for scannedFile in scannedVob if hasBugs(scannedFile)]
    print "Scored files in", str(datetime.today() - startWeigh) 
    
    print "Start file sorting"
    startSort = datetime.today()
    scoredVob.sort(compareScoredFiles)
    print "Sorted files in", str(datetime.today() - startSort) 
    
    return Classification(scoredVob)


def scoreProject():
    "Score each file of the project and update the prediction database."

    print "Loading Defect Cache ..."
    cache.fill(CACHE_FILE)
    print "Loading CDETS Cache done.", len(cache.knownBugs), " bugs loaded"  
    
    print "Start scoring of vob files ..."
    startTime = datetime.today() 
    classification = scoreVob()
    print "Completed scoring in ", str(datetime.today() - startTime), " seconds"
    
    print "Scored", classification.size() , " files"
    print "Keep first", classification.topSize(), "files for prediction algorithm"
    
    print "Storing classification in", RANKFILE
    classification.storeTop(RANKFILE)
    print "Done"
    
    print "Cache size is ", len(cache.cache)
    
    print "Storing cache in", CACHE_FILE
    cache.store(CACHE_FILE)
    print "Done"    


if __name__ == '__main__':
    runInCcViewOrDie()
    
    parser = OptionParser(prog="%prog", usage="%prog [options]")#, description=__doc__, version=lazyjack.opt_ver)   
    parser.add_option("-w", "--working-dir", dest="workingDir",
                      help="Set the working directory for cache and result files.", metavar="DIRECTORY")
		      
    (opt, args) = parser.parse_args()
    if opt.workingDir:
        if not os.path.isdir(opt.workingDir):
	    print "The working directory does not exists."
	    sys.exit(1)
	    
	RANKFILE = os.path.join(opt.workingDir, "rankedVob.csv")
        CACHE_FILE = os.path.join(opt.workingDir, "cdets.cache.csv")
        print "Working directory is ", opt.workingDir

    cache = DefectsCache()
    scoreProject()

    
    
