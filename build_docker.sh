docker build --network="host" -f Dockerfile -t vosk_asr --build-arg USERID=$(id -u) .
