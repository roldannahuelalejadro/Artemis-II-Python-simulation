import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from IPython.display import HTML

# ===================== PARÁMETROS =====================
mu = 3.986e14
R_T = 6.371e6
r_target = 8.0e6

dt = 0.1
steps = 4000

# ===================== DINÁMICA =====================
def gravity(r):
    norm = np.linalg.norm(r)
    return -mu * r / norm**3

def simular_trayectoria():
    r = np.array([R_T, 0.0])
    v = np.array([0.0, 0.0])

    a_thrust = 10.0
    phase = 1

    trayectoria = []

    for i in range(steps):

        r_norm = np.linalg.norm(r)
        r_hat = r / r_norm

        v_radial = np.dot(v, r_hat)
        v_tan_vec = v - v_radial * r_hat
        v_tan = np.linalg.norm(v_tan_vec)

        v_circ = np.sqrt(mu / r_norm)

        if phase == 1 and r_norm > r_target:
            phase = 2

        a = gravity(r)

        if phase == 1:
            thrust_dir = r_hat
        else:
            if v_tan > 0:
                thrust_dir = v_tan_vec / v_tan
            else:
                thrust_dir = np.array([0.0, 1.0])

            if abs(v_tan - v_circ) < 10:
                thrust_dir = np.array([0.0, 0.0])

        a += a_thrust * thrust_dir

        v = v + a * dt
        r = r + v * dt

        trayectoria.append(r.copy())

    return np.array(trayectoria)

traj = simular_trayectoria()

def animar_trayectoria(traj):

    xs = traj[:,0]
    ys = traj[:,1]

    xmin, xmax = np.min(xs), np.max(xs)
    ymin, ymax = np.min(ys), np.max(ys)

    # evitar ejes degenerados
    if abs(ymax - ymin) < 1e-3:
        ymin -= 1e6
        ymax += 1e6

    if abs(xmax - xmin) < 1e-3:
        xmin -= 1e6
        xmax += 1e6

    fig, ax = plt.subplots(figsize=(6,6))

    plot_line, = ax.plot([], [], "darkcyan", alpha=0.7)
    dot, = ax.plot([], [], "ro")

    theta = np.linspace(0, 2*np.pi, 300)
    earth_x = R_T * np.cos(theta)
    earth_y = R_T * np.sin(theta)
    ax.plot(earth_x, earth_y, 'b')

    ax.set_aspect('equal')
    ax.set_xlim(xmin*1.1, xmax*1.1)
    ax.set_ylim(ymin*1.1, ymax*1.1)

    def update(i):
        plot_line.set_data(xs[:i], ys[:i])
        dot.set_data([xs[i]], [ys[i]])
        return plot_line, dot

    anim = animation.FuncAnimation(
        fig,
        update,
        frames=len(traj),
        interval=5,
        blit=False   # importante
    )

    return anim