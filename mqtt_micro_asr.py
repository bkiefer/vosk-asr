#!/usr/bin/env python3

import sys
import asyncio
import websockets
import logging
import yaml
import wave
import time

import resampy
import numpy as np

import json
import paho.mqtt.client as mqtt

import gstmicpipeline as gm

MAX_RECONNECTS = 40
RECONNECT_WAIT = 5  # SECONDS


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def current_milli_time():
    return round(time.time() * 1000)

class VoskMicroServer():

    def __init__(self, config):
        self.pid = "voskasr"
        self.audio_dir = "audio/"
        self.language = "de"

        self.channels = 1
        self.usedchannel = 0
        self.sample_rate = 16000
        self.asr_sample_rate = 8000

        self.config = config
        if 'asr_sample_rate' in config:
            self.asr_sample_rate = config['asr_sample_rate']
        if 'channels' in config:
            self.channels = config['channels']
        if 'use_channel' in config:
            self.usedchannel = config['use_channel']
        if 'audio_dir' in config:
            self.audio_dir = config['audio_dir']
        if 'language' in config:
            self.language = config['language']
        self.topic = self.pid + '/asrresult'
        if self.language:
            self.topic += '/' + self.language
        self.loop = asyncio.get_running_loop()
        self.audio_queue = asyncio.Queue()
        self.__init_mqtt_client()

    def __init_mqtt_client(self):
        self.client = mqtt.Client()
        # self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
        # self.client.on_connect = self.__on_mqtt_connect

    def wav_filename(self):
        return self.audio_dir + 'chunk-%d.wav' % (time.time())

    def open_wave_file(self, path):
        """Opens a .wav file.
        Takes path, number of channels and sample rate.
        """
        wf = wave.open(path, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        return wf

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

    def writeframes(self, audio):
        self.wf.writeframes(audio)

    def resample(self, audio, channels, sample_rate):
        if sample_rate == self.asr_sample_rate and channels == 1:
            self.am.writeframes(audio)
            return audio

        frame = np.frombuffer(audio, dtype=np.int16)
        if channels > 1:
            # numpy slicing:
            # take every i'th value: frame[start:stop:step]
            frame = frame[self.usedchannel::channels]
        #print(frame[:64])
        if sample_rate != self.asr_sample_rate:
            frame = resampy.resample(frame, sample_rate, self.asr_sample_rate)
            frame = frame.astype(np.int16)
        self.am.writeframes(frame)
        return frame.tobytes()

    def callback(self, indata, frames, time_block, status):
        """This is called (from a separate thread) for each audio block."""
        self.loop.call_soon_threadsafe(self.audio_queue.put_nowait,
                                       bytes(indata))

    def mqtt_connect(self):
        self.client.connect(self.config['mqtt_address'])
        self.client.loop_start()

    def mqtt_disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    # Send a result returned from the ASR to the MQTT topic
    def check_result(self, transcribe):
        data = json.loads(transcribe)
        if data and 'text' in data:
            text = data['text']
            if text != '' and text != 'einen' and text != 'bin':
                # TODO: not sure if we need this, maybe the MQTT message id is
                # enough?
                data['id'] = current_milli_time()
                print(data)
                self.client.publish(self.topic, json.dumps(data, indent=None))

    # Send audio from file to ASR
    async def send_audio(self, file):
        print("Opening ASR websocket %s" % (self.config['uri']))
        async with websockets.connect(self.config['uri']) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }'
                                 % (self.asr_sample_rate))
            wf = wave.open(file, "rb")
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            buffer_size = int(self.sample_rate * 0.2) # 0.2 seconds of audio
            while True:
                data = wf.readframes(buffer_size)
                if len(data) == 0:
                    break

                data = self.resample(data, channels, sample_rate)
                await websocket.send(data)
                #print('.', end='')
                result = await websocket.recv()
                self.check_result(result)

            await websocket.send('{"eof" : 1}')
            result = await websocket.recv()
            self.check_result(result)

    # Send audio from a collection of files to ASR
    async def send_files(self, files):
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

    async def audio_loop(self, websocket):
        await websocket.send('{ "config" : { "sample_rate" : %d } }'
                             % (self.asr_sample_rate))
        while True:
            data = await self.audio_queue.get()
            self.writeframes(data)
            #print(len(data))

            data = self.resample(data, self.channels, self.sample_rate)
            #print('<', end='', flush=True)
            await websocket.send(data)
            #print('>', end='', flush=True)
            result = await websocket.recv()
            self.check_result(result)

        await websocket.send('{"eof" : 1}')
        result = await websocket.recv()
        self.check_result(result)

    async def reconnect_loop(self):
        print("Opening ASR websocket %s" % (self.config['uri']))
        async for websocket in websockets.connect(self.config['uri']):
            #print("****************** Connected ******************")
            reconnects = 0
            try:
                await self.audio_loop(websocket)
            except websockets.ConnectionClosed:
                print('r', end='')
                reconnects += 1
                time.sleep(RECONNECT_WAIT)
                if reconnects > MAX_RECONNECTS:
                    print("MAX_RECONNECTS reached")
                    break
                else:
                    continue

    async def run_micro(self):
        cb = lambda inp, frames: self.callback(inp, frames, None, None)
        pipeline = self.config["pipeline"] if "pipeline" in self.config \
            else gm.PIPELINE
        with gm.GstreamerMicroSink(callback=cb, pipeline_spec=pipeline) as device:
            with self.open_wave_file(self.wav_filename()) as self.wf:
                with self.open_asrmon_file(self.asrmon_filename()) as self.am:
                    print("Connecting to MQTT broker")
                    try:
                        self.mqtt_connect()
                        await self.reconnect_loop()
                    finally:
                        print('Disconnecting...')
                        self.mqtt_disconnect()

async def main(args):
    #if len(args) < 1:
    #    sys.stderr.write('Usage: %s <config.yaml> [audio_file(s)]\n' % args[0])
    #    sys.exit(1)

    config = { 'mqtt_address':'localhost', 'uri':'ws://0.0.0.0:2700/' }
    if len(args) >= 1:
        with open(args[0], 'r') as f:
            config = yaml.safe_load(f)

    vms = VoskMicroServer(config)

    logging.basicConfig(level=logging.INFO)
    if len(args) > 1:
        await vms.send_files(args[1:])
    else:
        await vms.run_micro()

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
