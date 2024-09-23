#!/bin/bash

source ~/python-envs/lstm/bin/activate
source ~/catkin_ws/devel/setup.bash
rosrun stretch_demos grasp_detection.py
