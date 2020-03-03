"""This script perform an efficient build of the Maven modules.
By default it build only projects that have been modified in the view.

Author: siasi@cisco.com
Date: October 2012

"""


from optparse import OptionParser
import sys
from subprocess import call
from cc import *

def mavenBuild(buildCommand):
    try:
        retcode = call(buildCommand, shell=True)
        if retcode > 0:
            print >>sys.stderr, "Build failed"
            sys.exit(retcode)
    except OSError, e:
        print >>sys.stderr, "UT Execution failed:", e
        sys.exit(-1)

def getImpactedModules(changeSet):
    prefixLen = len("/vob/visionway/ctm") + 1
    return [module[prefixLen:] for module in changeSet.impactedModules]

def buildAlsoDependents(changeSet):
    impactedModules = getImpactedModules(changeSet)
    print "Building " + str(impactedModules)
    buildCommand = "cd /vob/visionway/ctm; mvn -N install; mvn reactor:make-dependents -Dmake.folders=" + ",".join(impactedModules)
    mavenBuild(buildCommand)

def buildChanged(changeSet):
    impactedModules = getImpactedModules(changeSet)
    print "Building " + str(impactedModules)
    buildCommand = "cd /vob/visionway/ctm; mvn -N install; mvn reactor:make -Dmake.folders=" + ",".join(impactedModules)
    mavenBuild(buildCommand)


def build(changeSet, buildDependents):
    if buildDependents:
        print "Build changed Projects and dependents"
        buildAlsoDependents(changeSet)
    else:
        print "Build changed Projects only"
        buildChanged(changeSet)

if __name__ == "__main__":
    import __init__ as lazyjack
    parser = OptionParser(prog="build", usage="%prog [options]", description=__doc__, version=lazyjack.opt_ver)
    parser.add_option("-d", "--build-dependents", action="store_true", dest="buildDependents",
                    help="Build changed Maven projects and dependents projects. By default only changed projects are built.", metavar="FILE")

    (opts, args) = parser.parse_args()

    viewName = runInCcViewOrDie()

    cs = getChangeSet()

    if cs.isEmpty():
        print "Changeset is empty: nothing to commit."
        sys.exit(-1)

    build(cs, opts.buildDependents)
