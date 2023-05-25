export AUDIO_GID="$(getent group audio | cut -d: -f3)"
export UID
docker compose up
