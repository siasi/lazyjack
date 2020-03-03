"""This module can be used to check the usage of LazyJack toolkit.
   It prints out the list of users that do not have import of lazyjack.alias in .cshrc_USER file.
   
"""

import os


users = [
  'clapicci',
  'gguerrer',
  'gregorim',
  'aarchett',
  'dsivigli',
  'pcasarot',
  'pdelbuon',
  'mbronzi',
  'mcaccian',
  'mamato',
  'siasi',
  'lsona',
  'mrighett',
  'raltavil',
  'pacaruso',
  'daniemar',
  'ighidini',
  'lbertilo',
  'epagliar',
  'fbonora',
  'ifavelli',
  'rgarofal',
  'nfranzos',
  'amonguzz',
  'ceplacan',
  'edavanzo',
  'jaludden',
  'spaolo',
  'sbarella',
  'abotti',
]

usage = {}
for user in users:
    folder = "/users/" + user
    if not os.path.exists(folder) or not os.path.exists(folder):
        print "User ", user, "not valid"
        continue
    cshrcPath = folder + "/.cshrc_USER"
    if not os.path.exists(cshrcPath):
        print "User", user, "does not have .cshrc_USER"
        continue
    cshrc = open(cshrcPath)
    lines = [line for line in cshrc.readlines() if "/opt/dev-tools/lazyjack" in line]
    cshrc.close()
    for line in lines:
        if "/opt/dev-tools/lazyjack/beta" in line:
            usage[user] = "BETA"
        elif "/opt/dev-tools/lazyjack/release" in line:
            usage[user] = "RELEASE"
    print user, ":", usage.get(user, "NONE")

