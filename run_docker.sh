cd `dirname $0`
docker container ls | grep -q mqtt ||
    docker run -d -p1883:1883 --name mqtt ncarlier/mqtt

docker container ls | grep -q alphacep ||
    docker run -d -p 2700:2700 --name kaldi_asr alphacep/kaldi-de:latest

docker run -d -t \
       -v "/etc/alsa:/etc/alsa" \
       -v "/usr/share/alsa:/usr/share/alsa" \
       -v "/run/user/$UID/pulse/native:/run/user/$UID/pulse/native" \
       -v "`pwd`/audio:/app/audio" \
       -v "`pwd`/user_config.yaml:/app/user_config.yaml" \
    --env "PULSE_SERVER=unix:/run/user/$UID/pulse/native" \
    --device /dev/snd \
    --user "$(id -u)" \
    --network "host" \
    --group-add $(getent group audio | cut -d: -f3) \
    drz_vosk_asr
