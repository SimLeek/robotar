import asyncio

import numpy as np
import sounddevice as sd
from scipy import fft

latest_fft = None
fft_lock = asyncio.Lock()


async def play_speaker_async(sample_rate=44800, channels=1, sends_per_sec=24, device=None):
    blocksize = sample_rate // sends_per_sec
    global latest_fft, fft_lock

    def receive_speaker_callback(outdata, frames, time, status):
        outdata[:] = 0  # Set to silent when no data comes in

        # Pull the latest FFT data and set output
        global latest_fft
        async with fft_lock:
            if latest_fft is not None:
                y = fft.irfft(latest_fft, axis=0)

                # Ensure the output array is the correct size
                outdata[:] = np.real(y[:frames]).reshape(-1, 1).astype(np.float32)
                latest_fft = None  # Clear after use

    with sd.OutputStream(samplerate=sample_rate, channels=channels, blocksize=blocksize,
                         callback=receive_speaker_callback, device=device):
        print("Playing dish audio...")
        while True:
            await asyncio.sleep(0)  # Allow async event loop to run


def fft_setter(audio_buffer):
    global latest_fft, fft_lock
    async with fft_lock:
        latest_fft = audio_buffer.fft_data
