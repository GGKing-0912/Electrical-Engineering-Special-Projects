import time
import math

# PID 參數
Kp, Ki, Kd = 0.3, 0.0, 0.0
integral = 0.0
last_error = 0.0
last_time = time.time()

def pidControl(target_speed, current_speed):
    global Kp, Ki, Kd, integral, last_error, last_time

    error = target_speed - current_speed
    
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time

    integral += error * dt
    derivative = (error - last_error) / dt if dt > 0 else 0
    pid_output = Kp * error + Ki * integral + Kd * derivative
    last_error = error

    return pid_output


def findLookaheadPoint(path, position, lookahead_dist, last_index=0):
    """
    path: Nx2 array of waypoints [[x,y],...]
    position: (x,y)
    lookahead_dist: desired lookahead distance Ld
    last_index: start searching from this index (to ensure forward progress)
    returns: (index, point) where point is (x,y). If not found, returns last point.
    """
    px, py = position

    N = len(path)
    # search for the first path point whose distance along path from current pos >= lookahead_dist
    for i in range(last_index, N):
        dx = path[i,0] - px
        dy = path[i,1] - py
        if math.hypot(dx,dy) >= lookahead_dist:
            return i, (path[i, 0], path[i, 1])
        
    # fallback: return final point
    return N-1, (path[-1, 0], path[-1, 1])

def purePursuit(position, yaw, lookahead_point, lookahead_dist, wheelbase):
    """
    position: (x,y)
    yaw: heading angle (rad)
    lookahead_point: (x_ld, y_ld)
    returns: delta(rad) (steering_angle), alpha (angle to lookahead relative to heading)
    """
    px, py = position
    lx, ly = lookahead_point

    # transform lookahead point to vehicle coordinates
    dx = lx - px
    dy = ly - py

    # angle from heading to lookahead point
    local_x =  math.cos(-yaw) * dx - math.sin(-yaw) * dy  # rotate coordinates by -yaw
    local_y =  math.sin(-yaw) * dx + math.cos(-yaw) * dy

    # alpha is angle between heading and vector to lookahead
    alpha = math.atan2(local_y, local_x)

    # curvature kappa = 2*sin(alpha)/Ld
    if lookahead_dist == 0:
        return 0.0, alpha
    
    curvature = 2.0 * math.sin(alpha) / lookahead_dist

    # steering angle (bicycle): delta = atan(L * kappa)
    delta = math.atan(wheelbase * curvature)

    return delta, alpha