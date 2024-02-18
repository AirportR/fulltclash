#!/bin/bash

if [[ ! -f /app/resources/config.yaml ]]; then
cat > /app/resources/config.yaml <<EOF
clash:
 path: './bin/fulltclash-${branch}'
 core: ${core}
 startup: 1124
 branch: ${branch}
websocket:
  bindAddress: "${bind}"
  token: "${token}"
EOF
fi

if [ ! -z "${buildtoken}" ]; then
  echo "buildtoken: ${buildtoken}" >> /app/resources/config.yaml
fi

supervisord -c /etc/supervisord.conf

crond -f > /dev/null 2>&1