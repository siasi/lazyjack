
"Bug prediction server."

import os
import score_vob
import socket
import sys
import zmq
import bugprediction
import score_vob


predictionService = bugprediction.PredictionService(score_vob.RANKFILE)

context = zmq.Context()
s = context.socket(zmq.REP)
if len(sys.argv) == 1:
    print "usage: %s listen-port" % sys.argv[0]
    sys.exit(0)
else:
    port = int(sys.argv[1])
    s.bind("tcp://%s:%d" % (socket.gethostbyname(socket.gethostname()), port))
    while True:
        msg = s.recv()

        if msg == 'RELOAD':
        	predictionService = bugprediction.PredictionService(score_vob.RANKFILE)
        	s.send("OK")
        else:
        	# msg is a comma separated list of abs filename
        	s.send(str(predictionService.prediction(msg.split(','))))
