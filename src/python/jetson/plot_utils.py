import matplotlib.pyplot as plt
from collections import deque

# 繪圖資料
time_window = 50
times = deque(maxlen=time_window)
rps_values = deque(maxlen=time_window)
plot_counter = 0

plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [], 'b-')
ax.set_ylim(0, 75)
ax.set_xlim(0, time_window)
ax.set_xlabel("Samples")
ax.set_ylabel("RPS")
ax.set_title("RPS plot")

def updatePlot(rps):
    global plot_counter

    plot_counter += 1
    times.append(plot_counter)
    rps_values.append(rps)

    line.set_xdata(times)
    line.set_ydata(rps_values)

    ax.set_xlim(plot_counter - time_window, plot_counter)
    ax.figure.canvas.draw()
    ax.figure.canvas.flush_events()