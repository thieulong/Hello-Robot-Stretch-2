#!/usr/bin/env python3

import rospy
import time
from std_msgs.msg import Bool, Float32

class StretchBehavior:
    def __init__(self):
        rospy.init_node('stretch_behavior')

        rospy.Subscriber("/lift_object", Bool, self.handle_lift_object)
        rospy.Subscriber("/release_object", Bool, self.handle_release_object)

        self.lift_object_pub = rospy.Publisher("/lift_object", Bool, queue_size=1)
        self.release_object_pub = rospy.Publisher("/release_object", Bool, queue_size=1)

        self.lift_pub = rospy.Publisher("/move_lift", Float32, queue_size=1)
        self.arm_pub = rospy.Publisher("/move_arm", Float32, queue_size=1)

    def handle_lift_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to lift object.")
            self.lift_pub.publish(Float32(1.1))
            self.arm_pub.publish(Float32(0.0))
            rospy.loginfo("Object lifted!")

    def handle_release_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to release object.")
            self.lift_pub.publish(Float32(0.8))
            time.sleep(5)
            self.arm_pub.publish(Float32(0.25))
            rospy.loginfo("Object released!")

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    controller = StretchBehavior()
    try:
        controller.run()
    except rospy.ROSInterruptException:
        pass

