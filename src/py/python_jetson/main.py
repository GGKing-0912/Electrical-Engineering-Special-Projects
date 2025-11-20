import time
import keyboard
import math
import numpy as np

from wifi import start_stream, update_json, get_arduino_data
from pid import pidControl, findLookaheadPoint, purePursuit
from utils import processData
import serial_utils
from plot_utils import updatePlot

lat0, lng0 = 25.011029, 121.539077
base_station_gps = (100, 100)

target_speed = 30.0
stop_moving = False
stopping_distance = 50.0
no_sensor_data = False

path = [
    [
        259.263,
        136.923
    ],
    [
        255.833,
        140.597
    ],
    [
        252.303,
        144.27
    ],
    [
        248.873,
        147.944
    ],
    [
        245.342,
        151.617
    ],
    [
        241.912,
        155.291
    ],
    [
        238.482,
        158.964
    ],
    [
        234.951,
        162.638
    ],
    [
        231.521,
        166.423
    ],
    [
        227.99,
        170.096
    ],
    [
        224.56,
        173.77
    ],
    [
        221.03,
        177.443
    ],
    [
        217.6,
        181.117
    ],
    [
        214.069,
        184.79
    ],
    [
        210.639,
        188.464
    ],
    [
        207.108,
        192.137
    ],
    [
        203.678,
        195.922
    ],
    [
        200.248,
        199.596
    ],
    [
        196.717,
        203.269
    ],
    [
        193.287,
        206.943
    ],
    [
        189.757,
        210.616
    ],
    [
        193.388,
        214.067
    ],
    [
        197.02,
        217.518
    ],
    [
        200.753,
        221.081
    ],
    [
        204.384,
        224.531
    ],
    [
        208.016,
        227.982
    ],
    [
        211.648,
        231.433
    ],
    [
        215.279,
        234.884
    ],
    [
        218.911,
        238.335
    ],
    [
        222.543,
        241.897
    ],
    [
        226.174,
        245.348
    ],
    [
        229.907,
        248.799
    ],
    [
        233.539,
        252.25
    ],
    [
        237.17,
        255.701
    ],
    [
        233.539,
        259.486
    ],
    [
        230.008,
        263.271
    ],
    [
        226.477,
        267.055
    ],
    [
        222.845,
        270.84
    ],
    [
        219.315,
        274.625
    ],
    [
        215.784,
        278.41
    ],
    [
        212.152,
        282.306
    ]
]
path = np.array(path)

lookahead_dist, wheelbase = 2.0, 1.0

