cd `dirname $0`
docker container ls | grep -q mqtt-broker ||
    docker run -d -p1883:1883 -p9001:9001 \
           -v ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro \
           --name mqtt-broker eclipse-mosquitto:2.0.15

# select server for the required language: de or en
if test -z "$ASR_LANG"; then ASR_LANG="de" ; fi
docker container ls | grep -q kaldi-$ASR_LANG ||
    docker run -d -p 2700:2700 \
           --name kaldi_asr_$ASR_LANG alphacep/kaldi-$ASR_LANG:latest
