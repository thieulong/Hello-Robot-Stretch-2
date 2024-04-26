#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32
import stretch_body.stretch_gripper

class StretchGripperController:
    def __init__(self):
        rospy.init_node('stretch_gripper_controller')

        self.gripper = stretch_body.stretch_gripper.StretchGripper()

        if not self.gripper.startup():
            rospy.logerr("Failed to initialize Stretch Gripper")

        rospy.Subscriber("/move_gripper", Float32, self.handle_move_gripper)
        
        self.arm_pub = rospy.Publisher("/move_gripper", Float32, queue_size=1)

    def handle_move_gripper(self, data):
        rospy.loginfo(f"Received command to move gripper to position: {data.data}")
        self.gripper.move_to(data.data)

    def run(self):
        rospy.spin()

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
