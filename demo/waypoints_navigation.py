#!/usr/bin/env python3
import rospy
import tf
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray
import math

class StretchNavigation:
    def __init__(self):
        rospy.init_node('waypoints_navigation', anonymous=True)

        self.velocity_publisher = rospy.Publisher('/stretch/cmd_vel', Twist, queue_size=10)
        self.goal_subscriber = rospy.Subscriber('/destination', Float32MultiArray, self.move_to_goal)

        self.rate = rospy.Rate(10)

        # Initialize pose variables
        self.pose_x = 0.0
        self.pose_y = 0.0
        self.pose_yaw = 0.0

        # TF listener setup
        self.tf_listener = tf.TransformListener()

        # Tolerances
        self.linear_tolerance = 0.05  # Tolerance for distance to goal (in meters)
        self.angular_tolerance = 0.05  # Tolerance for angle to goal (in radians)

    def update_tf_pose(self):
        try:
            (trans, rot) = self.tf_listener.lookupTransform('/map', '/base_link', rospy.Time(0))
            self.pose_x, self.pose_y = trans[0], trans[1]
            _, _, self.pose_yaw = tf.transformations.euler_from_quaternion(rot)

            rospy.loginfo(f"Current pose: {self.pose_x:.3f}, {self.pose_y:.3f}")
            rospy.loginfo(f"Current yaw: {self.pose_yaw:.3f}")
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

        goal_angle = math.atan2(goal_y - self.pose_y, goal_x - self.pose_x)
        rospy.loginfo(f"Goal angle: {goal_angle:.3f}")
        angle_error = abs(goal_angle - self.pose_yaw)
        while angle_error > self.angular_tolerance:
            self.update_tf_pose()
            velocity_msg = Twist()
            velocity_msg.angular.z = 0.1 * (goal_angle - self.pose_yaw)
            self.velocity_publisher.publish(velocity_msg)
            angle_error = abs(goal_angle - self.pose_yaw)
            self.rate.sleep()

        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

        while math.sqrt(pow((goal_x - self.pose_x), 2) + pow((goal_y - self.pose_y), 2)) > self.linear_tolerance:
            self.update_tf_pose()
            velocity_msg = Twist()
            velocity_msg.linear.x = 0.1 * math.sqrt(pow((goal_x - self.pose_x), 2) + pow((goal_y - self.pose_y), 2))
            velocity_msg.angular.z = 0
            self.velocity_publisher.publish(velocity_msg)
            self.rate.sleep()

        velocity_msg = Twist()
        velocity_msg.linear.x = 0
        self.velocity_publisher.publish(velocity_msg)

        while abs(goal_yaw - self.pose_yaw) > self.angular_tolerance:
            self.update_tf_pose()
            velocity_msg.angular.z = 0.1 * (goal_yaw - self.pose_yaw)
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
