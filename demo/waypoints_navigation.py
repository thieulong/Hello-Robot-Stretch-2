#!/usr/bin/env python3
import rospy
import tf
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, Pose, PoseStamped, Point, Quaternion
from std_msgs.msg import Float32MultiArray
from tf.transformations import euler_from_quaternion, quaternion_from_euler
import math

class StretchNavigation:
    def __init__(self):
        rospy.init_node('waypoints_navigation', anonymous=True)

        self.velocity_publisher = rospy.Publisher('/stretch/cmd_vel', Twist, queue_size=10)
        self.odom_subscriber = rospy.Subscriber('/odom', Odometry, self.update_odometry_pose)
        self.goal_subscriber = rospy.Subscriber('/destination', Float32MultiArray, self.move_to_goal)

        self.rate = rospy.Rate(10)

        # Initialize pose variables
        self.odom_x = 0.0
        self.odom_y = 0.0
        self.odom_yaw = 0.0
        self.global_x = 0.0
        self.global_y = 0.0
        self.global_yaw = 0.0

        # TF listener setup
        self.tf_listener = tf.TransformListener()

        # Tolerances
        self.linear_tolerance = 0.05  # Tolerance for distance to goal (in meters)
        self.angular_tolerance = 0.05  # Tolerance for angle to goal (in radians)

    def update_odometry_pose(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation

        # Update current position (in odometry frame)
        self.odom_x = position.x
        self.odom_y = position.y

        # Convert quaternion to yaw
        quaternion = (orientation.x, orientation.y, orientation.z, orientation.w)
        _, _, self.odom_yaw = euler_from_quaternion(quaternion)

        rospy.loginfo(f"Odometry pose: {self.odom_x:.3f}, {self.odom_y:.3f}")
        rospy.loginfo(f"Odometry yaw: {self.odom_yaw:.3f}")

        self.update_global_pose()

    def update_global_pose(self):
        # Create a pose in the odom frame
        odom_pose = PoseStamped()
        odom_pose.header.frame_id = "odom"
        odom_pose.pose = Pose(
            position=Point(self.odom_x, self.odom_y, 0.0),
            orientation=Quaternion(*quaternion_from_euler(0, 0, self.odom_yaw))
        )

        try:
            # Transform the odom pose to the global map frame
            global_pose = self.tf_listener.transformPose("map", odom_pose)
            self.global_x = global_pose.pose.position.x
            self.global_y = global_pose.pose.position.y
            _, _, self.global_yaw = euler_from_quaternion(
                (global_pose.pose.orientation.x, global_pose.pose.orientation.y,
                 global_pose.pose.orientation.z, global_pose.pose.orientation.w)
            )

            rospy.loginfo(f"Global pose: {self.global_x:.3f}, {self.global_y:.3f}")
            rospy.loginfo(f"Global yaw: {self.global_yaw:.3f}")
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            rospy.logwarn("TF lookup failed")

    def move_to_goal(self, goal):
        goal_x = goal.data[0]
        goal_y = goal.data[1]
        goal_z = goal.data[2]
        goal_w = goal.data[3]

        goal_quaternion = (0.0, 0.0, goal_z, goal_w)
        _, _, goal_yaw = tf.transformations.euler_from_quaternion(goal_quaternion)

        rospy.loginfo(f"Received goal: x = {goal_x:.3f}, y = {goal_y:.3f}, z = {goal_z:.3f}, w = {goal_w:.3f}")
        rospy.loginfo(f"Goal yaw: {goal_yaw:.3f}")

        goal_angle = math.atan2(goal_y - self.global_y, goal_x - self.global_x)
        rospy.loginfo(f"Goal angle: {goal_angle:.3f}")
        angle_error = abs(goal_angle - self.global_yaw)
        while angle_error > self.angular_tolerance:
            rospy.loginfo(f"Angle error: {angle_error}")
            self.update_global_pose()
            velocity_msg = Twist()
            velocity_msg.angular.z = 0.1 * (goal_angle - self.global_yaw)
            self.velocity_publisher.publish(velocity_msg)
            angle_error = abs(goal_angle - self.global_yaw)
            self.rate.sleep()

        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

        while math.sqrt(pow((goal_x - self.global_x), 2) + pow((goal_y - self.global_y), 2)) > self.linear_tolerance:
            rospy.loginfo(f"Distance error: {math.sqrt(pow((goal_x - self.global_x), 2) + pow((goal_y - self.global_y), 2))}")
            self.update_global_pose()
            velocity_msg = Twist()
            velocity_msg.linear.x = 0.1 * math.sqrt(pow((goal_x - self.global_x), 2) + pow((goal_y - self.global_y), 2))
            velocity_msg.angular.z = 0
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        velocity_msg = Twist()
        velocity_msg.linear.x = 0
        self.velocity_publisher.publish(velocity_msg)

        while abs(goal_yaw - self.global_yaw) > self.angular_tolerance:
            rospy.loginfo(f"Orientation error: {abs(goal_yaw - self.global_yaw)}")
            self.update_global_pose()
            velocity_msg.angular.z = 0.1 * (goal_yaw - self.global_yaw)
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

if __name__ == '__main__':
    try:
        x = StretchNavigation()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
