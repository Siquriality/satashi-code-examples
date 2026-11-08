# Моделирует движение затухающей пружины и строит график.
import numpy as np
from scipy.integrate import solve_ivp

import matplotlib.pyplot as plt

mass = 1.0  # kg
spring_constant = 50.0  # N/m
damping_coefficient = 0.5  # Ns/m

def spring_damper_system(t, y):
    position, velocity = y
    acceleration = -(damping_coefficient / mass) * velocity - (spring_constant / mass) * position
    return [velocity, acceleration]


initial_conditions = [1.0, 0.0]


time_span = (0, 10)  
time_points = np.linspace(time_span[0], time_span[1], 500)


solution = solve_ivp(spring_damper_system, time_span, initial_conditions, t_eval=time_points)

position = solution.y[0]
velocity = solution.y[1]


plt.figure(figsize=(10, 5))
plt.plot(solution.t, position, label="Position (m)")
plt.plot(solution.t, velocity, label="Velocity (m/s)")
plt.title("Spring-Damper-Mass System")
plt.xlabel("Time (s)")
plt.ylabel("Response")
plt.legend()
plt.grid()
plt.show()


