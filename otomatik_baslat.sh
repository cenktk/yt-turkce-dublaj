#!/bin/sh
# Installs the dub server as a macOS login service (launchd) so the extension finds it after every reboot.
# Run once: sh otomatik_baslat.sh      Remove: launchctl bootout gui/$(id -u)/com.yt-dublaj; rm ~/Library/LaunchAgents/com.yt-dublaj.plist
set -e
KOK=$(cd "$(dirname "$0")" && pwd)
# macOS gives background services no access to Documents and Desktop: the service dies with exit 78 (EX_CONFIG).
case "$KOK" in "$HOME/Documents"*|"$HOME/Desktop"*)
  echo "Repo $KOK altinda. Servis orada calisamaz; once tasi:  mv \"$KOK\" ~/yt-turkce-dublaj"; exit 1;; esac
PY=$(command -v python3)
# launchd starts with a bare PATH, so the folders of yt-dlp, ffmpeg and claude are written into the service.
P=$(dirname "$(command -v yt-dlp)"):$(dirname "$(command -v ffmpeg)"):$(dirname "$(command -v claude)"):/usr/bin:/bin
PLIST=$HOME/Library/LaunchAgents/com.yt-dublaj.plist
mkdir -p "$HOME/Library/LaunchAgents" "$KOK/dublaj"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.yt-dublaj</string>
  <key>ProgramArguments</key><array>
    <string>$PY</string><string>-u</string><string>$KOK/hazirla.py</string><string>serve</string><string>--port</string><string>8790</string>
  </array>
  <key>WorkingDirectory</key><string>$KOK</string>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>$P</string><key>HOME</key><string>$HOME</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$KOK/dublaj/serve.log</string>
  <key>StandardErrorPath</key><string>$KOK/dublaj/serve.log</string>
</dict></plist>
PL
launchctl bootout "gui/$(id -u)/com.yt-dublaj" 2>/dev/null || true
pkill -f 'hazirla.py serve' 2>/dev/null || true  # a hand-started server would keep port 8790
launchctl bootstrap "gui/$(id -u)" "$PLIST"
sleep 2
curl -s -m 3 -X POST -H 'X-Dublaj: 1' http://localhost:8790/durum/dQw4w9WgXcQ && echo && echo "tamam: sunucu her girişte kendiliğinden açılır"
