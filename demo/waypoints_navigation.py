#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped
from std_msgs.msg import Float32MultiArray
import math
from tf.transformations import euler_from_quaternion, quaternion_from_euler

class StretchNavigation:
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

        # Tolerances
        self.linear_tolerance = 0.05  # Tolerance for distance to goal (in meters)
        self.angular_tolerance = 0.05  # Tolerance for angle to goal (in radians)

    def update_pose(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation

        # Update current position
        self.pose_x = position.x
        self.pose_y = position.y

        # Convert quaternion to yaw
        quaternion = (orientation.x, orientation.y, orientation.z, orientation.w)
        _, _, self.pose_yaw = euler_from_quaternion(quaternion)

        rospy.loginfo(f"Current pose: {self.pose_x:.3f}, {self.pose_y:.3f}")
        rospy.loginfo(f"Current yaw: {self.pose_yaw:.3f}")

    def move_to_goal(self, goal):
        # Goal coordinates (x, y) and quaternion (z, w)
        goal_x = goal.data[0]
        goal_y = goal.data[1]
        goal_z = goal.data[2]
        goal_w = goal.data[3]

        # Convert goal quaternion to yaw
        goal_quaternion = (0.0, 0.0, goal_z, goal_w)
        _, _, goal_yaw = euler_from_quaternion(goal_quaternion)

        rospy.loginfo(f"Received goal: x = {goal_x:.3f}, y = {goal_y:.3f}, z = {goal_z:.3f}, w = {goal_w:.3f}")
        rospy.loginfo(f"Goal yaw: {goal_yaw:.3f}")

        # Rotate to face the goal direction
        goal_angle = math.atan2(goal_y - self.pose_y, goal_x - self.pose_x)
        rospy.loginfo(f"Goal angle: {goal_angle:.3f}")
        while abs(goal_angle - self.pose_yaw) > self.angular_tolerance:
            velocity_msg = Twist()
            velocity_msg.angular.z = 0.1 * (goal_angle - self.pose_yaw)
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        # Stop rotation
        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

        # Move straight to the goal position
        while math.sqrt(pow((goal_x - self.pose_x), 2) + pow((goal_y - self.pose_y), 2)) > self.linear_tolerance:
            velocity_msg = Twist()
            velocity_msg.linear.x = 0.1 * math.sqrt(pow((goal_x - self.pose_x), 2) + pow((goal_y - self.pose_y), 2))
            velocity_msg.angular.z = 0
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        # Stop linear movement
        velocity_msg = Twist()
        velocity_msg.linear.x = 0
        self.velocity_publisher.publish(velocity_msg)

        # Rotate to the final orientation (goal_yaw)
        while abs(goal_yaw - self.pose_yaw) > self.angular_tolerance:
            velocity_msg.angular.z = 0.5 * (goal_yaw - self.pose_yaw)
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        # Stop angular movement
        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

if __name__ == '__main__':
    try:
        x = StretchNavigation()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
