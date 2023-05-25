cd `dirname $0`
docker run -it \
       -v "/etc/alsa:/etc/alsa" \
       -v "/usr/share/alsa:/usr/share/alsa" \
       -v "/run/user/$UID/pulse/native:/run/user/$UID/pulse/native" \
       -v "`pwd`/audio:/app/audio" \
       -v "`pwd`/local_config.yaml:/app/user_config.yaml" \
    --name "vosk_asr" \
    --env "PULSE_SERVER=unix:/run/user/$UID/pulse/native" \
    --device /dev/snd \
    --user "$(id -u)" \
    --network "host" \
    --group-add $(getent group audio | cut -d: -f3) \
    vosk_asr /bin/bash
