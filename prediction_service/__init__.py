
"""Bug prediction service

Setup:
Connect to an host the launch a server process
python score_vob_server.py 5000 &

then launch a backup process
python score_vob_server.py 6000 &

Service client will connect to both processes and will be served by the
the first free process in a load balanced fashion."""
