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

    sample_rate=0
    asr_sample_rate=16000

    client=None
    loop=None
    audio_queue=None

    def __init__(self, config):
        self.config = config
        self.sample_rate = config['sample_rate']
        if 'asr_sample_rate' in config:
            self.asr_sample_rate = config['asr_sample_rate']
        if 'audio_dir' in config:
            audio_dir = config['audio_dir']

        self.loop = asyncio.get_running_loop()
        self.audio_queue = asyncio.Queue()
        self.__init_mqtt_client()

    def __init_mqtt_client(self):
        self.client = mqtt.Client()
        #self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
        #self.client.on_connect = self.__on_mqtt_connect

    def wav_filename(self):
        return self.audio_dir + 'chunk-%d.wav' % (time.time())

    def open_wave_file(self, path):
        """Opens a .wav file.
        Takes path, number of channels and sample rate.
        """
        self.wf = wave.open(path, 'wb')
        self.wf.setnchannels(self.config['channels'])
        self.wf.setsampwidth(2)
        self.wf.setframerate(self.sample_rate)
        return self.wf

    def writeframes(self, audio):
        self.wf.writeframes(audio)

    def resample(self, audio):
        if self.sample_rate != self.asr_sample_rate:
            nparr = np.frombuffer(audio, dtype=np.int16)
            upsampled = resampy.resample(nparr, self.sample_rate,
                                         self.asr_sample_rate)
            return upsampled.tobytes()
        else:
            return audio

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        self.loop.call_soon_threadsafe(self.audio_queue.put_nowait,
                                       bytes(indata))

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
            self.client.publish(self.pid + '/asrresult', str(data))

    async def run_loop(self):
        print("Opening ASR websocket %s" % (self.config['uri']))
        async with websockets.connect(self.config['uri']) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }'
                                 % (self.asr_sample_rate))
            while True:
                data = await self.audio_queue.get()
                self.writeframes(data)
                #print(data)
                data = self.resample(data)
                await websocket.send(data)
                result = await websocket.recv()
                self.check_result(result)

            await websocket.send('{"eof" : 1}')
            result = await websocket.recv()
            self.check_result(result)

    async def run_test(self):
        cb = lambda inp, frames, time, stat: self.callback(inp, frames, time, stat)
        print("Connecting to audio input %s" % (self.config['device']))
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize = 4000,
                               device=self.config['device'], dtype='int16',
                               channels=self.config['channels'],
                               callback=cb) as device:
            with self.open_wave_file(self.wav_filename()) as wf:

                print("Connecting to MQTT broker")
                try:
                    self.mqtt_connect()
                    await self.run_loop()
                finally:
                    print('Disconnecting...')
                    self.mqtt_disconnect()


async def main(args):
    if len(args) != 1:
        sys.stderr.write('Usage: %s <config.yaml>\n' % args[0])
        sys.exit(1)

    if args[0] == "-p":
        print(sd.query_devices())
        return

    config = None
    with open(args[0], 'r') as f:
        config = yaml.safe_load(f)

    vms = VoskMicroServer(config)

    logging.basicConfig(level=logging.INFO)
    await vms.run_test()

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
