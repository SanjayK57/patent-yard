#!/bin/bash
# All patents, start to finish once the export is downloaded: build the data, upload it to its two Pages projects,
# then restart the publisher so the next website build switches the section on. Progress: world.log.
cd "$(dirname "$0")"
PY=/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3
while pgrep -f "download_worl[d].sh" >/dev/null; do sleep 30; done
n=$(ls raw/world/parts | grep -c 'json.gz$')
[ "$n" -ge 1000 ] || { echo "only $n of 1000 export files downloaded; run download_world.sh again"; exit 1; }
$PY -u world.py build > world.log 2>&1 || { echo "build failed"; tail -5 world.log; exit 1; }
$PY -u world.py deploy >> world.log 2>&1 || { echo "deploy failed"; tail -5 world.log; exit 1; }
for p in $(pgrep -f "pipeline.py publis[h]"); do kill "$p"; done
while pgrep -f "pipeline.py we[b]|pages deplo[y] dist" >/dev/null; do sleep 30; done
nohup caffeinate -i $PY -u pipeline.py publish >> publish.log 2>&1 &
echo "All patents deployed; publisher restarted"
