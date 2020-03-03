
"Utility module to check for source files not created in clearcase."

# author ceplacan@cisco.com

import commands
import os

from scan_view_cfg import SRC_EXCLUDE_SCANNERS
from scan_view_cfg import SRC_FILE_SCANNERS
from scan_view_cfg import excluded_files


def scan(line, scanners):
    "Returns true if a line contains a pattern in scanners."
    for scanner in scanners:
        if scanner.search(line):
            return True
    return False


def ls_private():
    "Returns a list of local files of the view."
    # clearcase command to retrieve local files
    cmd = 'cleartool lsprivate'
    file_list = commands.getoutput(cmd).split('\n')
    return [x for x in file_list if x != '']



def search_source_elems(basedir):
    "Returns the list of source files."
    src_files = []
    for path, dirs, files in os.walk(basedir):
        abs_files = (os.path.join(path, f) for f in files)
        filt_files = (f for f in abs_files if not scan(f, SRC_EXCLUDE_SCANNERS) and f not in excluded_files)
        src_files.extend([f for f in filt_files if scan(f, SRC_FILE_SCANNERS)])
    return src_files


def sub_paths(path):
    "Returns all possible sub-paths of path:string."
    pieces = path.split(os.path.sep)
    lp = len(pieces)
    i = 0
    acc = os.path.sep
    while i < lp:
        acc = os.path.join(acc, pieces[i])
        i = i + 1
        # this function is a generator
        yield acc


def add_parent_dirs(dir_list):
    "Returns all possible parent dirs of dir_list:list"
    grouped_dirs = [(x, y) for x in dir_list for y in sub_paths(x)]
    return [x[1] for x in grouped_dirs]


def search_new_elems():
    "Returns a list of possible files that need to be created."
    private_files = ls_private()
    filt_files = [f for f in private_files if not scan(f, SRC_EXCLUDE_SCANNERS) and f not in excluded_files]
    src_files = [f for f in filt_files if scan(f, SRC_FILE_SCANNERS)]
    # first level dirs of the new files
    dirs = [os.path.split(d)[0] for d in src_files if os.path.split(d)[0] in filt_files]
    # add parent dirs
    dirs_with_parents = [d for d in add_parent_dirs(dirs) if d in filt_files]
    # remove duplicates
    dir_set = set(dirs_with_parents)
    return list(dir_set) + src_files


def main():
    "Main function."
    for filename in search_new_elems():
        print filename


if __name__ == '__main__':
    # just for testing purpose
    import cProfile as prof
    prof.Profile.bias = 7e-6
    print 'Profiling...'
    prof.run('main()', 'scan_view.prof')
    import pstats
    stats = pstats.Stats('scan_view.prof')
    stats.sort_stats('cumulative')
    stats.print_stats()
