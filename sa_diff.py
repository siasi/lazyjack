#!/usr/bin/env python

#
# This module is a collection of functions to perform Static Analysis
# on diff file.
#
# author: siasi@cisco.com
# Date: February 2012
#
from optparse import OptionParser
from HTMLParser import HTMLParser
import itertools, os, sys
import xml.etree.ElementTree as ET


class Issue(object):
    """The Static Analysis issue."""

    def __init__(self, file_name="", line_number="0"):
        self.file_name = file_name
        self._line_number = int(line_number)

    @property
    def line_number(self):
        return self._line_number

    @line_number.setter
    def line_number(self, value):
        "The line number where the issue has been found."
        self._line_number = int(value)

    @property
    def fileName(self):
        "The simple file name of the file where the issue is."
        return os.path.basename(self.file_name)

    def isValid(self):
        """Return True if the issue is valid.
           An issue is true when line number is different from 0 and
           file_name is not an empty string.
        """
        return self.file_name != "" and self.line_number != 0

    def __repr__(self):
        return "SA Issue of " + self.fileName + " line " + str(self.line_number)


class PmdReportParser(HTMLParser):
    """A parser for the PMD HTML report.
       It is able to parse the HTML report and provide the
       list of Static Analysis issues in the report. """

    def __init__(self):
        HTMLParser.__init__(self)
        self.current_issue = None
        self.issues = []
        self.countTd = 0
        self.expect = ""
	self.tableCount = 0

    def handle_starttag(self, tag, attrs):
        #print "Encountered a start tag:", tag

        if tag == "tr":
            self.currentIssue = Issue()
        elif tag == "td":
            #print "TD FOUND!!!"
            self.countTd += 1
	    if not self._isSuppressedViolationTable():
	        td_with_file_name = 2
		td_with_line_number = 3
	    else:
	        td_with_file_name = 1
		td_with_line_number = 2

	    if self.currentIssue and self.countTd == td_with_file_name:
                #print "Prepare to save file name"
                self.expect = "file_name"
            elif self.currentIssue and self.countTd == td_with_line_number:
                #print "Prepare to saving line number"
                self.expect = "line_number"
            else:
                self.expect = ""
	
        elif tag == "table":
	    #print "table tag found: ", self.tableCount
	    self.tableCount += 1
	    
    def _isSuppressedViolationTable(self):
        return self.tableCount == 2
	    

    def handle_endtag(self, tag):
        #print "Encountered an end tag:", tag
        if tag == "tr":
            #print "tr found"
            if self.currentIssue.isValid():
                #print "NEW ISSUE FOUND"
                self.issues.append(self.currentIssue)
            self.currentIssue = None
            self.countTd = 0

    def handle_data(self, data):
        #print "Encountered some data  :", data
        if self.expect:
            #print "Saving file name to", data
            setattr(self.currentIssue, self.expect, data.strip())
            self.expect = ""


class Report():

    def __init__(self, file_name):
        self.file_name = file_name

    @property
    def issues(self):
        "The list of Static Analysis issues of the PMD report"
        f = open(self.file_name)
        parser = PmdReportParser()

        for line in f.readlines():
            parser.feed(line)

        return parser.issues

    def issuesIn(self, diff):
        "Return the list of Static Analysis issues of the PMD report which are in the passed Diff"

        #It is possible to pass
        if type(diff) == str:
            diff = DiffFile(diff)

        files = {}
        for file in diff.files:
            files[file.name] = file
	
        return [issue for issue in self.issues if issue in files.get(issue.fileName, [])]

    def _filterIssuesFromTable(self, root, table, lines_with_issues, td_with_line_number):
        #print table
        if (len(table) <= 1):
            return ET.tostring(root)
        #print "Going to filter table"
        for tr in table[1:]:
            line = int(tr[td_with_line_number].text)
            if not line in lines_with_issues: 
                table.remove(tr)

        # Remove the header if no violations kept
        if (len(table) == 1):
            table.attrib = {}
            table.remove(table[0])

        return ET.tostring(root)
	
    def _suppressedViolationTableExists(self, root):
        return len(root[1]) >= 6
	
    def keepIssuesIn(self, diff):
        lines_with_issues = [issue.line_number for issue in self.issuesIn(diff)]
        
        tree = ET.parse(self.file_name)
        root = tree.getroot()
        activeViolationsTable = root[1][2]
        
        newReport = self._filterIssuesFromTable(root, activeViolationsTable, lines_with_issues, 2)
	
	if self._suppressedViolationTableExists(root):
	    suppressedViolationsTable = root[1][5]
	    newReport = self._filterIssuesFromTable(root, suppressedViolationsTable, lines_with_issues, 1)
	
	return newReport
	
	    		    


