import asyncio
import random

import sounddevice as sd
from robonet.buffers.buffer_handling import pack_obj
from robonet.buffers.buffer_objects import AudioBuffer
from robonet.util import send_burst
from scipy import fft


async def transmit_mic_async(radio_lock, radio, sample_rate=44800, channels=1, sends_per_sec=24, fft_size=1536, device=None):
    block_size = sample_rate // sends_per_sec

    def transmit_mic_callback(indata, frames, time, status):
        print("transmit mic callback")
        nonlocal fft_size, radio, radio_lock

        x = fft.rfft(indata, n=block_size, axis=0)

        fft_size = min(len(indata) * 2, fft_size)
        fft_transmit = x[:fft_size // 2]

        direct_message = AudioBuffer(sample_rate, sends_per_sec, fft_transmit)
        direct_message = pack_obj(direct_message)
        parts = []
        for i in range(0, len(direct_message), 4096):
            parts.append(direct_message[i:i + 4096])
        print('transmit mic burst')
        send_burst(radio_lock, radio, bytes([random.randint(0, 255)]), parts)
        print(f"Sent fft")

    with sd.InputStream(samplerate=sample_rate, channels=channels, blocksize=block_size,
                        callback=transmit_mic_callback, device=device):
        print("Transmitting mic data...")
        while True:
            await asyncio.sleep(0)  # Allow async event loop to run
