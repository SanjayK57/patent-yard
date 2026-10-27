#!/bin/bash
# Installs the daily check (daily.sh) as a login item that runs at 9 AM, 9 PM and whenever the Mac starts up or wakes
# after a missed run, so the website keeps itself up to date with nothing to remember. Run once:
#   bash ~/Desktop/JARVIS/Foundling/pipeline/install-daily.sh
# Undo: launchctl bootout gui/$(id -u)/dev.patentyard.daily; rm ~/Library/LaunchAgents/dev.patentyard.daily.plist
set -e
here="$(cd "$(dirname "$0")" && pwd)"
plist="$HOME/Library/LaunchAgents/dev.patentyard.daily.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>dev.patentyard.daily</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$here/daily.sh</string></array>
  <key>StartCalendarInterval</key><array>
    <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$here/daily.log</string>
  <key>StandardErrorPath</key><string>$here/daily.log</string>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)/dev.patentyard.daily" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist"
echo "Installed. The daily check runs at 9 AM, 9 PM and at login; progress goes to $here/daily.log"
