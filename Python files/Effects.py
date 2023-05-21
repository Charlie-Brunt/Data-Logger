import numpy as np
import matplotlib.pyplot as plt


def f(t, freq):
    return np.sin(2*np.pi*freq*t)


def hard_clipping(f, threshold):
    for t in range(len(f)):
        if abs(f[t]) > threshold:
            if f[t] > 0:
                f[t] = threshold
            else:
                f[t] = -threshold
    return f


def soft_clipping(f):
    for t in range(len(f)):
        f[t] = f[t] - (f[t]**3)/3
    return f


def tremolo(f, tlist, rate):
    env = np.sin(2*np.pi*rate*tlist)
    mod = env*f
    return mod



t = np.linspace(0, 0.03, 10000)
signal = f(t, 400)
hc_signal = hard_clipping(f(t, 400), 0.5)
sc_signal = soft_clipping(f(t, 400))
t_signal = tremolo(f(t, 400), t, 50)

plt.plot(t, signal)
plt.plot(t, hc_signal)
plt.plot(t, sc_signal)
plt.plot(t, t_signal)
plt.show()
