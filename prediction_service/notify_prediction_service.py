import requests
import sys

resp = requests.put("http://gpk-nmtg-cpo02:8089/reload")
if resp.status_code == 200:
    print "Prediction Service successfuly udpated."
else:
    print "Error contacting the Prediction Service"
    print resp.content
    sys.exit(1)
