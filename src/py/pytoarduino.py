import serial
import time

ser = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2)

print("input format: pin state, for example: 1 H, or exit")

while True:
    cmd = input(">>> ").strip().upper()
    
    if cmd == "EXIT":
        break

    try:
        pin, state = cmd.split()
        if pin.isdigit() and state in ['H', 'L']:
            pin_num = int(pin)
            if 1 <= pin_num <= 8:
                message = f"{pin} {state}"
                ser.write(message.encode('utf-8'))
                print(f"send: {message}")
                response = ser.readline().decode('utf-8').strip()
                if response:
                    print("response: ", response)
            else:
                print("pin range 1~8")
        else:
            print("syntax error, please enter: 2 H or 5 L")
    except ValueError:
        print("please enter: pin state, for example: 3 H")

ser.close()
print("serial closed")
