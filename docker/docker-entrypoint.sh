#!/bin/bash

supervisord -c /etc/supervisord.conf

cron -f > /dev/null 2>&1