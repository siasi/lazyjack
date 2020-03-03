
"Schedules the vob ranking task."

import csv
import os
import sched
import score_vob
import bugprediction
import time

score_vob.cache = bugprediction.DefectsCache()

def score_vob_task():
    "This is score vob task."
    #start = time.time()
    #print "running..."
    score_vob.scoreProject()
    
    #print "finished in", time.time() - start, "secs"


def loop():
    "Starts the score vob task and reschedules it every day."
    s = sched.scheduler(time.time, time.sleep)
    # start a task immediately
    score_vob_task()
    # then schedules it every 24H
    while True:
        s.enter(24 * 60 * 60, 1, score_vob_task, ())
        s.run()


if __name__ == '__main__':
    loop()
