#!/usr/bin/env python3

import rospy
from control_msgs.msg import FollowJointTrajectoryGoal
from trajectory_msgs.msg import JointTrajectoryPoint
import hello_helpers.hello_misc as hm
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool, TriggerRequest, Trigger
import time

class ManipulatorCommand(hm.HelloNode):

  def __init__(self):
    hm.HelloNode.__init__(self)
    hm.HelloNode.main(self, 'stretch_manipulator', 'stretch_manipulator', wait_for_first_pointcloud=False)
    
    self.in_motion_pub = rospy.Publisher("/in_motion", Bool, queue_size=1)
    
    rospy.Subscriber("/grasp_detect_auto", Bool, self.handle_object_grasped_auto)
    rospy.Subscriber("/grasp_detect_manual", Bool, self.handle_object_grasped_manual)
    rospy.Subscriber("/stretch/handover_mode", String, self.set_mode)

    self.switch_to_navigation_service = rospy.ServiceProxy('/switch_to_navigation_mode', Trigger)
    self.switch_to_position_service = rospy.ServiceProxy('/switch_to_position_mode', Trigger)

    rospy.wait_for_service('/switch_to_navigation_mode')
    rospy.wait_for_service('/switch_to_position_mode')
    
    self.handover_mode = None
    self.call_grasping_service(False)
    
  def switch_to_navigation_mode(self):
    try:
        rospy.loginfo("Manipulator - Switching to navigation mode")
        response = self.switch_to_navigation_service(TriggerRequest())
        if response.success:
            rospy.loginfo("Manipulator - Stretch switched to navigation mode")
        else:
            rospy.logerr("Manipulator - Failed to switch to navigation mode: %s" % response.message)
    except rospy.ServiceException as e:
        rospy.logerr("Manipulator - Failed to switch to navigation mode: %s" % e)
    
  def switch_to_position_mode(self):
    try:
        rospy.loginfo("Manipulator - Switching to position mode")
        response = self.switch_to_position_service(TriggerRequest())
        if response.success:
            rospy.loginfo("Manipulator - Stretch switched to position mode")
        else:
            rospy.logerr("Manipulator - Failed to switch to position mode: %s" % response.message)
    except rospy.ServiceException as e:
        rospy.logerr("Manipulator - Failed to switch to position mode: %s" % e)

  def set_mode(self, msg):
    if msg.data in ["home", "direct", "indirect"]:
      self.switch_to_position_mode()
      rospy.loginfo(msg.data)
      self.handover_mode = msg.data
      rospy.sleep(0.5)
    rospy.loginfo(f"Manipulator - Mode set to: {self.handover_mode}")

    if self.handover_mode == "home":
        rospy.loginfo("Homing robot")
        self.handle_home_robot()
    if self.handover_mode == "indirect":
        rospy.loginfo("Releasing object")
        self.handle_release_object()
    if self.handover_mode == "direct":
        rospy.loginfo("Handover object")
        self.handle_handover_object()

  def call_grasping_service(self, state):
    rospy.wait_for_service('ControlGrasping')
    try:
      control_service = rospy.ServiceProxy('ControlGrasping', SetBool)
      response = control_service(state)
      rospy.loginfo(response.message)
    except rospy.ServiceException as e:
      rospy.logerr("Service call failed: %s" % e)

  def handle_home_robot(self):

    self.in_motion_pub.publish(True)
    home_point = JointTrajectoryPoint()
    home_point.time_from_start = rospy.Duration(0.000)
    home_point.positions = [0.0, 3.0, 0, 0, 0]

    trajectory_goal = FollowJointTrajectoryGoal()
    trajectory_goal.trajectory.joint_names = ['wrist_extension', 'joint_wrist_yaw', 'gripper_aperture', 'joint_head_pan', 'joint_head_tilt']
    trajectory_goal.trajectory.points = [home_point]
    trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
    trajectory_goal.trajectory.header.frame_id = 'base_link'

    self.trajectory_client.send_goal(trajectory_goal)
    rospy.loginfo('Sent home goal = {0}'.format(trajectory_goal))
    self.trajectory_client.wait_for_result()

    time.sleep(1)

    home_point = JointTrajectoryPoint()
    home_point.time_from_start = rospy.Duration(0.000)
    home_point.positions = [0.2]

    trajectory_goal = FollowJointTrajectoryGoal()
    trajectory_goal.trajectory.joint_names = ['joint_lift']
    trajectory_goal.trajectory.points = [home_point]
    trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
    trajectory_goal.trajectory.header.frame_id = 'base_link'

    self.trajectory_client.send_goal(trajectory_goal)
    rospy.loginfo('Sent home goal = {0}'.format(trajectory_goal))
    self.trajectory_client.wait_for_result()

    self.in_motion_pub.publish(False)
    self.switch_to_navigation_mode()

  def handle_release_object(self):

    self.in_motion_pub.publish(True)
    release_point = JointTrajectoryPoint()
    release_point.time_from_start = rospy.Duration(0.000)
    release_point.positions = [0.82]

    trajectory_goal = FollowJointTrajectoryGoal()
    trajectory_goal.trajectory.joint_names = ['joint_lift']
    trajectory_goal.trajectory.points = [release_point]
    trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
    trajectory_goal.trajectory.header.frame_id = 'base_link'

    self.trajectory_client.send_goal(trajectory_goal)
    rospy.loginfo('Sent release goal = {0}'.format(trajectory_goal))
    self.trajectory_client.wait_for_result()

    time.sleep(1)

    release_point = JointTrajectoryPoint()
    release_point.time_from_start = rospy.Duration(0.000)
    release_point.positions = [0.4, 1.0]

    trajectory_goal = FollowJointTrajectoryGoal()
    trajectory_goal.trajectory.joint_names = ['wrist_extension', 'joint_wrist_yaw']
    trajectory_goal.trajectory.points = [release_point]
    trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
    trajectory_goal.trajectory.header.frame_id = 'base_link'

    self.trajectory_client.send_goal(trajectory_goal)
    rospy.loginfo('Sent release goal = {0}'.format(trajectory_goal))
    self.trajectory_client.wait_for_result()

    time.sleep(1)

    release_point = JointTrajectoryPoint()
    release_point.time_from_start = rospy.Duration(0.000)
    release_point.positions = [50]

    trajectory_goal = FollowJointTrajectoryGoal()
    trajectory_goal.trajectory.joint_names = ['gripper_aperture']
    trajectory_goal.trajectory.points = [release_point]
    trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
    trajectory_goal.trajectory.header.frame_id = 'base_link'

    self.trajectory_client.send_goal(trajectory_goal)
    rospy.loginfo('Sent release goal = {0}'.format(trajectory_goal))
    self.trajectory_client.wait_for_result()
    self.handle_home_robot()

  def handle_handover_object(self):

    self.in_motion_pub.publish(True)
    release_point = JointTrajectoryPoint()
    release_point.time_from_start = rospy.Duration(0.000)
    release_point.positions = [0.9]

    trajectory_goal = FollowJointTrajectoryGoal()
    trajectory_goal.trajectory.joint_names = ['joint_lift']
    trajectory_goal.trajectory.points = [release_point]
    trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
    trajectory_goal.trajectory.header.frame_id = 'base_link'

    self.trajectory_client.send_goal(trajectory_goal)
    rospy.loginfo('Sent release goal = {0}'.format(trajectory_goal))
    self.trajectory_client.wait_for_result()

    time.sleep(1)

    release_point = JointTrajectoryPoint()
    release_point.time_from_start = rospy.Duration(0.000)
    release_point.positions = [0.3, 0.8]

    trajectory_goal = FollowJointTrajectoryGoal()
    trajectory_goal.trajectory.joint_names = ['wrist_extension', 'joint_wrist_yaw']
    trajectory_goal.trajectory.points = [release_point]
    trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
    trajectory_goal.trajectory.header.frame_id = 'base_link'

    self.trajectory_client.send_goal(trajectory_goal)
    rospy.loginfo('Sent release goal = {0}'.format(trajectory_goal))
    self.trajectory_client.wait_for_result()

    time.sleep(1)

    self.call_grasping_service(True)

  # def handle_handover_object(self):

  #   self.in_motion_pub.publish(True)
  #   handover_point = JointTrajectoryPoint()
  #   handover_point.time_from_start = rospy.Duration(0.000)
  #   handover_point.positions = [0.9, 0, 2.1, -10]

  #   trajectory_goal = FollowJointTrajectoryGoal()
  #   trajectory_goal.trajectory.joint_names = ['joint_lift', 'wrist_extension', 'joint_wrist_yaw', 'gripper_aperture']
  #   trajectory_goal.trajectory.points = [handover_point]
  #   trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
  #   trajectory_goal.trajectory.header.frame_id = 'base_link'

  #   self.trajectory_client.send_goal(trajectory_goal)
  #   rospy.loginfo('Sent handover goal = {0}'.format(trajectory_goal))
  #   self.trajectory_client.wait_for_result()

  #   time.sleep(1)

  #   handover_point = JointTrajectoryPoint()
  #   handover_point.time_from_start = rospy.Duration(0.000)
  #   handover_point.positions = [0, -1.3]

  #   trajectory_goal = FollowJointTrajectoryGoal()
  #   trajectory_goal.trajectory.joint_names = ['joint_head_pan', 'joint_head_tilt']
  #   trajectory_goal.trajectory.points = [handover_point]
  #   trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
  #   trajectory_goal.trajectory.header.frame_id = 'base_link'

  #   self.trajectory_client.send_goal(trajectory_goal)
  #   rospy.loginfo('Sent handover goal = {0}'.format(trajectory_goal))
  #   self.trajectory_client.wait_for_result()

  #   self.call_grasping_service(True)

  def handle_object_grasped_auto(self, data):

    if data.data:
      self.in_motion_pub.publish(True)
      self.call_grasping_service(False)
      handover_point = JointTrajectoryPoint()
      handover_point.time_from_start = rospy.Duration(0.000)
      handover_point.positions = [50]

      trajectory_goal = FollowJointTrajectoryGoal()
      trajectory_goal.trajectory.joint_names = ['gripper_aperture']
      trajectory_goal.trajectory.points = [handover_point]
      trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
      trajectory_goal.trajectory.header.frame_id = 'base_link'

      self.trajectory_client.send_goal(trajectory_goal)
      rospy.loginfo('Sent handover goal = {0}'.format(trajectory_goal))
      self.trajectory_client.wait_for_result()
      self.handle_home_robot()

    else:
      self.in_motion_pub.publish(True)
      handover_point = JointTrajectoryPoint()
      handover_point.time_from_start = rospy.Duration(0.000)
      handover_point.positions = [-10]

      trajectory_goal = FollowJointTrajectoryGoal()
      trajectory_goal.trajectory.joint_names = ['gripper_aperture']
      trajectory_goal.trajectory.points = [handover_point]
      trajectory_goal.trajectory.header.stamp = rospy.Time(0.0)
      trajectory_goal.trajectory.header.frame_id = 'base_link'

      self.trajectory_client.send_goal(trajectory_goal)
      rospy.loginfo('Sent handover goal = {0}'.format(trajectory_goal))
      self.trajectory_client.wait_for_result()

  def handle_object_grasped_manual(self, data):
     if data.data:
        self.in_motion_pub.publish(True)
        self.handle_home_robot()

  def main(self):
    rospy.spin()

if __name__ == '__main__':
  try:
    node = ManipulatorCommand()
    node.main()
  except KeyboardInterrupt:
    rospy.loginfo('interrupt received, so shutting down')