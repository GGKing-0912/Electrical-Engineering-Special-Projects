import subprocess
import socket
import json
import time
import threading
import serial_utils

VIDEO_IP = '192.168.50.110'   # receiver IP
VIDEO_PORT = 5000           # video port
JSON_PORT = 5001            # json port
ARDUINO_UDP_PORT = 4210     # arduino udp port

# ===== FFmpeg for jetson nano=====
# ffmpeg_cmd = [
#     'ffmpeg',
#     '-f', 'v4l2',
#     '-i', '/dev/video0',
#     '-c:v', 'libx264',
#     '-preset', 'ultrafast',
#     '-tune', 'zerolatency',
#     '-f', 'mpegts',
#     f'udp://{VIDEO_IP}:{VIDEO_PORT}'
# ]

# ===== FFmpeg for windows pc=====
ffmpeg_cmd = [
    'ffmpeg',
    '-f', 'dshow',
    '-i', 'video=Brio 100',
    '-c:v', 'libx264',
    '-preset', 'ultrafast',
    '-tune', 'zerolatency',
    '-f', 'mpegts',
    f'udp://{VIDEO_IP}:{VIDEO_PORT}'
]

json_data = None
json_lock = threading.Lock()
arduino_data = None
arduino_lock = threading.Lock()

# ===== UDP socket for JSON (send) =====
sock_json = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ===== UDP socket for Arduino (receive) =====
sock_arduino = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_arduino.bind(("0.0.0.0", ARDUINO_UDP_PORT))

def start_stream():
    ffmpeg_proc = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    threading.Thread(target=send_json, daemon=True).start()
    threading.Thread(target=receive_arduino, daemon=True).start()
    return ffmpeg_proc, sock_json

def send_json():
    global json_data
    # frame_id = 0
    while True:
        # with json_lock:
        # frame_id += 1
        # data = {
        #     "timestamp": 1, 
        #     "lat": 2, 
        #     "lng": 3
        # }
        message = json.dumps(json_data).encode('utf-8')
        sock_json.sendto(message, (VIDEO_IP, JSON_PORT))
        time.sleep(1/30)

def update_json(data):
    global json_data
    # with json_lock:
    json_data = data

def receive_arduino():
    global arduino_data
    while True:
        arduino_data, _ = sock_arduino.recvfrom(1024)
        arduino_data = arduino_data.decode('utf-8', errors='ignore').strip().split(",")
        time.sleep(1/10)

def get_arduino_data():
    global arduino_data
    with arduino_lock:
        return arduino_data