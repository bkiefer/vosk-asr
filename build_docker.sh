docker build --network="host" -f Dockerfile -t drz_vosk_asr --build-arg USERID=$(id -u) .
