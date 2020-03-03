import bottle, os, optparse
from bottle import post, put, get, run, request, template

class PredictionDb():
    "The prediction DB contaning the list of risky files."
    def __init__(self, workingDir):
        self.workingDir = workingDir
        self.riskyFiles = set()

    def load(self):
        db = open(os.path.join(self.workingDir, 'rankedVob.csv'))
        self.riskyFiles = set([line.split(',')[0] for line in db.readlines()])
        db.close()
	
    def __len__(self):
        return len(self.riskyFiles)
             
	     
@post('/prediction')
def prediction():
    "Return true if any of the passed files is in the risky files DB."
    
    print "Got new prediction request for following changeset:"
    change_set = set([str(filename) for filename in request.json['change_set']])

    print "Comparing with", len(db), "riskyFiles"
    
    changedRisky = change_set & db.riskyFiles
    print "Prediction is", bool(changedRisky)
    print "Risky files changed:"
    print changedRisky
    return str(len(changedRisky))

@put('/reload')
def reload():
    "Reload the prediction DB."

    print "Got new request to reload the db."
    db.load()
    print "DB updated. Current size:", len(db)
    
@get('/')
def index():
    "Return the presentation page."
    
    return '<center><h1>Prediction Service</h1><b>Up and running</b></center>'




parser = optparse.OptionParser(prog="%prog", usage="%prog [options]")#, description=__doc__, version=lazyjack.opt_ver)   
parser.add_option("-w", "--working-dir", dest="workingDir",
                      help="Set the working directory for prediction data.", metavar="DIRECTORY", default ="/opt/dev-tools/lazyjack/cfg/")

(opts, args) = parser.parse_args()

db = PredictionDb(opts.workingDir)
db.load()
print "DB loaded. Current size:", len(db)
run(host='0.0.0.0', port=8089)
