
"Utility class and functions for interactive scripts."

import re

# Validators
NUMBER_RE = re.compile(r'^\d+$')
CONTINUE_RE = re.compile(r'^[ynYN][eEoO]*[sS]*$')

class TextMenu(object):
    "Textual interactive menu."
    def __init__(self, choices):
        """Constructor.
           choices: list
        """
        self.choices = choices

    def get_input(self, question):
        "Gets user input."
        while True:
            i = raw_input(question)
            if NUMBER_RE.search(i):
                j = int(i)
                if j > 0 and j <= len(self.choices):
                    return self.choices[j - 1]

    def display(self, question):
        "Displays text menu."
        for n, e in enumerate(self.choices):
            print "%d) %s" % (n+1, e)
        return self.get_input(question)


def yes(question):
    "question: string"
    while True:
        i = raw_input("%s [Y/N] " % question)
        if CONTINUE_RE.search(i):
            if i.lower().startswith('y'):
                return True
            else:
                return False


if __name__ == '__main__':
    # Test code
    t = TextMenu(['list files', 'print system info'])
    while True:
        out = t.display('Choose? ')
        if out == 'list files':
            print 'list files chosen'
        if out == 'print system info':
            print 'print system info chosen'
        if yes('Continue?'):
            pass
        else:
            break
