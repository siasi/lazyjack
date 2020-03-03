#!/bin/sh

echo "PYTHONPATH = $PYTHONPATH"
DEV_TOOLS="/auto/gpk-dev-tools"
$DEV_TOOLS/python/Linux/2.7.4/py_bin/bin/python $DEV_TOOLS/lazyjack/beta/prediction_service/score_vob.py -w $DEV_TOOLS/lazyjack/cfg
