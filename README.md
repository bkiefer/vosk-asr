# Build docker image

./build_docker.sh

# Start websocket ASR client sending output to MQTT topic /asrresult

Starts MQTT broker and vosk kaldi server, if necessary

```
./run_docker.sh
```

# Start vosk kaldi server (done by main script)

docker run -d -p 2700:2700 --name vosk_asr alphacep/kaldi-de:latest

# Start MQTT broker (done by main script

docker run -d -p1883:1883 --name mqtt ncarlier/mqtt
