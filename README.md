## Introduction

This project develops an autonomous robot system powered by ROS2, designed to operate within hospital environments and perform navigation tasks across multiple rooms in an optimized sequence.

Unlike basic navigation systems that only handle a single destination, this system addresses the more complex **multi-goal navigation** problem. This is analogous to the Traveling Salesperson Problem (TSP), where the primary objective is to minimize the total travel distance/time.

The system features a modular design, integrating essential components of a real-world robotic system: SLAM, localization, navigation, task planning, and a user interface.

------------------------------------------------------------------------

## Features

- **Multi-point Navigation:** Handles multiple destinations with an optimized sequence.
- **Route Optimization:** Utilizes a Genetic Algorithm (GA) to solve the sequence planning.
- **Realistic Cost Calculation:** Uses actual path costs from Nav2 instead of simple Euclidean (geometric) distance.
- **Automatic Re-planning:** Dynamically adjusts the plan when encountering obstacles or unreachable goals.
- **Hospital Simulation:** Includes a detailed simulation environment with complex rooms and corridors.
- **Dash board (GUI):** Supports goal selection and real-time system monitoring.

------------------------------------------------------------------------

## System Architecture

The system consists of the following core components:

- **Gazebo:** Simulation environment.
- **Cartographer:** Map construction (SLAM).
- **robot_localization (EKF):** Sensor data fusion for state estimation.
- **Nav2:** Global/local path planning and robot command execution.
- **Genetic Algorithm:** Optimization of the goal visitation order.
- **Nav Controller:** Execution coordination and re-planning logic.

------------------------------------------------------------------------

## Algorithms Used

| Component      | Method             |
|----------------|--------------------|
| SLAM           | Cartographer       |
| Localization   | EKF (Extended Kalman Filter) |
| Navigation     | Nav2               |
| Controller     | MPPI (Model Predictive Path Integral) |
| Task Planning  | A* / Genetic Algorithm |

------------------------------------------------------------------------
## Dashboard
![Dashboard UI](Screenshot%20from%202026-04-18%2007-08-54.png)
