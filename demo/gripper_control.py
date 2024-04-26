#!/usr/bin/env python3

import rospy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class WristYawController:
    def __init__(self):
        rospy.init_node('wrist_yaw_controller')

        # Publisher to send commands to the wrist yaw joint
        self.joint_pub = rospy.Publisher('/joint_trajectory_controller/command', JointTrajectory, queue_size=10)

    def set_wrist_yaw(self, angle):
        '''
        Function to set the wrist yaw joint to a specific angle.
        :param angle: Desired angle in radians.
        '''
        # Create a JointTrajectory message
        msg = JointTrajectory()
        msg.joint_names = ['joint_wrist_yaw']

        # Create a JointTrajectoryPoint to define movement
        point = JointTrajectoryPoint()
        point.positions = [angle]
        point.time_from_start = rospy.Duration(1.0)  # Set duration for the movement

        # Assign the point to the trajectory message
        msg.points = [point]
        self.joint_pub.publish(msg)
        rospy.loginfo("Setting wrist yaw to {:.2f} radians".format(angle))

    def run(self):
        # Example: Set the wrist yaw to 0.5 radians
        rate = rospy.Rate(1)  # 1 Hz
        while not rospy.is_shutdown():
            self.set_wrist_yaw(0.5)  # Adjust this value as needed for your application
            rate.sleep()

if __name__ == '__main__':
    controller = WristYawController()
    try:
        controller.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("WristYawController node terminated.")
