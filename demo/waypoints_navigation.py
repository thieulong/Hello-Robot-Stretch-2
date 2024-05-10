#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped
from std_msgs.msg import Float32MultiArray
import math
from tf.transformations import euler_from_quaternion, quaternion_from_euler

class WayPointsNavigation:
    def __init__(self):
        rospy.init_node('waypoints_navigation', anonymous=True)

        self.velocity_publisher = rospy.Publisher('/stretch/cmd_vel', Twist, queue_size=10)

        self.pose_subscriber = rospy.Subscriber('/amcl_pose', PoseWithCovarianceStamped, self.update_pose)
        self.goal_subscriber = rospy.Subscriber('/destination', Float32MultiArray, self.move_to_goal)

        self.rate = rospy.Rate(10)

        # Initialize pose variables
        self.pose_x = 0.0
        self.pose_y = 0.0
        self.pose_yaw = 0.0

    def update_pose(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation

        # Update current position
        self.pose_x = position.x
        self.pose_y = position.y

        # Convert quaternion to yaw
        quaternion = (orientation.x, orientation.y, orientation.z, orientation.w)
        _, _, self.pose_yaw = euler_from_quaternion(quaternion)

        rospy.loginfo(f"Current pose: {self.pose_x, self.pose_y}")
        rospy.loginfo(f"Current yaw: {self.pose_yaw}")

    def move_to_goal(self, goal):
        # Goal coordinates (x, y) and quaternion (z, w)
        goal_x = goal.data[0]
        goal_y = goal.data[1]
        goal_z = goal.data[2]
        goal_w = goal.data[3]

        # Convert goal quaternion to yaw
        goal_quaternion = (0.0, 0.0, goal_z, goal_w)
        _, _, goal_yaw = euler_from_quaternion(goal_quaternion)

        rospy.loginfo(f"Received goal: x = {goal_x}, y = {goal_y}, z = {goal_z}, w = {goal_w}")
        rospy.loginfo(f"Goal yaw: {goal_yaw}")

        # Rotate to face the goal
        goal_angle = math.atan2(goal_y - self.pose_y, goal_x - self.pose_x)
        while abs(goal_angle - self.pose_yaw) > 0.01:
            velocity_msg = Twist()
            velocity_msg.angular.z = 2.0 * (goal_angle - self.pose_yaw)
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        # Move straight to the goal position
        while math.sqrt(pow((goal_x - self.pose_x), 2) + pow((goal_y - self.pose_y), 2)) > 0.1:
            velocity_msg = Twist()
            velocity_msg.linear.x = 0.5 * math.sqrt(pow((goal_x - self.pose_x), 2) + pow((goal_y - self.pose_y), 2))
            velocity_msg.angular.z = 0
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        # Stop linear movement
        velocity_msg = Twist()
        velocity_msg.linear.x = 0
        self.velocity_publisher.publish(velocity_msg)

        # Rotate to the final orientation
        while abs(goal_yaw - self.pose_yaw) > 0.01:
            velocity_msg.angular.z = 2.0 * (goal_yaw - self.pose_yaw)
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        # Stop angular movement
        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

if __name__ == '__main__':
    try:
        x = WayPointsNavigation()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
