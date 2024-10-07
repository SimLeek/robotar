import asyncio
import random

from robonet import camera
from robonet.buffers.buffer_handling import pack_obj
from robonet.buffers.buffer_objects import MJpegCamFrame
from robonet.util import send_burst


async def transmit_cam_async(radio_lock, radio, device='/dev/video0', width=320, height=240):
    """Async function to transmit camera MJPEG data"""
    print("transmitting cam data..")
    cam = camera.CameraPack(device=device, width=width, height=height)
    while True:
        # Send direct messages to the server
        direct_message = cam.get_packed_frame()
        direct_message = MJpegCamFrame(0, 0, direct_message)
        direct_message = pack_obj(direct_message)
        parts = []
        for i in range(0, len(direct_message), 4096):
            parts.append(direct_message[i:i + 4096])

        send_burst(radio_lock, radio, bytes([random.randint(0, 255)]), parts)

        print(f"Sent frame")
        await asyncio.sleep(0)
