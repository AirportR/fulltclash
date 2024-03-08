#!/bin/bash

if [[ ! -f /app/resources/config.yaml ]]; then
cat > /app/resources/config.yaml <<EOF
admin:
  - ${admin}
bot:
 api_id: ${api_id}
 api_hash: ${api_hash}
 bot_token: ${bot_token}
clash:
 path: './bin/fulltclash-${branch}'
 core: ${core}
 startup: ${startup}
 branch: ${branch}
pingurl: https://www.gstatic.com/generate_204
netflixurl: "https://www.netflix.com/title/80113701"
speedfile:
  - https://dl.google.com/dl/android/studio/install/3.4.1.0/android-studio-ide-183.5522156-windows.exe
  - https://dl.google.com/dl/android/studio/install/3.4.1.0/android-studio-ide-183.5522156-windows.exe
speednodes: ${speednodes}
speedthread: ${speedthread}
nospeed: ${nospeed}
EOF

if [ ! -z "${s5_proxy}" ]; then
sed -i '/bot:/a\ proxy: '"${s5_proxy}" /app/resources/config.yaml
fi
if [ ! -z "${http_proxy}" ]; then
  echo "proxy: ${http_proxy}" >> /app/resources/config.yaml
fi

fi

supervisord -c /etc/supervisord.conf

if [[ -f "/etc/debian_version" ]]; then
    cron -f > /dev/null 2>&1
fi

if [[ -f "/etc/alpine-release" ]]; then
    crond -f > /dev/null 2>&1
fi