def main():
    global target_speed, stop_moving, stopping_distance, no_sensor_data, path, lookahead_dist, wheelbase

    ffmpeg_proc, sock_json = start_stream()
    serial_utils.init_serial(portA='COM6', portB='COM4', baudrate=9600)

    serial_utils.start_sensor_thread()

    last_index = 0

    b_pressed = [False for _ in range(10)]
    
    mode = input("Semi / Fully Automatic? (0/1): ")
    print("========== Press 0 to leave ==========")
    
    running = True

    while running:
        if serial_utils.action_down:
            for i in range(10):
                if keyboard.is_pressed(str(i)):
                    if not b_pressed[i]:
                        b_pressed[i] = True
                        if i == 0:
                            serial_utils.send_command("pid," + str(-200) + ",ec," + str(0))

                            try:
                                ffmpeg_proc.terminate()
                            except Exception as e:
                                print("FFmpeg terminate error:", e)
                            try:
                                sock_json.close()
                            except Exception as e:
                                print("Socket close error:", e)
                            
                            serial_utils.stop_sensor_thread()

                            running = False
                            
                            break

                        elif i == 1:
                            if mode == "0":
                                serial_utils.send_command("pid," + str(20) + ",ec," + str(0))
                        elif i == 2:
                            if mode == "0":
                                serial_utils.send_command("pid," + str(-20) + ",ec," + str(0))
                        elif i == 3:
                            if mode == "0":
                                serial_utils.send_command("pid," + str(0) + ",ec," + str(10))
                        elif i == 4:
                            if mode == "0":
                                serial_utils.send_command("pid," + str(0) + ",ec," + str(-10))
                        elif i == 8:
                            target_speed += 5
                            print("========== target_speed:", target_speed, "==========")
                        elif i == 9:
                            target_speed -= 5
                            print("========== target_speed:", target_speed, "==========")
                else:
                    b_pressed[i] = False
            
            if not running:
                break

            # Get Arduino Data (GPS Error)
            arduino_data = get_arduino_data()
            if arduino_data is None:
                arduino_data = [base_station_gps[0], base_station_gps[1]]
                print("========== Can not get GPS error message ==========")
            gps_error = [float(arduino_data[0]) - base_station_gps[0], float(arduino_data[1]) - base_station_gps[1]]

            # Get Sensor Data
            data_processed = processData(serial_utils.sensor_data, (lat0, lng0), gps_error)
            
            if data_processed:
                no_sensor_data = False
                update_json(data_processed)

                # Ingnore Abnormal RPS
                if data_processed["hall"]["rps_avg"] > 100:
                    print("========== Ingnore Abnormal RPS: ", data_processed["hall"]["rps_avg"], "==========")
                    continue
                
                updatePlot(data_processed["hall"]["rps_avg"])
                for outer_key, inner_dict in data_processed.items():
                    print("    ", outer_key, end=": \n")
                    for key, value in inner_dict.items():
                        print(f"        {key}: {value}")
                print()
                
                if not stop_moving:
                    # Check Stopping Distance
                    if any(v < stopping_distance for v in data_processed["hr-04"].values()):
                        print("========== Stop Moving ==========")
                        serial_utils.send_command("pid," + str(-200) + ",ec," + str(0))
                        stop_moving = True

                    if stop_moving:
                        continue

                else:
                    if all(value > stopping_distance for value in data_processed["hr-04"].values()):
                        print("========== All Clear, Resume Moving ==========")
                        stop_moving = False
                    else:
                        continue

                if not stop_moving:
                    if mode == "1":
                        # PID Control
                        pid_output = pidControl(target_speed=target_speed, current_speed=data_processed["hall"]["rps_avg"])

                        # Pure Pursuit
                        last_index, (tx, ty) = findLookaheadPoint(
                            path=path, 
                            position=(data_processed["gps"]["x"], data_processed["gps"]["y"]), 
                            lookahead_dist=lookahead_dist, 
                            last_index=last_index
                        )
                        ec_output = purePursuit(
                            position=(data_processed["gps"]["x"], data_processed["gps"]["y"]), 
                            yaw=math.radians(data_processed["campass"]["degree"]),
                            lookahead_point=(tx, ty), 
                            lookahead_dist=lookahead_dist, 
                            wheelbase=wheelbase
                        )
                        delta, alpha = ec_output
                        delta_deg = math.degrees(delta)

                        print(f"Get Command => pid: {int(pid_output)}, ec: {int(delta_deg)}")
                        
                        # pid_output = 0
                        delta_deg = 0
                        
                        # Send Command to Arduino
                        serial_utils.send_command("pid," + str(int(pid_output)) + ",ec," + str(int(delta_deg)))
            
            else:
                print("========== No Sensor Data ==========")
                if not no_sensor_data:
                    serial_utils.send_command("pid," + str(-200) + ",ec," + str(0))
                    print("========== Stop Moving ==========")
                    no_sensor_data = True
                continue
        else:
            while True:
                if serial_utils.getDownSignal() == True:
                    print("========== Get Down Signal => Next Step ==========")
                    serial_utils.action_down = True
                    break
                time.sleep(0.05)
        time.sleep(0.05)
    print("========== ALL STOP ==========")

if __name__ == "__main__":
    main()