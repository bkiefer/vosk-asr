cd `dirname $0`
docker container ls | grep -q mqtt-broker ||
    docker run -d -p1883:1883 -p9001:9001 \
           -v ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro \
           --name mqtt-broker eclipse-mosquitto:2.0.15

docker container ls | grep -q alphacep ||
    docker run -d -p 2700:2700 --name kaldi_asr alphacep/kaldi-de:latest
