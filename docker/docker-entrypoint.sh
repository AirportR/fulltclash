#!/bin/bash

supervisord -c /etc/supervisord.conf

if [[ -f "/etc/debian_version" ]]; then
    cron -f > /dev/null 2>&1
fi

if [[ -f "/etc/alpine-release" ]]; then
    crond -f > /dev/null 2>&1
fi