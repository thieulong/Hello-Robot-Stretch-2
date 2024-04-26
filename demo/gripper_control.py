#!/usr/bin/env python3

import rospy
from std_msgs.msg import Bool, Float32
import stretch_body.robot
import stretch_body.arm

class StretchLiftController:
    def __init__(self):
        rospy.init_node('stretch_lift_controller')
        
        self.robot = stretch_body.robot.Robot()
        self.arm = stretch_body.arm.Arm()
        self.arm.motor.disable_sync_mode()

        if not self.robot.start_up():
            rospy.logerr("Failed to initialize Stretch Body")
        if not self.arm.startup():
            rospy.logerr("Failed to initialize Stretch Arm")

        rospy.Subscriber("/lift_object", Bool, self.handle_lift_object)
        rospy.Subscriber("/release_object", Bool, self.handle_release_object)

        rospy.Subscriber("/move_lift", Float32, self.handle_move_lift)
        rospy.Subscriber("/move_arm", Float32, self.handle_move_arm)

        self.lift_pub = rospy.Publisher("/move_lift", Float32, queue_size=1)
        self.arm_pub = rospy.Publisher("/move_arm", Float32, queue_size=1)

    def handle_lift_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to lift object.")
            self.lift_pub.publish(Float32(1.0))
            rospy.loginfo("Object lifted!")

    def handle_release_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to release object.")
            self.lift_pub.publish(Float32(0.7))
            self.arm_pub.publish(Float32(0.35))

    def handle_move_lift(self, data):
        rospy.loginfo(f"Received command to move lift to position: {data.data}")
        self.robot.lift.move_to(data.data) 
        self.robot.push_command()

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
