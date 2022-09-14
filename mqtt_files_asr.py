#!/usr/bin/env python3

import sys
import asyncio
import websockets
import logging
import sounddevice as sd
import yaml
import wave
import time

import resampy
import numpy as np

import json
import paho.mqtt.client as mqtt

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def current_milli_time():
    return round(time.time() * 1000)

class VoskMicroServer():
    pid="voskasr"
    audio_dir="audio/"

    channels=1
    usedchannel=1
    sample_rate=0
    asr_sample_rate=16000

    client=None
    loop=None
    audio_queue=None

    def __init__(self, config):
        self.config = config
        if 'asr_sample_rate' in config:
            self.asr_sample_rate = config['asr_sample_rate']

        self.loop = asyncio.get_running_loop()
        self.audio_queue = asyncio.Queue()
        self.__init_mqtt_client()

    def __init_mqtt_client(self):
        self.client = mqtt.Client()
        #self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
        #self.client.on_connect = self.__on_mqtt_connect

    def asrmon_filename(self):
        return self.audio_dir + 'asrmon-%d.wav' % (time.time())

    def open_asrmon_file(self, path):
        """Opens a .wav file.
        Takes path, number of channels and sample rate.
        """
        am = wave.open(path, 'wb')
        am.setnchannels(1)
        am.setsampwidth(2)
        am.setframerate(self.asr_sample_rate)
        return am

    def resample(self, audio):
        if self.sample_rate == self.asr_sample_rate and self.channels == 1:
            return audio

        frame = np.frombuffer(audio, dtype=np.int16)
        if self.channels == 2:
            # channels on separate axes
            frame = np.stack((frame[::2], frame[1::2]), axis=0)
            #print(frame.shape)
            frame = frame[self.usedchannel]
            #print(frame)
        if self.sample_rate != self.asr_sample_rate:
            frame = resampy.resample(frame, self.sample_rate,
                                     self.asr_sample_rate)
        self.am.writeframes(frame)
        return frame.tobytes()

    def mqtt_connect(self):
        self.client.connect(self.config['mqtt_address'])
        self.client.loop_start()

    def mqtt_disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def check_result(self, transcribe):
        data = json.loads(transcribe)
        if data and 'text' in data and data['text'] != '':
            # TODO: not sure if we need this, maybe the MQTT message id is
            # enough?
            data['id'] = current_milli_time()
            print(data)
            self.client.publish(self.pid + '/asrresult',
                                json.dumps(data, indent=None))

    async def send_audio(self, file):
        print("Opening ASR websocket %s" % (self.config['uri']))
        async with websockets.connect(self.config['uri']) as websocket:

            wf = wave.open(file, "rb")
            self.channels = wf.getnchannels()
            self.usedchannel = self.config['use_channel']
            self.sample_rate = wf.getframerate()
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % (self.sample_rate))
            buffer_size = int(self.sample_rate * 0.2) # 0.2 seconds of audio
            while True:
                data = wf.readframes(buffer_size)
                if len(data) == 0:
                    break

                data = self.resample(data)
                await websocket.send(data)
                result = await websocket.recv()
                self.check_result(result)

            await websocket.send('{"eof" : 1}')
            result = await websocket.recv()
            self.check_result(result)

    async def run_test(self, files):
        with self.open_asrmon_file(self.asrmon_filename()) as self.am:
            try:
                print("Connecting to MQTT broker")
                self.mqtt_connect()
                for f in files:
                    # open wav file and get channes, sample rate, etc.
                    await self.send_audio(f)
            finally:
                print('Disconnecting...')
                self.mqtt_disconnect()


async def main(args):
    if len(args) < 2:
        sys.stderr.write('Usage: %s <config.yaml> audio_file(s)\n' % args[0])
        sys.exit(1)

    if args[0] == "-p":
        print(sd.query_devices())
        return

    config = None
    with open(args[0], 'r') as f:
        config = yaml.safe_load(f)

    vms = VoskMicroServer(config)

    logging.basicConfig(level=logging.INFO)
    await vms.run_test(args[1:])

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
