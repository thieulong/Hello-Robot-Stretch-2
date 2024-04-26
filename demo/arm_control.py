#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32
import stretch_body.arm

class StretchLiftController:
    def __init__(self):
        rospy.init_node('stretch_arm_controller')

        self.arm = stretch_body.arm.Arm()
        self.arm.motor.disable_sync_mode()

        if not self.arm.startup():
            rospy.logerr("Failed to initialize Stretch Arm")

        rospy.Subscriber("/move_arm", Float32, self.handle_move_arm)
        
        self.arm_pub = rospy.Publisher("/move_arm", Float32, queue_size=1)

    def handle_move_arm(self, data):
        rospy.loginfo(f"Received command to move arm to position: {data.data}")
        self.arm.move_to(data.data)
        self.arm.push_command()
        self.arm.motor.wait_until_at_setpoint()

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
