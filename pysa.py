
"Static analysis for Python."

import sys
from pylint import lint
from pylint.reporters.text import ParseableTextReporter

pythonpath = [
'/vob/visionway/ctm/common/platform/src/main/resources/catalog',
'/vob/visionway/ctm/tools/DBtools',
'/vob/visionway/ctm/tools/TST',
'/vob/visionway/ctm/tools/TST/suite',
'/vob/visionway/ctm/tools/jalopy/bin',
'/vob/visionway/ctm/tools/staticTreeEditor/scripts',
'/vob/visionway/ctm/server/install/vws/python',
'/vob/visionway/ctm/server/jmoco/test',
'/vob/visionway/ctm/server/cdimage/bin',
'/vob/visionway/ctm/server/cdimage/lib/python',
'/vob/visionway/ctm/HA/Linux/installer',
'/vob/visionway/ctm/HA/Linux/script',
'/vob/visionway/ctm/HA/Linux/script/MulticastHeartBeat',
'/vob/visionway/ctm/HA/Linux/script/GEOManager',
'/vob/visionway/ctm/HA/Linux/test',
'/vob/visionway/ctm/JSONModelBrowser',
]

class WriteableObject:
    "An utility class to call pylint programmatically."

    def __init__(self):
        self.content = []

    def write(self, string):
        "Dummy write method."
        self.content.append(string)

def no_exit(arg):
    "A no-op utility function."
    arg = arg

def convert_to_html_table(seq):
    "Converts seq:list into html table."
    t = ['<html>', '<body>', '<table border="1" width="100%">']
    for row in seq:
        t.append('<tr><td>%s</td></tr>' % row)
    t = t + ['</table>', '</body>', '</html>']
    return t

def run_pylint(filelist):
    "Executes pylint on python files programmatically."
    sys.path = sys.path + pythonpath
    args = ["--rcfile=/opt/dev-tools/pylint/pylintrc"] + filelist
    pylint_output = WriteableObject()
    original_exit = sys.exit
    sys.exit = no_exit
    lint.Run(args, reporter=ParseableTextReporter(pylint_output))
    sys.exit = original_exit
    return [line.strip() for line in pylint_output.content if line.strip()]

def test_run_pylint():
    "py.test testcase."
    issues = run_pylint(['sa.py'])
    assert len(issues) > 0
