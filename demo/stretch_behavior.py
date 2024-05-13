#!/usr/bin/env python3

import rospy
import time
from std_msgs.msg import Bool, Float32
import stretch_body.robot

class StretchBehavior:
    def __init__(self):
        rospy.init_node('stretch_behavior')
        self.robot = stretch_body.robot.Robot()

        if not self.robot.startup():
            rospy.logerr("Failed to initialize Stretch Lift")

        rospy.Subscriber("/lift_object", Bool, self.handle_lift_object)
        rospy.Subscriber("/release_object", Bool, self.handle_release_object)
        rospy.Subscriber("/give_object", Bool, self.handle_give_object)

        self.lift_object_pub = rospy.Publisher("/lift_object", Bool, queue_size=1)
        self.release_object_pub = rospy.Publisher("/release_object", Bool, queue_size=1)

        self.lift_pub = rospy.Publisher("/move_lift", Float32, queue_size=1)
        self.arm_pub = rospy.Publisher("/move_arm", Float32, queue_size=1)
        # self.wrist_pub = rospy.Publisher("/move_wrist", Float32, queue_size=1)
        # self.gripper_pub = rospy.Publisher("/move_gripper", Float32, queue_size=1)

    def handle_lift_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to lift object.")
            self.robot.end_of_arm.move_to('stretch_gripper', -20.0)
            self.lift_pub.publish(Float32(1.05))
            self.arm_pub.publish(Float32(0.0))
            self.robot.end_of_arm.move_to('wrist_yaw', 3.1)
            rospy.loginfo("Object lifted!")

    def handle_release_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to release object.")
            self.lift_pub.publish(Float32(0.8))
            time.sleep(3)
            self.arm_pub.publish(Float32(0.25))
            self.robot.end_of_arm.move_to('wrist_yaw', -0.1)
            time.sleep(3)
            self.robot.end_of_arm.move_to('stretch_gripper', 20.0)
            rospy.loginfo("Object released!")

    def handle_give_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to release object.")
            self.lift_pub.publish(Float32(1.05))
            time.sleep(10)
            self.robot.end_of_arm.move_to('wrist_yaw', -0.1)
            self.arm_pub.publish(Float32(0.1))
            rospy.loginfo("Handing object out!")
            time.sleep(5)
            self.robot.end_of_arm.move_to('stretch_gripper', 20.0)
            rospy.loginfo("Object given!")

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    controller = StretchBehavior()
    try:
        controller.run()
    except rospy.ROSInterruptException:
        pass

