import serial
import time
import threading
# 建立 Serial 物件，參數視你的 Arduino COM 口而定
# Windows 可能是 COM3, COM4, Mac/Linux 是 /dev/ttyUSB0
# 設定兩塊 Arduino 的 COM port
COM_PORTS = {
    'A': 'COM3',  # 請改成你實際接 Arduino A 的 Port
    'B': 'COM4',  # Arduino B 的 Port
}
# 儲存 Serial 物件
arduinos = {}

# 讀取資料的背景執行緒
def read_from_arduino(name, ser):
    while True:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            print(f"[來自板子{name}] {line}")
        time.sleep(0.1)

# 初始化所有序列連接
for name, port in COM_PORTS.items():
    try:
        ser = serial.Serial(port=port, baudrate=9600, timeout=1)
        time.sleep(2)
        arduinos[name] = ser
        threading.Thread(target=read_from_arduino, args=(name, ser), daemon=True).start()
        print(f"已連線至 Arduino {name} 在 {port}")
    except Exception as e:
        print(f"連線 Arduino {name} 失敗：{e}")

print("""
控制選單：
1. 電動缸 正轉
2. 電動缸 反轉
3. 步進馬達 A 正轉
4. 步進馬達 A 反轉
5. 步進馬達 B 正轉
6. 步進馬達 B 反轉
輸入對應數字執行，輸入 q 離開
""")

try:
    while True:
        cmd = input("輸入指令: ")
        if cmd == 'q':
            break
        if cmd in ['1', '2', '3', '4', '5', '6']:
            arduinos['A'].write(cmd.encode())
            print(f"已送出指令 {cmd} 給 A 板")
        else:
            print("請輸入 1~6 或 q")
except KeyboardInterrupt:
    print("強制離開")
finally:
    for ser in arduinos.values():
        ser.close()