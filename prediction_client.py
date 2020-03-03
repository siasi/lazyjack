
"Bug prediction service client."

import socket
import zmq

def reload(server):
    "Request to the server to reload the bug prediction DB."
    init_zmq(server)
    s.send("RELOAD")
    s.recv()

def ask_score(server, changeset):
    "Give a a list of filenames retrieve a boolean saying if the changeset has high probability to inject a bug."
    init_zmq(server)
    s.send(",".join(changeset))

    return s.recv()

def init_zmq(server):
    context = zmq.Context()
    s = context.socket(zmq.REQ)
    s.connect("tcp://%s:5000" % socket.gethostbyname(server))
    #s.connect("tcp://%s:6000" % socket.gethostbyname(server))

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3:
        # comma separated abs filename list
        ask_score(*sys.argv[1:])
    else:
        print "usage: %s prediction-hostname comma-sep-filelist" % sys.argv[0]
