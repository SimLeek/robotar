"""
Avatar Networking Interface

Usage:
    ani <network> <motors> [--motor_pins=<mpins>] [--speaker=<spk>] [--speaker_channels=<spk_chan>] [--mic=<mic>] [--mic_channels=<mic_chan>] [--camera=<cam>] [--camera_resolution=<res>]
    ani -h | --help
    ani --version

Options:
    <network>                        The network config to use (adhoc, wifi, localhost)
    <motors>                        The motor system to use (debug, rpi)
    --motor_pins=<mpins>            The motor pin specs. [default: 24,50;25,50;8,50;7,50;12,50;16,50;20,50;21,50]
    --speaker=<spk>                 The speaker to use. Use `python3 -m sounddevice` to query
    --speaker_channels=<spk_chan>   The number of speaker channels. [default: 1]
    --mic=<mic>                     The microphone to use. Use `python3 -m sounddevice` to query
    --mic_channels=<mic_chan>       The number of microphone channels. [default: 1]
    --camera=<cam>                  The v4l2 camera to use. [default: /dev/video0]
    --camera_resolution=<res>       The v4l2 camera resolution. [default: 320x240]
"""

import asyncio
import zmq
import zmq.asyncio
from robonet.receive_callbacks import receive_objs
from docopt import docopt
from robotar.receive_speaker import play_speaker_async, fft_setter
from robotar.transmit_camera import transmit_cam_async
from robotar.transmit_mic import transmit_mic_async
from typing import Dict, Any
import threading

async def udp_loop(ctx, local_ip, client_ip, args):
    motors = args['<motors>']
    motor_pins = args['--motor_pins']
    camera = args['--camera']
    camera_resolution = args['--camera_resolution']
    speaker = args['--speaker']
    speaker_channels = int(args['--speaker_channels'])
    mic = args['--mic']
    mic_channels = int(args['--mic_channels'])

    mpins = [p.split(',') for p in motor_pins.split(';')]
    mpins = [(int(x), int(y)) for x,y in mpins]

    if motors == 'rpi':
        from robotar.pi_motor_handling import get_motor_handling
        motor_handling = get_motor_handling(mpins)
    elif motors == 'debug':
        from robotar.fake_motor_handling import get_display_motor_handling
        motor_handling = get_display_motor_handling()
    else:
        raise ValueError(f"Unknown Motor Type: {motors}")

    res = [int(r) for r in camera_resolution.split('x')]

    radio_lock = threading.Lock()

    unicast_radio = ctx.socket(zmq.RADIO)
    unicast_radio.setsockopt(zmq.LINGER, 0)
    unicast_radio.setsockopt(zmq.CONFLATE, 1)
    unicast_dish = ctx.socket(zmq.DISH)
    unicast_dish.setsockopt(zmq.LINGER, 0)
    unicast_dish.setsockopt(zmq.CONFLATE, 1)
    unicast_dish.rcvtimeo = 1000

    unicast_dish.bind(f"udp://{local_ip}:9999")
    unicast_dish.join("direct")
    unicast_radio.connect(f"udp://{client_ip}:9998")

    await asyncio.gather(
        transmit_cam_async(radio_lock, unicast_radio, device=camera, width=res[0], height=res[1]),
        transmit_mic_async(radio_lock, unicast_radio, device=mic, channels=mic_channels),
        play_speaker_async(device=speaker, channels=speaker_channels),
        receive_objs({'AudioBuffer': fft_setter, 'TensorBuffer': motor_handling})(unicast_radio, unicast_dish)
    )

    unicast_radio.close()
    unicast_dish.close()


async def main(args: Dict[str, Any]):
    ctx = zmq.Context.instance()

    network = args['<network>']

    if network == 'localhost':
        local_ip = other_ip = '127.0.0.1'
        await udp_loop(ctx, local_ip, other_ip, args)
    elif network in ['wifi', 'adhoc']:
        from robonet.util import get_local_ip, client_udp_discovery
        local_ip = get_local_ip()
        other_ip = client_udp_discovery(ctx, local_ip)
        if network == 'adhoc':
            from robonet.util import get_connection_info, switch_connections
            from robonet.adhoc_pair.client import lazy_pirate_recv_con_info, connect_hotspot
            wifi_obj = lazy_pirate_recv_con_info(ctx, other_ip)  # receive our new adhoc network info from the server

            devices, current_connection = get_connection_info()
            try:
                connect_hotspot(wifi_obj, devices)
                await udp_loop(ctx, wifi_obj.client_ip, wifi_obj.server_ip, args)

            finally:
                switch_connections(wifi_obj.ssid, current_connection)
                ctx.term()
        else:
            await udp_loop(ctx, local_ip, other_ip, args)
    else:
        raise ValueError(f"Unknown Network Type: {network}")


if __name__ == "__main__":
    args = docopt(__doc__, version='Avatar Networking Interface 0.1')

    asyncio.run(main(args))
