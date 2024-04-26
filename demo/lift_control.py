#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32
import stretch_body.lift

class StretchLiftController:
    def __init__(self):
        rospy.init_node('stretch_lift_controller')
        
        self.lift = stretch_body.lift.Lift()
        self.lift.motor.disable_sync_mode()
        
        if not self.lift.startup():
            rospy.logerr("Failed to initialize Stretch Lift")

        rospy.Subscriber("/move_lift", Float32, self.handle_move_lift)

        self.lift_pub = rospy.Publisher("/move_lift", Float32, queue_size=1)

    def handle_move_lift(self, data):
        rospy.loginfo(f"Received command to move lift to position: {data.data}")
        self.lift.move_to(data.data) 
        self.lift.push_command()
        self.lift.motor.wait_until_at_setpoint()
        
    def run(self):
        rospy.spin()

    def shutdown(self):
        self.lift.stop()

if __name__ == '__main__':
    controller = StretchLiftController()
    try:
        controller.run()
    except rospy.ROSInterruptException:
        pass
    finally:
        controller.shutdown()
