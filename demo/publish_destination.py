#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float32MultiArray

def publish_goal():

    rospy.init_node('destination_publisher')

    pub = rospy.Publisher('/destination', Float32MultiArray, queue_size=10)

    rospy.sleep(1)
    
    goal_msg = Float32MultiArray()

    goal_msg.data = [x, y, theta]
    
    rospy.loginfo(f"Publishing goal coordinate: {goal_msg.data}")
    
    pub.publish(goal_msg)

    rospy.sleep(1)

if __name__ == '__main__':
    try:
        publish_goal()
    except rospy.ROSInterruptException:
        pass
