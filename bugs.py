
"""Displays bugs queries. Use -h option for help.

This scripts prints some handy queries from CDETS DB.

Used without parameters it reports the "unresolved" bugs of the current user.
With the "-a" option it reports all the bugs not only sev. 1,2,3,6 bugs.

Is possible to ask for "unresolved" bugs of other users using the "-u <user>" option,
or ask for bugs submitted by a particular user with "-u <submitter>" and "-s" options.

Is also possible to display the "unresolved" FEA bugs using the "-f" option.
"""

# author ceplacan@cisco.com

import commands
import optparse


def get_command(opts):
    "Returns the findcr command."
    cmd_format_string = 'findcr %s -w Identifier,Severity,Status,Headline -o Severity -s AOWHIPMN "%s"'
    if opts.fea == True:
        query = "[Product]='ctm' and [Component]='new-feature' and [Severity]=6"
        return cmd_format_string % ('', query)
    else:
        if opts.all == True:
            query = "[Product]='ctm'"
        else:
            query = "[Product]='ctm' and ([Severity]=1 or [Severity]=2 or [Severity]=3 or [Severity]=6)"
        if opts.user == '':
            # returns bugs assigned to me
            return cmd_format_string % ('-m', query)
        else:
            if opts.submitter == True:
                user_str = '-t -u %s' % opts.user
            else:
                user_str = '-u %s' % opts.user
            return cmd_format_string % (user_str, query)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-a", "--all", action="store_true", dest="all", default=False, \
                      help="Shows all unresolved bugs not only sev. 1,2,3,6")
    parser.add_option("-f", "--fea", action="store_true", dest="fea", default=False, \
                      help="Shows all unresolved FEA bugs")
    parser.add_option("-s", "--submitter", action="store_true", dest="submitter", default=False, \
                      help="Changes the meaning of -u searching bugs submitted by USER")
    parser.add_option("-u", "--user", dest="user", type="string", default="", \
                      help="Finds bugs assigned to USER")
    options = parser.parse_args()[0]
    cmd = get_command(options)
    print commands.getoutput(cmd)
