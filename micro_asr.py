#!/usr/bin/env python3

import sys
import asyncio
import websockets
import logging
import sounddevice as sd
import yaml
import wave
import resampy
import numpy as np

sample_rate=0
asr_sample_rate=16000

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def resample(audio):
    if sample_rate != asr_sample_rate:
        nparr = np.frombuffer(audio, dtype=np.int16)
        upsampled = resampy.resample(nparr, sample_rate, asr_sample_rate)
        return upsampled.tobytes()
    else:
        return audio

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

async def run_test():
    with sd.RawInputStream(samplerate=sample_rate, blocksize = 4000,
                           device=config['device'], dtype='int16',
                           channels=config['channels'], callback=callback) as device:

        async with websockets.connect(config['uri']) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % (asr_sample_rate))

            while True:
                data = await audio_queue.get()
                #print(data)
                data = resample(data)
                await websocket.send(data)
                print (await websocket.recv())

            await websocket.send('{"eof" : 1}')
            print (await websocket.recv())

async def main(args):

    global config
    global sample_rate
    global loop
    global audio_queue

    if len(args) != 1:
        sys.stderr.write('Usage: example.py <config.yaml>\n')
        sys.exit(1)

    if args[0] == "-p":
        print(sd.query_devices())
        return

    config = None
    with open(args[0], 'r') as f:
        config = yaml.safe_load(f)
    sample_rate = config['sample_rate']

    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue()

    logging.basicConfig(level=logging.INFO)
    await run_test()

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
