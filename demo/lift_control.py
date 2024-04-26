#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32
import stretch_body.robot

class StretchLiftController:
    def __init__(self):
        rospy.init_node('stretch_lift_controller')
        
        self.robot = stretch_body.robot.Robot()

        if not self.robot.start_up():
            rospy.logerr("Failed to initialize Stretch Body")

        rospy.Subscriber("/move_lift", Float32, self.handle_move_lift)

        self.lift_pub = rospy.Publisher("/move_lift", Float32, queue_size=1)

    def handle_move_lift(self, data):
        rospy.loginfo(f"Received command to move lift to position: {data.data}")
        self.robot.lift.move_to(data.data) 
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
