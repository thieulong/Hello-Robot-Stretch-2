#!/usr/bin/env python3

import rospy
from std_srvs.srv import Trigger, TriggerResponse, TriggerRequest
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Pose

class HandoverServiceNode:
    def __init__(self):
        rospy.init_node('handover_service_node')

        # Service proxies for switching modes
        self.switch_to_navigation_service = rospy.ServiceProxy('/switch_to_navigation_mode', Trigger)
        self.switch_to_position_service = rospy.ServiceProxy('/switch_to_position_mode', Trigger)

        rospy.wait_for_service('/switch_to_navigation_mode')
        rospy.wait_for_service('/switch_to_position_mode')

        # Service servers
        self.direct_handover_service = rospy.Service('/execute_direct_handover', Trigger, self.execute_direct_handover)
        self.indirect_handover_service = rospy.Service('/execute_indirect_handover', Trigger, self.execute_indirect_handover)
        
        # Publishers
        self.pose_publisher = rospy.Publisher('/destination', Pose, queue_size=10)
        self.handover_type_publisher = rospy.Publisher('/select_handover', String, queue_size=10)
        self.navigation_publisher = rospy.Publisher('/finish_navigation', Bool, queue_size=10)
        
        # Subscribe to /in_motion
        self.in_motion_subscriber = rospy.Subscriber('/in_motion', Bool, self.in_motion_callback)

        # Initialize in_motion state
        self.in_motion = True

        rospy.loginfo("Handover Service Node Initialized")

    def switch_to_navigation_mode(self):
        try:
            rospy.loginfo("Handover - Switching to navigation mode")
            response = self.switch_to_navigation_service(TriggerRequest())
            if response.success:
                rospy.loginfo("Handover - Stretch switched to navigation mode")
            else:
                rospy.logerr("Handover - Failed to switch to navigation mode: %s" % response.message)
        except rospy.ServiceException as e:
            rospy.logerr("Handover - Failed to switch to navigation mode: %s" % e)
        
    def switch_to_position_mode(self):
        try:
            rospy.loginfo("Handover - Switching to position mode")
            response = self.switch_to_position_service(TriggerRequest())
            if response.success:
                rospy.loginfo("Handover - Stretch switched to position mode")
            else:
                rospy.logerr("Handover - Failed to switch to position mode: %s" % response.message)
        except rospy.ServiceException as e:
            rospy.logerr("Handover - Failed to switch to position mode: %s" % e)

    def execute_direct_handover(self, request):
        self.navigation_publisher.publish(False)
        rospy.loginfo("Executing Direct Handover")

        self.switch_to_navigation_mode()
        rospy.sleep(0.1)
        rospy.loginfo("Moving to 1st position")

        # Publish intermediate pose before handover
        intermediate_pose = Pose()
        intermediate_pose.position.x = 5.550155105115524
        intermediate_pose.position.y = -3.3041773408828736
        intermediate_pose.position.z = 0.0
        intermediate_pose.orientation.x = 0.0
        intermediate_pose.orientation.y = 0.0
        intermediate_pose.orientation.z = 0.027058256157831903
        intermediate_pose.orientation.w = 0.9996338583569973

        self.pose_publisher.publish(intermediate_pose)

        rospy.sleep(15)
        rospy.loginfo("Moving to 2nd position")

        # Publish initial pose and handover type
        initial_pose = Pose()
        initial_pose.position.x = 5.9411927544167815
        initial_pose.position.y = -0.47858886659256217
        initial_pose.position.z = 0.0
        initial_pose.orientation.x = 0.0
        initial_pose.orientation.y = 0.0
        initial_pose.orientation.z = 0.5932816188818617
        initial_pose.orientation.w = 0.8049949817836863

        self.pose_publisher.publish(initial_pose)
        rospy.sleep(20)

        rospy.loginfo("Destination reached")
        self.navigation_publisher.publish(True)
        # self.switch_to_position_mode()
        rospy.sleep(0.1)
        
        self.handover_type_publisher.publish("direct")
        rospy.loginfo("Published direct handover pose and method")

        # Wait for the robot to stop moving
        rospy.sleep(0.5)
        while self.in_motion:
            rospy.sleep(0.1)

        self.navigation_publisher.publish(False)
        
        # Publish intermediate pose before returning to home
        return_intermediate_pose = Pose()
        return_intermediate_pose.position.x = 4.8888635755417775
        return_intermediate_pose.position.y = -3.5316571644092623
        return_intermediate_pose.position.z = 0.0
        return_intermediate_pose.orientation.x = 0.0
        return_intermediate_pose.orientation.y = 0.0
        return_intermediate_pose.orientation.z = 0.9920823609255104
        return_intermediate_pose.orientation.w = 0.12558896902381694

        self.pose_publisher.publish(return_intermediate_pose)
        rospy.loginfo("Moving to 1st position")
        rospy.sleep(15)

        # Publish destination pose and return to home
        home_pose = Pose()
        home_pose.position.x = 3.6930874637228173
        home_pose.position.y = -2.9872666596823008
        home_pose.position.z = 0.0
        home_pose.orientation.x = 0.0
        home_pose.orientation.y = 0.0
        home_pose.orientation.z = -0.1227928271088054
        home_pose.orientation.w = 0.9924323259601266

        self.pose_publisher.publish(home_pose)
        self.navigation_publisher.publish(True)
        self.handover_type_publisher.publish("home")

        rospy.loginfo("Returned to home position after direct handover")
        return TriggerResponse(success=True, message="Direct handover executed successfully.")

    def execute_indirect_handover(self, request):
        self.navigation_publisher.publish(False)
        rospy.loginfo("Executing Indirect Handover")

        self.switch_to_navigation_mode()
        rospy.sleep(0.1)
        rospy.loginfo("Moving to 1st position")

        # Publish intermediate pose before handover
        intermediate_pose = Pose()
        intermediate_pose.position.x = 5.550155105115524
        intermediate_pose.position.y = -3.3041773408828736
        intermediate_pose.position.z = 0.0
        intermediate_pose.orientation.x = 0.0
        intermediate_pose.orientation.y = 0.0
        intermediate_pose.orientation.z = 0.027058256157831903
        intermediate_pose.orientation.w = 0.9996338583569973

        self.pose_publisher.publish(intermediate_pose)

        rospy.sleep(15)
        rospy.loginfo("Moving to 2nd position")

        # Publish initial pose and handover type
        initial_pose = Pose()
        initial_pose.position.x = 5.9411927544167815
        initial_pose.position.y = -0.47858886659256217
        initial_pose.position.z = 0.0
        initial_pose.orientation.x = 0.0
        initial_pose.orientation.y = 0.0
        initial_pose.orientation.z = 0.5932816188818617
        initial_pose.orientation.w = 0.8049949817836863

        self.pose_publisher.publish(initial_pose)
        rospy.sleep(20)

        rospy.loginfo("Destination reached")
        self.navigation_publisher.publish(True)
        # self.switch_to_position_mode()
        rospy.sleep(0.1)
        
        # self.handover_type_publisher.publish("direct")
        self.handover_type_publisher.publish("indirect")
        rospy.loginfo("Published indirect handover pose and method")

        # Wait for the robot to stop moving
        rospy.sleep(0.5)
        while self.in_motion:
            rospy.sleep(0.1)

        self.navigation_publisher.publish(False)
        
        # Publish intermediate pose before returning to home
        return_intermediate_pose = Pose()
        return_intermediate_pose.position.x = 4.8888635755417775
        return_intermediate_pose.position.y = -3.5316571644092623
        return_intermediate_pose.position.z = 0.0
        return_intermediate_pose.orientation.x = 0.0
        return_intermediate_pose.orientation.y = 0.0
        return_intermediate_pose.orientation.z = 0.9920823609255104
        return_intermediate_pose.orientation.w = 0.12558896902381694

        self.pose_publisher.publish(return_intermediate_pose)
        rospy.loginfo("Moving to home position")
        rospy.sleep(15)

        # Publish destination pose and return to home
        home_pose = Pose()
        home_pose.position.x = 3.6930874637228173
        home_pose.position.y = -2.9872666596823008
        home_pose.position.z = 0.0
        home_pose.orientation.x = 0.0
        home_pose.orientation.y = 0.0
        home_pose.orientation.z = -0.1227928271088054
        home_pose.orientation.w = 0.9924323259601266

        self.pose_publisher.publish(home_pose)
        self.navigation_publisher.publish(True)
        self.handover_type_publisher.publish("home")

        rospy.loginfo("Returned to home position after indirect handover")
        return TriggerResponse(success=True, message="Indirect handover executed successfully.")

    def in_motion_callback(self, msg):
        self.in_motion = msg.data
        rospy.loginfo("In motion status: %s", self.in_motion)

if __name__ == '__main__':
    try:
        handover_service_node = HandoverServiceNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
