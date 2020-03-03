import unittest
from sa_diff import Report, Issue, ChangedFile, Range, DiffFile

class DiffParsingTest(unittest.TestCase):

    def test_extract_line_range_extract_4_files(self):
        files = DiffFile("test/sa_diff/diff.txt").files

        self.assertEquals(len(files), 4)

    def test_extract_line_range_extract_two_ranges_for_file_one(self):
        files = DiffFile("test/sa_diff/diff.txt").files

        self.assertEquals(files[0].name, "ICommonLink.java")
        self.assertEquals(len(files[0].ranges), 2)

        self.assertEquals(files[0].ranges[0].lowerBound, 1)
        self.assertEquals(files[0].ranges[0].higherBound, 9)
        self.assertEquals(files[0].ranges[1].lowerBound, 22)
        self.assertEquals(files[0].ranges[1].higherBound, 32)

    def test_extract_line_range_extract_one_ranges_for_file_two(self):
        files = DiffFile("test/sa_diff/diff.txt").files

        self.assertEquals(files[1].name, "ILink.java")
        self.assertEquals(len(files[1].ranges), 1)

        self.assertEquals(files[1].ranges[0].lowerBound, 1)
        self.assertEquals(files[1].ranges[0].higherBound, 15)


    def test_extract_line_range_extract_2_ranges_for_file_three(self):
        files = DiffFile("test/sa_diff/diff.txt").files

        self.assertEquals(files[2].name, "CpoLink.java")
        self.assertEquals(len(files[2].ranges), 2)

        self.assertEquals(files[2].ranges[0].lowerBound, 9)
        self.assertEquals(files[2].ranges[0].higherBound, 19)
        self.assertEquals(files[2].ranges[1].lowerBound, 804)
        self.assertEquals(files[2].ranges[1].higherBound, 823)

    def test_extract_line_range_extract_2_ranges_for_file_four(self):
        files = DiffFile("test/sa_diff/diff.txt").files

        self.assertEquals(files[3].name, "NcpLink.java")
        self.assertEquals(len(files[3].ranges), 2)

        self.assertEquals(files[3].ranges[0].lowerBound, 8)
        self.assertEquals(files[3].ranges[0].higherBound, 18)
        self.assertEquals(files[3].ranges[1].lowerBound, 705)
        self.assertEquals(files[3].ranges[1].higherBound, 729)


class ReportParsingTest(unittest.TestCase):


    def test_extract_issues_extract_six_issues(self):
        report = Report("test/sa_diff/report_six_issues.html")

        self.assertEquals(len(report.issues), 6)


    def test_extract_issues_extract_one_issue(self):
        report = Report("test/sa_diff/report.html")

        self.assertEquals(len(report.issues), 1)

    def test_extract_issues_extract_one_issue(self):
        report = Report("test/sa_diff/report.html")

        self.assertEquals(report.issues[0].file_name, "/vob/visionway/ctm/tools/pmd/report/myco.KC6400/NetworkModelBuilder.java")
        self.assertEquals(report.issues[0].line_number, 27)

    def test_extract_issues_with_empty_report_extract_no_issues(self):
        report = Report("test/sa_diff/empty_report.html")

        self.assertEquals(len(report.issues), 0)


