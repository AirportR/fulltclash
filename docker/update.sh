#!/bin/bash

git_version=$(git rev-parse HEAD)
last_version=$(curl -Ls "https://api.github.com/repos/AirportR/FullTclash/commits/dev" | jq .sha | sed -E 's/.*"([^"]+)".*/\1/')

update() {
    git fetch --all
    git reset --hard origin/dev
    git pull
}

cd /app

if [[ $last_version ==  $git_version ]]; then
    echo -e "已是最新版本，无需更新"
else
    echo -e "检查到新版本，正在更新"
    update
    supervisorctl restart fulltclash
fi