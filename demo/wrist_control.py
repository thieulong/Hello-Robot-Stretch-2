#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32
import stretch_body.wrist_yaw

class StretchWristController:
    def __init__(self):
        rospy.init_node('stretch_wrist_controller')

        self.wrist_yaw = stretch_body.wrist_yaw.WristYaw()

        if not self.wrist_yaw.startup():
            rospy.logerr("Failed to initialize Stretch Wrist")

        rospy.Subscriber("/move_wrist", Float32, self.handle_move_wrist)
        
        self.wrist_pub = rospy.Publisher("/move_wrist", Float32, queue_size=1)

    def handle_move_wrist(self, data):
        rospy.loginfo(f"Received command to move wrist to position: {data.data}")
        self.wrist_yaw.move_to(data.data)

    def run(self):
        rospy.spin()

    def shutdown(self):
        self.robot.stop()

if __name__ == '__main__':
    controller = StretchWristController()
    try:
        controller.run()
    except rospy.ROSInterruptException:
        pass
    finally:
        controller.shutdown()
