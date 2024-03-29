from __future__ import annotations
import math
import numpy as np
import csv
import sys

from typing import Any, Iterable, Tuple
from matplotlib import pyplot as plt
from numpy import ndarray
from pandas import read_csv
from scipy.interpolate import CubicSpline


def process_path_planner_csv(file: str, conversion_factor: float) -> tuple[
    Any, list[float | Any], list[float | Any], Any]:
    data = read_csv(file)
    t = data['timeSeconds'].tolist()
    x = data[' xPositionMeters'].tolist()
    y = data[' yPositionMeters'].tolist()

    heading = data[' holonomicRotationDegrees'].tolist()

    x_offset = x[0]
    y_offset = y[0]
    heading_offset = heading[0]

    x = [(position - x_offset) * -conversion_factor for position in x]
    y = [(position - y_offset) * conversion_factor for position in y]

    # for position in heading:
    #     appended_item = 0
    #     if position < 0:
    #         appended_item = position - heading_offset
    #     else:
    #         appended_item = heading_offset + position
    #     heading_filtered.append(math.radians(appended_item))

    heading_filtered = [math.radians((position - heading_offset)) for position in heading]

    return t, x, y, heading_filtered


def generate_cubic_spline_trajectory(t: list[float | Any], x_points: list[float | Any], y_points: list[float | Any],
                                     heading_points) -> \
        Tuple[CubicSpline, CubicSpline, CubicSpline]:
    x_curve = CubicSpline(t, x_points)
    y_curve = CubicSpline(t, y_points)
    heading_curve = CubicSpline(t, heading_points)
    return x_curve, y_curve, heading_curve


def remove_repeating_times(t: list[float | Any]) -> list[float | Any]:
    last_time = t[0]
    for index, time in enumerate(t):
        if index == 0:
            continue
        if time == last_time:
            t[index] += 1E-15
            print('expanding time for ' + str(time) + ' at index ' + str(index) + ' to become ' + str(t[index]))
        last_time = time
    return t


def evaluate_splines(linear_eval_space: np.ndarray, x_curve: CubicSpline,
                     y_curve: CubicSpline, heading_curve: CubicSpline) -> ndarray | Iterable | int | float:
    return x_curve(linear_eval_space), y_curve(linear_eval_space), heading_curve(linear_eval_space)


def calculate_total_spline_distance(x_eval: ndarray, y_eval: ndarray) -> int:
    integral = 0
    lastX = 0
    lastY = 0
    for x, y in zip(x_eval, y_eval):
        integral += (math.sqrt(((x - lastX) ** 2) + ((y - lastY) ** 2)))
        lastX = x
        lastY = y
    return integral


def export_path_csv(linear_eval_space: ndarray, x_eval: ndarray, y_eval: ndarray, theta: ndarray, export_file: str):
    with open(export_file, "w", newline='') as file:
        csv_writer = csv.writer(file)
        for i in range(0, len(x_eval)):
            csv_writer.writerow([x_eval[i], y_eval[i], theta[i]])
        file.flush()
        file.close()


def calculate_speeds(x_velocities: ndarray, y_velocities: ndarray) -> list[float]:
    speeds = []
    for x_velocity, y_velocity in zip(x_velocities, y_velocities):
        speeds.append(math.hypot(x_velocity, y_velocity))
    return speeds


def display_charts(linear_eval_space: ndarray, x_eval: ndarray, y_eval: ndarray, heading: ndarray, speeds: ndarray):
    figure, axis = plt.subplots(3, 1)
    axis[0].plot(x_eval, y_eval)
    axis[0].set_title("actual path")
    axis[1].plot(linear_eval_space, heading)
    axis[1].set_title("heading")
    axis[2].plot(linear_eval_space, speeds)
    axis[2].set_title("velocity")
    plt.show()


if __name__ == '__main__':
    args = sys.argv[1:]

    input_file_path = 'input.csv' if len(args) < 1 else args[0]
    output_file_name = 'export_path.csv' if len(args) < 2 else args[1]

    meters_to_inches = 39.3700787402

    t, x, y, heading = process_path_planner_csv(input_file_path, meters_to_inches)

    t = remove_repeating_times(t)

    y_spline, x_spline, heading_spline = generate_cubic_spline_trajectory(t, x, y, heading)

    linear_eval_space = np.linspace(0, t[-1], int(t[-1] / .02))
    x_eval, y_eval, heading_eval = evaluate_splines(linear_eval_space, x_spline, y_spline, heading_spline)

    speeds = calculate_speeds(x_spline.derivative(1)(linear_eval_space), y_spline.derivative(1)(linear_eval_space))

    print(calculate_total_spline_distance(x_eval, y_eval))

    export_path_csv(linear_eval_space, x_eval, y_eval, heading_eval, "blue_"+output_file_name)
    export_path_csv(linear_eval_space, -x_eval, y_eval, -heading_eval, "red_"+output_file_name)
    display_charts(linear_eval_space, -x_eval, y_eval, -heading_eval, speeds)

