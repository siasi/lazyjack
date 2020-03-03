#!/usr/bin/env python

"""This module contains logic for deployment of Lazy Jack suite.
   It takes care of generating the proper files of alias for Bash and C-Shell.
   It copies all needed files in the deployment directory.
   It can deploy in Release or Beta stage.
"""

from shutil import copy, copytree, rmtree
from textmenu import yes, TextMenu

import ConfigParser as cfg
import os
import platform
import re
import sys

# import version from __init__.py
import __init__ as lazyjack

def fillTemplate(repofile, destFolder, values):
    "repofile: string, destFolder:string, values: dict are the values to substitute in template."
    template = open(repofile)
    destFile = open(os.path.join(destFolder, repofile), "w+")
    destFileContent = template.read() % values
    destFile.write(destFileContent)
    template.close()
    destFile.close()

parser = cfg.ConfigParser()
parser.read('deploy.cfg')
values = dict(parser.items('main'))

if not yes("Release version "  + lazyjack.__version__ + " is OK?"):
    print "Deploy failed"
    sys.exit(0)

menu = TextMenu(["release", "beta", "homedir"])
deployment = menu.display("Deploy to release or beta or homedir? ")
if deployment == "release":
    destLocation = 'releaselocation'
elif deployment == "beta":
    destLocation = 'betalocation'
else:
    destLocation = 'homedir'
homedir = "/users/%s/test_lj" % os.getenv("USER", "siasi")
tag = deployment.upper()

if not yes("Please confirm, do you want to deploy to %s?" % tag):
    print "Deploy failed"
    sys.exit(0)

dest = values.get(destLocation, homedir)
# add a dest key for templating
values['dest'] = dest

#Create missing folders:
files = values['files'].split(',')
folders = filter(None, (os.path.split(f)[0] for f in files))
folders.append('services')
for folder in folders:
    destFolder = os.path.join(dest, folder)
    if not os.path.exists(destFolder):
        os.makedirs(destFolder)

repopath = '/users/%s/lazyjack' % os.getenv('USER', 'siasi')
for filename in files:
    filepath = os.path.join(repopath, filename)
    destpath = os.path.join(dest, filename)
    copy(filepath, destpath)
    os.chmod(destpath, 0644)

fillTemplate("lazyjack.alias", dest, values)

# build alias for bash
def alias4bash(destpath, vals):
    "Generate alias file for bash."
    alias_re = re.compile(r'^alias\s+(\w+)\s+"(.*)"$')
    f = open('lazyjack.alias')
    text = f.read()
    f.close()
    lines = text.split('\n')
    aliases = []
    for line in lines:
        matched = alias_re.search(line)
        if matched:
            aliases.append((matched.group(1), matched.group(2)))
    template_text = '\n'.join(['alias %s="%s"' % alias for alias in aliases])
    template_text = template_text + '\n'
    text = template_text % vals
    f = open(os.path.join(destpath, 'lazyjack.alias.sh'), 'a')
    f.write(text)
    f.close()

copy(os.path.join(repopath, 'lazyjack.alias.sh'), os.path.join(dest, 'lazyjack.alias.sh'))
alias4bash(dest, values)

os.chmod(os.path.join(dest, 'yasview') , 0754)
os.chmod(os.path.join(dest, "lazyjack.alias.sh") , 0755)
os.chmod(os.path.join(dest, "lazyjack.alias") , 0755)

# ansible stuff
ansible_dest_dir = os.path.join(dest, 'ansible')
if os.path.exists(ansible_dest_dir):
    rmtree(ansible_dest_dir)
copytree(os.path.join(repopath, 'ansible'), ansible_dest_dir)
fillTemplate("ci.sh", ansible_dest_dir, values)
os.chmod(os.path.join(ansible_dest_dir, "ci.sh") , 0775)

# pre-compile the package if the interpreter is the one
# installed in /opt/dev-tools/python
pyver = platform.python_version_tuple()
if pyver[:2] == ("2", "7") and int(pyver[2]) >= 4:
    newpath, module = os.path.split(dest)
    sys.path.append(newpath)
    __import__(module)
else:
    print "WARNING: it was not possible to pre-compile modules."

print "Deploy of " + tag + " version " + lazyjack.__version__ + " completed."
