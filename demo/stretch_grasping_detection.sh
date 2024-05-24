#!/bin/bash

source ~/python-envs/lstm/bin/activate
source ~/catkin_ws/devel/setup.bash
rosrun stretch_demos stretch_grasping_detection.py
