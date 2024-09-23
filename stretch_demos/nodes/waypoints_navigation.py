#!/usr/bin/env python3

import rospy
import tf
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, Pose, PoseStamped, Point, Quaternion, Pose
from std_msgs.msg import Float32MultiArray, String, Bool
from tf.transformations import euler_from_quaternion, quaternion_from_euler
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Trigger, TriggerRequest
import math
import numpy

class StretchNavigation:
    def __init__(self):
        rospy.init_node('waypoints_navigation', anonymous=True)

        self.velocity_publisher = rospy.Publisher('/stretch/cmd_vel', Twist, queue_size=10)
        self.mode_publisher = rospy.Publisher('/stretch/handover_mode', String, queue_size=10)

        self.switch_to_navigation_service = rospy.ServiceProxy('/switch_to_navigation_mode', Trigger)
        self.switch_to_position_service = rospy.ServiceProxy('/switch_to_position_mode', Trigger)
        rospy.wait_for_service('/switch_to_navigation_mode')
        rospy.wait_for_service('/switch_to_position_mode')
        
        self.select_handover_subscriber = rospy.Subscriber('/select_handover', String, self.select_handover)
        self.odom_subscriber = rospy.Subscriber('/odom', Odometry, self.update_odometry_pose)
        self.goal_subscriber = rospy.Subscriber('/destination', Pose, self.move_to_goal)
        self.lidar_subscriber = rospy.Subscriber('/scan_filtered', LaserScan, self.lidar_callback)
        self.navigation_subscriber = rospy.Subscriber('/finish_navigation', Bool, self.navigation_callback)

        self.rate = rospy.Rate(10)

        self.width = 1
        self.extent = self.width / 2.0

        self.odom_x = 0.0
        self.odom_y = 0.0
        self.odom_yaw = 0.0
        self.global_x = 0.0
        self.global_y = 0.0
        self.global_yaw = 0.0

        self.tf_listener = tf.TransformListener()

        self.linear_tolerance = 0.5
        self.angular_tolerance = 0.035

        # self.stop_distance = 0.5
        self.stop_distance = 0.2
        self.front_distance = 0

        self.finish_navigation = False

        self.mode = None

    def switch_to_navigation_mode(self):
        try:
            rospy.loginfo("Waypoint - Switching to navigation mode")
            response = self.switch_to_navigation_service(TriggerRequest())
            if response.success:
                rospy.loginfo("Waypoint - Stretch switched to navigation mode")
            else:
                rospy.logerr("Waypoint - Failed to switch to navigation mode: %s" % response.message)
        except rospy.ServiceException as e:
            rospy.logerr("Waypoint - Failed to switch to navigation mode: %s" % e)
        
    def switch_to_position_mode(self):
        try:
            rospy.loginfo("Waypoint - Switching to position mode")
            response = self.switch_to_position_service(TriggerRequest())
            if response.success:
                rospy.loginfo("Waypoint - Stretch switched to position mode")
            else:
                rospy.logerr("Waypoint - Failed to switch to position mode: %s" % response.message)
        except rospy.ServiceException as e:
            rospy.logerr("Waypoint - Failed to switch to position mode: %s" % e)

    def select_handover(self, msg):
        if msg.data not in ["home", "direct", "indirect"]:
            rospy.logerr("The selected handover mode is unavailable.Handover mode must be home, direct or indirect")
        else:
            self.mode = msg.data
            rospy.loginfo(f"Received handover type: {self.mode}")

    def update_odometry_pose(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation

        self.odom_x = position.x
        self.odom_y = position.y

        quaternion = (orientation.x, orientation.y, orientation.z, orientation.w)
        _, _, self.odom_yaw = euler_from_quaternion(quaternion)

        # rospy.loginfo(f"Odometry pose: {self.odom_x:.3f}, {self.odom_y:.3f}")
        # rospy.loginfo(f"Odometry yaw: {self.odom_yaw:.3f}")

        self.update_global_pose()

    def update_global_pose(self):

        odom_pose = PoseStamped()
        odom_pose.header.frame_id = "odom"
        odom_pose.pose = Pose(
            position=Point(self.odom_x, self.odom_y, 0.0),
            orientation=Quaternion(*quaternion_from_euler(0, 0, self.odom_yaw))
        )

        try:
            global_pose = self.tf_listener.transformPose("map", odom_pose)
            self.global_x = global_pose.pose.position.x
            self.global_y = global_pose.pose.position.y
            _, _, self.global_yaw = euler_from_quaternion(
                (global_pose.pose.orientation.x, global_pose.pose.orientation.y,
                 global_pose.pose.orientation.z, global_pose.pose.orientation.w)
            )

            # rospy.loginfo(f"Global pose: {self.global_x:.3f}, {self.global_y:.3f}")
            # rospy.loginfo(f"Global yaw: {self.global_yaw:.3f}")
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            rospy.logwarn("TF lookup failed")

    def lidar_callback(self, msg):
        angles = numpy.linspace(msg.angle_min, msg.angle_max, len(msg.ranges))
        all_points = [r if (not math.isnan(r)) else numpy.inf for r in msg.ranges]
        front_points = [r * math.sin(theta) if (theta < -2.5 or theta > 2.5) else numpy.inf for r,theta in zip(msg.ranges, angles)]
        front_ranges = [r if abs(y) < self.extent else numpy.inf for r,y in zip(msg.ranges, front_points)]
        # min_front = min(front_ranges)
        error = min(front_ranges) - self.stop_distance

        self.front_distance = error
        # rospy.loginfo(f"Front min distance: {self.front_distance}")

    def navigation_callback(self, msg):
        if msg.data:
            self.finish_navigation = True
        else:
            self.finish_navigation = False

    def move_to_goal(self, goal):

        goal_x = goal.position.x
        goal_y = goal.position.y
        goal_z = goal.orientation.z
        goal_w = goal.orientation.w

        goal_quaternion = (0.0, 0.0, goal_z, goal_w)
        _, _, goal_yaw = tf.transformations.euler_from_quaternion(goal_quaternion)

        rospy.loginfo(f"Received goal: x = {goal_x:.3f}, y = {goal_y:.3f}, z = {goal_z:.3f}, w = {goal_w:.3f}")
        rospy.loginfo(f"Goal yaw: {goal_yaw:.3f}")

        # Calculate the goal angle to the position
        goal_angle = math.atan2(goal_y - self.global_y, goal_x - self.global_x)
        rospy.loginfo(f"Goal angle: {goal_angle:.3f}")

        # Compute the initial angle error and normalize it
        angle_error = self.normalize_angle(goal_angle - self.global_yaw)
        rospy.loginfo(f"Initial angle error: {angle_error:.3f}")

        if self.mode == "indirect": 
            self.linear_tolerance = 0.45
        elif self.mode == "direct":
            self.linear_tolerance = 0.45
        else:
            self.linear_tolerance = 0.45

        self.switch_to_navigation_mode()

        # Turn towards the goal angle
        while abs(angle_error) >= self.angular_tolerance:
            self.update_global_pose()
            velocity_msg = Twist()
            angular_speed = 0.5 * angle_error  # Proportional control

            # Ensure minimum angular speed to avoid getting stuck
            # if abs(angular_speed) < 0.075:
            #     angular_speed = 0.075 if angle_error > 0 else -0.075
            
            velocity_msg.angular.z = angular_speed
            self.velocity_publisher.publish(velocity_msg)

            # Update angle error
            self.update_global_pose()
            angle_error = self.normalize_angle(goal_angle - self.global_yaw)
            rospy.loginfo(f"Angle error: {angle_error:.3f}")
            self.rate.sleep()

        # Stop the robot after aligning
        velocity_msg = Twist()
        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

        # Move towards the goal position
        while math.sqrt(pow((goal_x - self.global_x), 2) + pow((goal_y - self.global_y), 2)) >= self.linear_tolerance:
            distance_error = math.sqrt(pow((goal_x - self.global_x), 2) + pow((goal_y - self.global_y), 2))
            self.update_global_pose()
            velocity_msg = Twist()

            # if self.front_distance < 0:
            #     rospy.logwarn("Detected obstacle in movement path!")
            #     velocity_msg.linear.x = 0
            # elif self.front_distance > 0:
            velocity_msg.linear.x = 0.15  # Constant linear speed

            velocity_msg.angular.z = 0
            self.velocity_publisher.publish(velocity_msg)

            self.update_global_pose()
            distance_error = math.sqrt(pow((goal_x - self.global_x), 2) + pow((goal_y - self.global_y), 2))
            rospy.loginfo(f"Distance error: {distance_error:.3f}")
            self.rate.sleep()

        velocity_msg = Twist()
        velocity_msg.linear.x = 0
        self.velocity_publisher.publish(velocity_msg)

        # Final orientation alignment
        yaw_error = self.normalize_angle(goal_yaw - self.global_yaw)
        while abs(yaw_error) >= self.angular_tolerance:
            self.update_global_pose()
            velocity_msg = Twist()
            angular_speed = 0.5 * yaw_error  # Proportional control

            # Ensure minimum angular speed
            # if abs(angular_speed) < 0.075:
            #     angular_speed = 0.075 if yaw_error > 0 else -0.075
            
            velocity_msg.angular.z = angular_speed
            self.velocity_publisher.publish(velocity_msg)

            # Update angle error
            self.update_global_pose()
            yaw_error = self.normalize_angle(goal_yaw - self.global_yaw)
            rospy.loginfo(f"Orientation error: {yaw_error:.3f}")
            self.rate.sleep()

        velocity_msg = Twist()
        velocity_msg.angular.z = 0
        self.velocity_publisher.publish(velocity_msg)

        rospy.sleep(1)
        rospy.loginfo(f"Finished Navigation: {self.finish_navigation}")

        if self.finish_navigation == True:
            # rospy.sleep(0.5)
            # self.switch_to_position_mode()
            self.mode_publisher.publish(self.mode)
            rospy.loginfo(f"Published handover mode: {self.mode}")

    def normalize_angle(self, angle):
        """Normalize an angle to the range [-pi, pi]."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


if __name__ == '__main__':
    try:
        x = StretchNavigation()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
