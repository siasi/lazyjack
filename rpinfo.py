
"Query a csv file containing release and patch information."

import csv
import optparse
import tabular_data

class NameInfo(object):
    "Selects information by name."

    def __init__(self, table, query):
        self.table = table
        self.query = query

    def display(self):
        "Displays information."
        header = [x.title() for x in self.table[0]]
        format = '%24s%24s%24s'
        print format % tuple(header)
        # use template method DP
        for row in self.select():
            print format % tuple(row)

    def select(self):
        "Selects by name."
        return [x for x in self.table[1:] if x.name == self.query.lower()]


class VersionInfo(NameInfo):
    "Selects information by version."

    def select(self):
        "Selects by version."
        return [x for x in self.table[1:] if x.version == self.query]


def main(opts, args):
    "Main."
    datafile = open('release_and_patch_info.csv', 'rb')
    table = [x for x in tabular_data.get_table(csv.reader(datafile))]
    datafile.close()
    if opts.version == True:
        info = VersionInfo(table, args[0])
    else:
        info = NameInfo(table, args[0])
    info.display()

if __name__ == '__main__':
    parser = optparse.OptionParser("%prog query-string [-v]")
    parser.add_option("-v", "--version", action="store_true", dest="version", default=False, \
                      help="Print info using a version string")
    options, arguments = parser.parse_args()
    main(options, arguments) 
