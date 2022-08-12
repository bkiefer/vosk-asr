#!/bin/sh
sudo chmod a+rwX audio
python -u "mqtt_micro_asr.py" "user_config.yaml"