class DiffFile:
    "The file of the diff."

    def __init__(self, name):
        self.file_name = name   

    @property
    def files(self): 
        "The list of changed file in the diff."

        parser = DiffParser(self.file_name)
        return parser.parse()

class ChangedFile:
    """One of the file contained in the diff file.
    Has file name and a list of (changed) line numbers."""

    def __init__(self, name):
        self._name = name
        self.ranges = []

    def append(self, newRange):
        self.ranges.append(newRange)

    @property
    def name(self):
        "The simple file name of the file in the diff."
        return os.path.basename(self._name)

    @property
    def changedLines(self):
        ranges = (range.generate() for range in self.ranges)
        return (line for lines in ranges for line in lines)
    
    def __contains__(self, key):
        return key.line_number in self.changedLines

    def __repr__(self):
        return self.name + ", " + str(len(self.ranges)) + " ranges"


class Range:
    "A range of lines in the Diff file."

    def __init__(self, lowerBound, higherBound):
        self.lowerBound = lowerBound
        self.higherBound = higherBound

    def generate(self):
        return range(self.lowerBound, self.higherBound + 1)


class DiffParser:
    """A parser for the diff file.
       Can parse the diff file and provide the list of
       ranges for each file in the diff file."""

    def __init__(self, diff_file):
        self.diffFile = diff_file
        self.files = []
        self.currentFile = None

    def parse(self):
        "Parse the file wit diff and return the list of DiffFiles."

        f = open(self.diffFile)
        for line in f.readlines():
            self._parseLine(line)

        if self.currentFile != None:
            self.files.append(self.currentFile)

        return self.files

    def _parseLine(self, line):
        line = line.strip()
        if line.startswith("Index:"):
            self._newFileFound(line)
        elif line.startswith("---") and line.endswith("---"):
            self._newRangeFound(line)

    def _newFileFound(self, line):
        if self.currentFile != None:
            self.files.append(self.currentFile)
        self.currentFile = ChangedFile(line.split()[1])

    def _newRangeFound(self, line):
        numbers = line[3:-4].split(",")
	
	if len(numbers) < 2:
	    return  
	
        lowestBound = int(numbers[0].strip())
        highestBound = int(numbers[1].strip())
        range = Range(lowestBound, highestBound)
        self.currentFile.append(range)


#
# BEGIN
#
if __name__ == "__main__":
    import __init__ as lazyjack
    parser = OptionParser(prog="sa_diff", usage="%prog [options]", description=__doc__, version=lazyjack.opt_ver)
    parser.add_option("-r", "--report", dest="report",
                      help="The html report file from PMD.", metavar="FILE")
    parser.add_option("-d", "--diff", dest="diff",
                      help="The diff files.", metavar="FILE")

    (opts, args) = parser.parse_args()

    if not opts.report or not opts.diff:
        print "Please provide -r and -d options."
        sys.exit(1)

    report = Report(opts.report)
    if report.issuesIn(opts.diff):
        newReport = report.keepIssuesIn(opts.diff)
        report_diff = open("report-diff.html")
        report_diff.write(newReport)
        report_diff.close()
        #open the browser
