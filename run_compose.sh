#!/bin/sh
cd `dirname $0`
export AUDIO_GID="$(getent group audio | cut -d: -f3)"
export UID
cmd="$1"
if test -z "$cmd"; then
    cmd="up"
fi
docker compose "$cmd"
