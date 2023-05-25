# An ASR client using a vosk server sending its output to the MQTT topic /asrresult

# Build docker image

./build_docker.sh

# run it via docker compose

Make sure no other MQTT broker is running and using port 2700. This uses the config file `dock_config.yaml`, so make sure the configuration is correct. You can use parts of the device name to identify the audio device, just make sure it is unique so you pick the right one. A list of the devices is printed when the vosk_asr container starts.

```
./run_compose.sh
```

# Running locally for debugging or development

Create a conda or virtualenv with the packages in `requirements.txt`

Start MQTT broker and vosk kaldi server, if necessary, with `./run_support.sh`

Now either build the docker, and start it in interactive mode with `run_docker.sh`. To start the client, you can use the `startclient.sh` script in the docker environment. This uses the `local_config.yaml` file.

Or start it locally, with
```
python mqtt_micro_asr.py local_config.yaml
```
