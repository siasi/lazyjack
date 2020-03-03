
"Script to list the files probably missing cc_mkelem."

from scan_view import main
from cc import runInCcViewOrDie

if __name__ == '__main__':
    runInCcViewOrDie()
    main()
