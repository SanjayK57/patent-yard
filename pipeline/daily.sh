#!/bin/bash
# The daily check without Claude: recheck every listing, add newly expired patents, fetch their text and drawings,
# and keep the two long-running jobs alive (the website publisher and the bulk download). The hand-written notes
# for the best new patents are the one thing it skips; ask Claude for those (pipeline.py todo / notes).
#
# Run by ~/Library/LaunchAgents/dev.patentyard.daily.plist at 9 AM, 9 PM and at login (so a restart doesn't leave
# the jobs dead). Progress: daily.log. Safe to run by hand: a second copy exits at once.
cd "$(dirname "$0")" || exit 1
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"   # npx (wrangler) for the publisher
PY=/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3
LOCK=/tmp/patentyard-daily.lock
mkdir "$LOCK" 2>/dev/null || { echo "$(date '+%F %R') already running"; exit 0; }
trap 'rmdir "$LOCK"' EXIT

log() { echo "$(date '+%F %R') $*"; }
keep() {  # start a long-running job detached unless it's already running
  pgrep -f "pipeline.py $1" >/dev/null && return
  nohup caffeinate -i "$PY" -u pipeline.py "$1" >> "$1.log" 2>&1 &
  log "started $1"
}

log "daily check"
keep publish
keep bulk

"$PY" -u pipeline.py verify > verify.log 2>&1 || log "verify failed: $(tail -1 verify.log)"
log "$(tail -1 verify.log)"

# a fresh harvest once the last is 6+ days old (the Official Gazette comes out on Tuesdays), else finish the last one
if [ -n "$(find raw/queue.json -mtime +5 2>/dev/null)" ] || [ ! -e raw/queue.json ]; then
  "$PY" -u pipeline.py harvest --per 4 > harvest.log 2>&1
else
  "$PY" -u pipeline.py harvest --resume > harvest.log 2>&1
fi
# from 2026-11-07 Patent Public Search needs a USPTO.gov sign-in; the harvest then fails with 401/403 until the
# pipeline gets a USPTO Open Data Portal API key (data.uspto.gov/apikey). Everything else keeps working.
grep -qE "HTTP Error 40[13]" harvest.log && log "harvest blocked by the USPTO sign-in: needs an Open Data Portal API key"
log "harvest: $(tail -1 harvest.log)"

"$PY" -u pipeline.py enrich --sheets 150 > enrich.log 2>&1
log "enrich: $(tail -1 enrich.log)"
"$PY" pipeline.py test > test.log 2>&1 && log "tests pass" || log "TESTS FAIL: $(tail -3 test.log | tr '\n' ' ')"
log "done; the publisher deploys the changes within 2 hours"
