
"Ansible automatic installation entry script."

from ansible.inventory.ini import InventoryParser

import optparse
import re
import subprocess


valid_target_dir_patterns = [re.compile(r'^/data/[^/]+(?:/+[^/]+)*$'),
                             re.compile(r'^/tmp/[^/]+(?:/+[^/]+)*$'),
                             re.compile(r'^/ws/[^/]+(?:/+[^/]+)*$')]

cmd_list = ['ansible-playbook', '--private-key=~/.ssh/ci_rsa', '-i', 'hosts']


def validate_target_dir(target_build_dir):
    "Since target build dir is removed with rm -f check if path is valid."
    matches = (x.search(target_build_dir) for x in valid_target_dir_patterns)
    matches = [x for x in matches if x]
    return len(matches) > 0

def main(opts):
    "Launches ansible-playbook and prints his stdout in this process."
    p = InventoryParser('hosts')
    dir = p.groups['all'].vars['target_build_dir']
    if validate_target_dir(dir):
        if opts.view == True:
            if opts.clean == True:
                cmd_list.append('deploytolocal.yml')
            else:
                cmd_list.append('viewtolocal.yml')
        else:
            if opts.clean == True:
                cmd_list.append('deploy.yml')
            else:
                cmd_list.append('install.yml')
        proc = subprocess.Popen(cmd_list)
        proc.communicate()
    else:
        print "target_build_dir %s is not valid" % dir


if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)
    parser.add_option("-c", "--clean", action="store_true", dest="clean",
                      default=False, help="remove installation then install again.")
    parser.add_option("-v", "--view", action="store_true", dest="view",
                      default=False, help="install from view if an installation is not present.")
    options = parser.parse_args()[0]
    main(options)

