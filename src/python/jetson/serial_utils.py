import serial
import threading
import time

# "gps,1,2,campass,4,hall,6,7,8,9,hr-04,11,12,13,14,15"
ser_readA, ser_readB = None, None
sensor_data = ""
action_down = True

stop_thread_flag = False

def init_serial(portA='COM6', portB='COM4', baudrate=9600):
    global ser_readA, ser_readB
    try:
        ser_readA = serial.Serial(portA, baudrate, timeout=1)  # sensor
        ser_readB = serial.Serial(portB, baudrate, timeout=1)  # motor
        print("Serial ports initialized.")
    except Exception as e:
        print("Error initializing serial ports: ", e)
        ser_readA, ser_readB = None, None

def getSensorData():
    global ser_readA, sensor_data, stop_thread_flag

    if ser_readA is None:
        print("Serial port A not initialized")
        return

    while not stop_thread_flag:
        try:
            if ser_readA.in_waiting > 0:
                sensor_data = ser_readA.readline().decode('ascii', errors='ignore').strip()
                # print("Sensor data: ", sensor_data)

        except Exception as e:
            print("Error reading serial port A data: ", e)
            time.sleep(1)
        time.sleep(0.05)

def start_sensor_thread():
    global stop_thread_flag
    stop_thread_flag = False
    threading.Thread(target=getSensorData, daemon=True).start()

def stop_sensor_thread():
    global stop_thread_flag
    stop_thread_flag = True

def getDownSignal():
    global ser_readB
    
    if ser_readB is None:
        print("Serial port A not initialized")
        return False
    
    while ser_readB.in_waiting > 0:
        line = ser_readB.readline().decode('ascii', errors='ignore').strip().split(",")
        if line[0] == "MotorActionDown":
            print(f"========== MotorActionDown => step: {line[1]}, ec: {line[2]} ==========")
            return True
        else:
            return False
            
    time.sleep(0.1)
    return False

def send_command(cmd):
    global action_down
    if ser_readB is None:
        print("Serial port B not initialized")
        return
    try:
        ser_readB.write((cmd + "\n").encode('ascii', errors='ignore'))
        action_down = False
        print(f"========== cmd sent: {cmd} ==========")
    except Exception as e:
        print("Serial port B transmission error: ", e)
        
    time.sleep(0.05)