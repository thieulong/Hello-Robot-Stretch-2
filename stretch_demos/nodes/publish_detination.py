#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Pose
from std_msgs.msg import String

class DestinationPublisher:
    def __init__(self):
        rospy.init_node('destination_publisher')
        
        self.pub = rospy.Publisher('/destination', Pose, queue_size=10)
        self.sub = rospy.Subscriber('/stretch/status', String, self.status_callback)
        
        # Define the Pose messages for "point" and "home"
        self.point_pose = Pose()
        self.home_pose = Pose()

    def status_callback(self, msg):
        if msg.data == "point":
            rospy.loginfo("Received 'point' status, publishing to /destination")
            self.pub.publish(self.point_pose)
        elif msg.data == "home":
            rospy.loginfo("Received 'home' status, publishing to /destination")
            self.pub.publish(self.home_pose)
    
    def run(self):
        rospy.spin()

if __name__ == '__main__':
    try:
        dp = DestinationPublisher()
        dp.run()
    except rospy.ROSInterruptException:
        pass
