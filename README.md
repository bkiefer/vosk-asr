# An ASR client using a vosk server sending its output to the MQTT topic /asrresult

# Build docker image (currently not recommended for this version)

```
./build_docker.sh
```

# run it via docker compose (currently not recommended for this version)

Make sure no other MQTT broker is running and using port 2700. This uses the config file `dock_config.yaml`, so make sure the configuration is correct. You can use parts of the device name to identify the audio device, just make sure it is unique so you pick the right one. A list of the devices is printed when the vosk_asr container starts.

```
./run_compose.sh
```

# Running locally for debugging or development

*DO NOT DO THIS IN A CONDA OR VIRTUAL ENVIRONMENT, THE PYTHON BINARY HAS TO BE THAT OF YOUR NATIVE OS INSTALLATION*

`pip install` the packages in `requirements.txt`

Start MQTT broker and vosk kaldi server, if necessary, with `./run_support.sh`

Now either build the docker, and start it in interactive mode with `run_docker.sh`. To start the client, you can use the `startclient.sh` script in the docker environment. This uses the `local_config.yaml` file.

Or start it locally, with (the default configuration should work)
```
python mqtt_micro_asr.py
```
or (if there's something you need to do differently)
```
python mqtt_micro_asr.py local_config.yaml
```
