#!/usr/bin/env python3

import rospy
import time
from std_msgs.msg import Bool
from stretch_body.robot import Robot

class StretchLiftController:
    def __init__(self):
        rospy.init_node('stretch_lift_controller')
        
        # Initialize Stretch RE2 robot
        self.robot = Robot()
        self.robot.startup()

        # Subscribers
        rospy.Subscriber("/object_in_hand", Bool, self.handle_object_in_hand)
        rospy.Subscriber("/release_object", Bool, self.handle_release_object)

    def handle_object_in_hand(self, data):
        if data.data:
            rospy.loginfo("Received signal to lift object.")
            # Lift the lift upwards to a certain position
            self.robot.lift.move_to(0.5)  # Adjust the target position as needed
            self.robot.push_command()

    def handle_release_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to release object.")
            # Move the lift downwards to the original position
            self.robot.lift.move_to(0.0)  # Adjust the target position as needed
            self.robot.push_command()
            time.sleep(2)
            # Open the gripper after 2 seconds
            self.robot.end_of_arm.move_to('stretch_gripper', {'pos': 0.0})  # Fully open
            self.robot.push_command()

    def run(self):
        rospy.spin()

    def shutdown(self):
        self.robot.stop()

if __name__ == '__main__':
    controller = StretchLiftController()
    try:
        controller.run()
    except rospy.ROSInterruptException:
        pass
    finally:
        controller.shutdown()
