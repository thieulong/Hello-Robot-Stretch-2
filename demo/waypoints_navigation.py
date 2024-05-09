#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped
from std_msgs.msg import Float32MultiArray
import math

class TurtleController:
    def __init__(self):
        rospy.init_node('waypoints_navigation', anonymous=True)

        self.velocity_publisher = rospy.Publisher('/stretch/cmd_vel', Twist, queue_size=10)

        self.pose_subscriber = rospy.Subscriber('/amcl_pose', PoseWithCovarianceStamped, self.update_pose)
        self.goal_subscriber = rospy.Subscriber('/destination', Float32MultiArray, self.move_to_goal)
        
        self.rate = rospy.Rate(10) 

    def update_pose(self, msg):
        self.data = msg
        self.pose_x = self.data.pose.pose.position.x
        self.pose_y = self.data.pose.pose.position.y
        self.pose_z = self.data.pose.pose.orientation.z
        self.pose_w = self.data.pose.pose.orientation.w
        rospy.loginfo(f"Current pose: {self.pose_x, self.pose_y}")
        rospy.loginfo(f"Current orientation: {self.pose_z, self.pose_w}")

    def move_to_goal(self, goal):
        goal_pose = Float32MultiArray()
        goal_pose.x = goal.data[0]
        goal_pose.y = goal.data[1]
        goal_pose.z = goal.data[2]
        goal_pose.w = goal.data[4]

        rospy.loginfo(f"Receive goal: x = {goal_pose.x}, y = {goal_pose.y}, z = {goal_pose.z}, w = {goal.pose_w}")
        goal_angle = math.atan2(goal_pose.y - self.pose.y, goal_pose.x - self.pose.x)
        
        while abs(goal_angle - self.pose.z) > 0.01:
            velocity_msg = Twist()
            velocity_msg.angular.z = 2.0 * (goal_angle - self.pose.z)
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        while math.sqrt(pow((goal_pose.x - self.pose.x), 2) + pow((goal_pose.y - self.pose.y), 2)) > 0.1:
            velocity_msg = Twist()
            velocity_msg.linear.x = math.sqrt(pow((goal_pose.x - self.pose.x), 2) + pow((goal_pose.y - self.pose.y), 2))
            velocity_msg.angular.z = 0
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        velocity_msg.linear.x = 0
        self.velocity_publisher.publish(velocity_msg)

        while abs(goal_pose.z - self.pose.z) > 0.01:
            velocity_msg = Twist()
            velocity_msg.angular.z = 2.0 * (goal_pose.z - self.pose.z)
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

if __name__ == '__main__':
    try:
        x = TurtleController()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
