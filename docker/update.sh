#!/bin/bash
. /etc/profile

git_version=$(git --git-dir='/app/.git' --work-tree='/app' rev-parse HEAD)
last_version=$(curl -Ls "https://api.github.com/repos/AirportR/FullTclash/commits/dev" | jq .sha | sed -E 's/.*"([^"]+)".*/\1/')

update() {
    git --git-dir='/app/.git' --work-tree='/app' fetch --all
    git --git-dir='/app/.git' --work-tree='/app' reset --hard origin/dev
    git --git-dir='/app/.git' --work-tree='/app' pull
}

if [[ $last_version ==  "$git_version" ]]; then
    echo -e "已是最新版本，无需更新"
else
    echo -e "检查到新版本，正在更新"
    update
    /opt/venv/bin/supervisorctl restart fulltclash
fi