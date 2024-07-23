#!/usr/bin/env python3

import rospy
import time
from std_msgs.msg import Bool, Float32
import stretch_body.robot
import stretch_body.head

class StretchBehavior:
    def __init__(self):
        rospy.init_node('stretch_behavior')
        self.robot = stretch_body.robot.Robot()
        self.head = stretch_body.head.Head()

        if not self.robot.startup():
            rospy.logwarn("Failed to initialize Stretch Body")

        if not self.head.startup():
            rospy.logwarn("Failed to initialize Stretch Head")

        rospy.Subscriber("/home_robot", Bool, self.handle_home_robot)
        rospy.Subscriber("/release_object", Bool, self.handle_release_object)
        rospy.Subscriber("/give_object", Bool, self.handle_give_object)
        rospy.Subscriber("/grasp_detect", Bool, self.handle_grasp_detect)

        self.lift_object_pub = rospy.Publisher("/lift_object", Bool, queue_size=1)
        self.release_object_pub = rospy.Publisher("/release_object", Bool, queue_size=1)

        self.lift_pub = rospy.Publisher("/move_lift", Float32, queue_size=1)
        self.arm_pub = rospy.Publisher("/move_arm", Float32, queue_size=1)

        self.home_robot_pub = rospy.Publisher("/home_robot", Bool, queue_size=1)
        
        # self.wrist_pub = rospy.Publisher("/move_wrist", Float32, queue_size=1)
        # self.gripper_pub = rospy.Publisher("/move_gripper", Float32, queue_size=1)

    def handle_home_robot(self, data):
        if data.data:
            rospy.loginfo("Received signal to home robot.")
            self.arm_pub.publish(Float32(0.0))
            time.sleep(1)
            self.robot.end_of_arm.move_to('wrist_yaw', 3.1)
            self.robot.end_of_arm.move_to('stretch_gripper', -10.0)
            time.sleep(1)
            self.lift_pub.publish(Float32(0.25))
            time.sleep(3)
            rospy.loginfo("Stretch homed successfully!")

    def handle_release_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to release object.")
            self.lift_pub.publish(Float32(0.75))
            time.sleep(5)
            self.robot.end_of_arm.move_to('wrist_yaw', -0.1)
            time.sleep(1.5)
            self.arm_pub.publish(Float32(0.25))
            time.sleep(2)
            self.robot.end_of_arm.move_to('stretch_gripper', 50.0)
            rospy.loginfo("Object released! Retracting the arm ...")
            time.sleep(1)
            self.lift_pub.publish(Float32(0.85))
            time.sleep(1)
            self.arm_pub.publish(Float32(0.0))
            time.sleep(1.5)
            self.robot.end_of_arm.move_to('wrist_yaw', 3.1)
            self.lift_pub.publish(Float32(0.25))
            self.robot.end_of_arm.move_to('stretch_gripper', -10.0)
            rospy.loginfo("Arm retracted, robot stowed!")

    def handle_give_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to release object.")
            self.lift_pub.publish(Float32(0.85))
            time.sleep(1)
            self.robot.end_of_arm.move_to('wrist_yaw', 2.1)
            # self.robot.head.pose('wheels')
            self.robot.head.move_to('head_tilt', -1.3)
            time.sleep(1)
            rospy.loginfo("Handing object out!")

    def handle_grasp_detect(self, data):
        if data.data:
            self.robot.end_of_arm.move_to('stretch_gripper', 50.0)
            time.sleep(1)
            self.robot.head.pose('ahead')
            rospy.loginfo("Object given!")
            self.home_robot_pub.publish(True)
        else: 
            self.robot.end_of_arm.move_to('stretch_gripper', -10.0)

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    controller = StretchBehavior()
    try:
        controller.run()
    except rospy.ROSInterruptException:
        pass


