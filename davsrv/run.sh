#!/bin/sh -f

set -e

# Re-set permission to the `radicale` user if current user is root
# This avoids permission denied if the data volume is mounted by root
if [ "$1" = 'radicale' ] && [ "$(id -u)" = '0' ]; then
    #chown -R radicale:radicale /data
    exec 2> /var/log/radicale/radicale.log
    exec "$@"
else
  exec "$@"
fi
