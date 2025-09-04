import serial
import time
import threading
import tkinter as tk
from tkinter import ttk
obstacle_detected = threading.Event()
# 建立 Serial 物件，參數視你的 Arduino COM 口而定
# Windows 可能是 COM3, COM4, Mac/Linux 是 /dev/ttyUSB0
# 設定兩塊 Arduino 的 COM port
COM_PORTS = {
    'A': 'COM3',  # 請改成你實際接 Arduino A 的 Port
    'B': 'COM5',  # Arduino B 的 Port
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

def send_command(ser, cmd):
    ser.write(cmd.encode())
    print(f"送出指令: {cmd}")
    timeout = 0
    while timeout < 5:
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"Arduino 回傳: {response}")
            if response == "DONE":
                return True
        time.sleep(1)
        timeout += 1
    print("錯誤: Arduino 無回應")
    return False

# 自動模式邏輯
def auto_mode():
    print("🚗 進入自動模式中... (偵測中)")
    # 1. 油門馬達正轉
    send_command(arduinos['A'], '3')
    time.sleep(3)

    # 2. 檢查是否有障礙物
    if obstacle_detected.is_set():
        print("⚠️ 偵測到障礙物！")
        send_command(arduinos['A'], '4')  # 油門反轉
        send_command(arduinos['A'], '5')  # 煞車正轉

        # 等待障礙物離開
        print("⏸️ 等待障礙物離開...")
        while obstacle_detected.is_set():
            time.sleep(0.5)
        print("✅ 障礙物已離開，恢復行程")

    # 3. 油門馬達反轉
    send_command(arduinos['A'], '4')
    # 4. 電動缸正轉
    send_command(arduinos['A'], '1')

print("""
控制選單：
1. 電動缸正轉1次
2. 電動缸反轉1次
3. 油門馬達正轉1次
4. 油門馬達反轉1次
5. 煞車馬達正轉1次
6. 煞車馬達反轉1次
7. 自動模式
輸入對應數字執行，輸入 q 離開
""")

try:
    while True:
        cmd = input("輸入指令: ")
        if cmd == 'q':
            break
        elif cmd in ['1', '2', '3', '4', '5', '6']:
            send_command(arduinos['A'], cmd)
        elif cmd == '7':
            auto_mode()
        else:
            print("請輸入 1~7 或 q")
except KeyboardInterrupt:
    print("強制離開")
finally:
    for ser in arduinos.values():
        ser.close()