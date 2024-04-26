#!/usr/bin/env python3

import rospy
from std_msgs.msg import Bool, Float32
import stretch_body.robot
import stretch_body.arm

class StretchLiftController:
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
            self.lift_pub.publish(Float32(1.0))
            rospy.loginfo("Object lifted!")

    def handle_release_object(self, data):
        if data.data:
            rospy.loginfo("Received signal to release object.")
            self.lift_pub.publish(Float32(0.7))
            self.arm_pub.publish(Float32(0.35))
            rospy.loginfo("Object released!")

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
