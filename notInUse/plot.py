import numpy as np
import matplotlib.pyplot as plt

def plot_solution(solution, maxAmper):
    time_points = []
    ampere_consumption = []
    current_ampere = 0
    print(solution)

    for i in range(0, len(solution), 7):
        _, _, _, start_time, end_time, ampere, _ = solution[i:i+7] 
        current_ampere += ampere

        # Append data points for plotting
        time_points.extend([start_time, end_time])
        ampere_consumption.extend([current_ampere, current_ampere])

    # Plot the ampere consumption over time
    plt.plot(time_points, ampere_consumption, label='Ampere Consumption')

    # Plot the maxAmper threshold line
    plt.axhline(y=maxAmper, color='r', linestyle='--', label='Max Ampere')

    # Highlight the areas where ampere consumption exceeds maxAmper
    plt.fill_between(time_points, ampere_consumption, where=[amp > maxAmper for amp in ampere_consumption],
                     color='red', alpha=0.3, label='Exceeds Max Ampere')

    plt.xlabel('Time')
    plt.ylabel('Ampere Consumption')
    plt.legend()
    plt.show()

