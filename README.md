# An ASR client using a vosk server sending output to MQTT

*DO NOT RUN THIS IN A CONDA OR VIRTUAL ENVIRONMENT WITH SEPARATE PYTHON BINARY, THE PYTHON BINARY HAS TO BE THAT OF YOUR NATIVE OS INSTALLATION*

Install python bindings for the gstreamer libraries

```
sudo apt install libgirepository1.0-dev python3-gst-1.0 libcairo2-dev python3-pip


pip install -r requirements.txt
```

Start MQTT broker and vosk kaldi server with `./run_support.sh`

Start ASR locally, maybe you have to adapt the pipeline in `local_de_config.yaml`, or the language, the current default expects a ReSpeaker as default PulseAudio device. For the ReSpeaker, use the multichannel, not the analog-stereo.monoto device! You can check your local audio device configuration with

```
pacmd list-sources | grep -e 'index:' -e device.string -e 'name:'
```

To set the default source to the ReSpeaker, use:

```
pacmd set-default-source 'alsa_input.usb-SEEED_ReSpeaker_4_Mic_Array__UAC1.0_-00.multichannel-input'
```

Check the content of gstmicpipeline.py in case of problems. In the audio directory, the microphone audio is stored in asrmon-XX.wav files and the data transferred to the ASR in chunk-XX.wav

```
python mqtt_micro_asr.py local_de_config.yaml
```

The ASR result will be send to the `voskasr/asrresult/<lang>` MQTT topic.
