
"File path filters for the scan_view module."

import re

# The list of private files (files local to the view and owned by the user)
# is obtained with the "ct lsprivate" command

# First filter.
# This is a list of file path patterns
# is used to exclude files from the list of private files
# (for example class files, eclipse project files etc.)
SRC_EXCLUDE_SCANNERS = [re.compile(r'/target/'),
                        re.compile(r'/target$'),
                        re.compile(r'/release/'),
                        re.compile(r'/release$'),
                        re.compile(r'/Trash/'),
                        re.compile(r'/\.settings$'),
                        re.compile(r'/ctm/server/IAInstall/buildlog.xml'),
                        re.compile(r'/ctm/server/main/src/CTMLicense.c'),
                        re.compile(r'/pmd/report'),
                        re.compile(r'/vob/visionway/ctm/patches/'),
                        re.compile(r'/vob/visionway/ctm/server/cfg/'),
                        re.compile(r'/vob/visionway/ctm/server/config/'),
                        re.compile(r'/vob/visionway/ctm/server/expect/'),
                        re.compile(r'/vob/visionway/ctm/server/ext_auth/pam/'),
                        re.compile(r'/vob/visionway/ctm/server/gwtl1/'),
                        re.compile(r'/vob/visionway/ctm/server/h/openssl/'),
                        re.compile(r'/vob/visionway/ctm/server/install/vws/insert_montype_\d+_\d+\.sql'),
                        re.compile(r'/vob/visionway/ctm/server/jmoco/test/'),
                        re.compile(r'/vob/visionway/ctm/server/libssh/'),
                        re.compile(r'/vob/visionway/ctm/server/main/cfg/hfr/'),
                        re.compile(r'/vob/visionway/ctm/server/main/cfg/ios7600/'),
                        re.compile(r'/vob/visionway/ctm/server/sim800/'),
                        re.compile(r'/vob/visionway/ctm/server/snmp/'),
                        re.compile(r'/vob/visionway/ctm/server/sw/'),
                        re.compile(r'/vob/visionway/ctm/server/tcl/'),
                        re.compile(r'/vob/visionway/ctm/server/telnetgw/'),
                        re.compile(r'/vob/visionway/ctm/server/TL1/'),
                        re.compile(r'/vob/visionway/ctm/server/tools/'),
                        re.compile(r'/vob/visionway/ctm/tools/'),
                        re.compile(r'/vob/visionway/<DIR-'),
                       ]

# Second filter
# After exclusion get only source files identified by extension or prefix
SRC_FILE_SCANNERS = [re.compile(r'\.java$'),
                     re.compile(r'\.xml$'),
                     re.compile(r'\.c$'),
                     re.compile(r'\.h$'),
                     re.compile(r'\.sh$'),
                     re.compile(r'ctms-\w+$'),
                     re.compile(r'\.sql$'),
                     re.compile(r'\.properties$'),
                     re.compile(r'\.png$'),
                     re.compile(r'\.py$'),
                     re.compile(r'\.conf$'),
                     re.compile(r'\.jsp$'),
                     re.compile(r'\.js$'),
                     re.compile(r'\.css$'),
                    ]

# Third filter
# This list of string contains private files which pass the
# previuos two filter but is *not* necessary to list because are
# "generated" or third party source files.
excluded_files = ["/vob/visionway/ctm/client/cpofs/src/main/DB_Console/runme.sh",
                  "/vob/visionway/ctm/common/platform/src/main/java/com/cisco/stardm/platform/event/BaseEventCause.java",
                  "/vob/visionway/ctm/common/platform/src/main/java/com/cisco/stardm/platform/event/BaseEventType.java",
                  "/vob/visionway/ctm/lib/java/jdk-6u33-solaris-sparc.sh",
                  "/vob/visionway/ctm/lib/java/jdk-6u33-solaris-sparcv9.sh",
                  "/vob/visionway/ctm/server/dbserv/h/dbserv_eventCause.h",
                  "/vob/visionway/ctm/server/dbserv/h/dbserv_eventType.h",
                  "/vob/visionway/ctm/server/gwtl1/h/ifindex_constants.h",
                  "/vob/visionway/ctm/server/gwtl1/h/mod_constants.h",
                  "/vob/visionway/ctm/server/gwtl1/h/obj_constants.h",
                  "/vob/visionway/ctm/server/install/vws/insert_eventcause.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_eventtype.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_eventtype_305.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_eventtype_454.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_eventtype_600.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_eventtype_600_131.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_eventtype_601.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_ifindex_rules.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_modTypeList.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_objTypeList.sql",
                  "/vob/visionway/ctm/server/install/vws/insert_other_eventtype_454.sql",
                  "/vob/visionway/ctm/server/main/src/version.c",
                  "/vob/visionway/ctm/tools/TST/ctms-toolkit.zip",
                 ]