class FilteringTest(unittest.TestCase):

    def test_keep_issues_in_diff(self):
        issues = [Issue("A.java", 10), Issue("B.java", 30), Issue("B.java", 15)]

        diffFileA = ChangedFile("A.java")
        diffFileA.append(Range(3, 7))
        diffFileA.append(Range(13, 20))

        diffFileB = ChangedFile("B.java")
        diffFileB.append(Range(30, 32))
        diffFileB.append(Range(20, 24))

        diffFileC = ChangedFile("C.java")
        diffFileC.append(Range(27, 32))
        diffFileC.append(Range(31, 31))
        diffFileC.append(Range(40, 45))

        changedFiles = [diffFileA, diffFileB, diffFileC]

        diff = DiffFile("")
        setattr(diff, 'files', changedFiles)

        report = Report("")
        setattr(report, 'issues', issues)
        issuesInDiff = report.issuesIn(diff)

        self.assertEquals(len(issuesInDiff), 1)
        self.assertEquals(issuesInDiff[0].file_name, "B.java")
        self.assertEquals(issuesInDiff[0].line_number, 30)

    def test_keep_issues_in_diff_when_issue_is_on_first_line(self):
        issues = [Issue("A.java", 10)]

        diffFile = ChangedFile("A.java")
        diffFile.append(Range(10, 15))
        diffFile.append(Range(20, 22))

        diff = DiffFile("")
        setattr(diff, 'files', [diffFile])

        report = Report("")
        setattr(report, 'issues', issues)
        issuesInDiff = report.issuesIn(diff)

        self.assertEquals(len(issuesInDiff), 1)
        self.assertEquals(issuesInDiff[0].file_name, "A.java")
        self.assertEquals(issuesInDiff[0].line_number, 10)

    def test_keep_issues_in_diff_when_issue_is_on_last_line(self):
        issues = [Issue("A.java", 22)]

        diffFile = ChangedFile("A.java")
        diffFile.append(Range(10, 15))
        diffFile.append(Range(20, 22))

        diff = DiffFile("")
        setattr(diff, 'files', [diffFile])

        report = Report("")
        setattr(report, 'issues', issues)
        issuesInDiff = report.issuesIn(diff)

        self.assertEquals(len(issuesInDiff), 1)
        self.assertEquals(issuesInDiff[0].file_name, "A.java")
        self.assertEquals(issuesInDiff[0].line_number, 22)

    def test_keep_issues_in_diff_when_no_issue_in_diff(self):
        issues = [Issue("A.java", 70), Issue("A.java", 80), Issue("B.java", 40)]

        diffFileA = ChangedFile("A.java")
        diffFileA.append(Range(10, 15))
        diffFileA.append(Range(20, 22))

        diffFileB = ChangedFile("B.java")
        diffFileB.append(Range(10, 15))
        diffFileB.append(Range(20, 22))

        diff = DiffFile("")
        setattr(diff, 'files', [diffFileA, diffFileB])

        report = Report("")
        setattr(report, 'issues', issues)
        issuesInDiff = report.issuesIn(diff)
        self.assertEquals(len(issuesInDiff), 0)

class IssueTest(unittest.TestCase):

    def test_line_number_should_be_an_int(self):

        issue = Issue()
        issue.line_number = "12"
        self.assertEquals(12, issue.line_number)

class IntegrationTest(unittest.TestCase):

    def test_no_issues_in_diff(self):

        report = Report("test/sa_diff/report.html")
        self.assertEquals(len(report.issuesIn("test/sa_diff/no_issues_diff.txt")), 0)

    def test_should_return_empty_report_when_no_issues_found_in_diff(self):

        report = Report("test/sa_diff/report.html")
        diffFileWithNoIssues = "test/sa_diff/no_issues_diff.txt"
        EMPTY_REPORT = """<html>
<head>
	<title>PMD</title>
</head>
<body>
<center>
	<h3>PMD report</h3>
</center>
<center>
	<h3>Problems found</h3>
</center>
<table>
	</table>
</body>
</html>"""
        #print report.keepIssuesIn(diffFileWithNoIssues)
        self.assertEquals(report.keepIssuesIn(diffFileWithNoIssues), EMPTY_REPORT)

    def test_should_return_one_issue(self):

        report = Report("test/sa_diff/report_with_two_issue.html")
        diffFileWithNoIssues = "test/sa_diff/diff_with_one_issue.txt"
        filteredReport = report.keepIssuesIn(diffFileWithNoIssues)
        
        tr_tags = filteredReport.count("<tr")
        self.assertEquals(tr_tags, 2)
	
if __name__ == "__main__":
    unittest.main()
