#!/usr/bin/env python3

import rospy
import stretch_body.robot
import stretch_body.end_of_arm

class StretchGripperController:
    def __init__(self):
        # Initialize the ROS node
        rospy.init_node('stretch_gripper_controller')

        # Initialize the robot
        self.robot = stretch_body.robot.Robot()
        self.robot.startup()

        # Initialize the end of arm tool
        self.eoa = stretch_body.end_of_arm.EndOfArm(self.robot)

    def open_gripper(self):
        # Open the gripper
        self.eoa.motors['stretch_gripper'].move_to(0.05)  # Adjust value as needed for your gripper
        self.eoa.push_command()

    def close_gripper(self):
        # Close the gripper
        self.eoa.motors['stretch_gripper'].move_to(0.00)  # Adjust value to close gripper completely
        self.eoa.push_command()

    def move_pitch(self, angle_radians):
        # Move the gripper pitch joint
        self.eoa.motors['wrist_pitch'].move_to(angle_radians)  # Set angle in radians
        self.eoa.push_command()

    def run(self):
        # Example usage
        while not rospy.is_shutdown():
            self.open_gripper()
            rospy.sleep(2)
            self.close_gripper()
            rospy.sleep(2)
            self.move_pitch(0.3)  # Move pitch to 0.3 radians
            rospy.sleep(2)

    def shutdown(self):
        self.robot.stop()

if __name__ == '__main__':
    controller = StretchGripperController()
    try:
        controller.run()
    except rospy.ROSInterruptException:
        pass
    finally:
        controller.shutdown()
