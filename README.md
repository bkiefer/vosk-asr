# An ASR client using a vosk server sending output to MQTT

*DO NOT RUN THIS IN A CONDA OR VIRTUAL ENVIRONMENT WITH SEPARATE PYTHON BINARY, THE PYTHON BINARY HAS TO BE THAT OF YOUR NATIVE OS INSTALLATION*

Install python bindings for the gstreamer libraries

```
sudo apt install libgirepository1.0-dev python3-gst-1.0 libcairo2-dev python3-pip


pip install -r requirements.txt
```

Start MQTT broker and vosk kaldi server with `./run_support.sh`

Start ASR locally, maybe you have to adapt the pipeline in `local_de_config.yaml`

```
python mqtt_micro_asr.py local_de_config.yaml
```

The ASR result will be send to the `voskasr/asrresult/<lang>` MQTT topic.
