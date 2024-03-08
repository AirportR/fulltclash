#!/bin/bash
. /etc/profile

git_branch=$(git --git-dir='/app/.git' --work-tree='/app' rev-parse --abbrev-ref HEAD)
git_version=$(git --git-dir='/app/.git' --work-tree='/app' rev-parse HEAD)

if [[ master ==  "$git_branch" ]]; then
    echo -e "当前分支为 $git_branch"
    echo -e "当前commits位于 $git_version"
    last_version=$(curl -Ls "https://api.github.com/repos/AirportR/FullTclash/commits/master" | jq .sha | sed -E 's/.*"([^"]+)".*/\1/')
elif [[ dev ==  "$git_branch" ]]; then
    echo -e "当前分支为 $git_branch"
    echo -e "当前commits位于 $git_version"
    last_version=$(curl -Ls "https://api.github.com/repos/AirportR/FullTclash/commits/dev" | jq .sha | sed -E 's/.*"([^"]+)".*/\1/')
elif [[ backend ==  "$git_branch" ]]; then
    echo -e "当前分支为 $git_branch"
    echo -e "当前commits位于 $git_version"
    last_version=$(curl -Ls "https://api.github.com/repos/AirportR/FullTclash/commits/backend" | jq .sha | sed -E 's/.*"([^"]+)".*/\1/')
else
    echo -e "暂不支持此分支"
    exit 1
fi

update() {
    git --git-dir='/app/.git' --work-tree='/app' fetch --all
    git --git-dir='/app/.git' --work-tree='/app' reset --hard origin/$git_branch
    git --git-dir='/app/.git' --work-tree='/app' pull
    git_version=$(git --git-dir='/app/.git' --work-tree='/app' rev-parse HEAD)
}

if [[ $last_version ==  "$git_version" ]]; then
    echo -e "已是最新版本，无需更新"
else
    echo -e "检查到新版本，正在更新"
    update
    echo -e "更新完成,当前commits位于 $git_version"
    /opt/venv/bin/supervisorctl restart fulltclash
fi