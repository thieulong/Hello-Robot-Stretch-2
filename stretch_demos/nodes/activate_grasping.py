#!/usr/bin/env python3

import rospy
from std_msgs.msg import Bool
from std_srvs.srv import Trigger, TriggerRequest

class GraspObjectController:
    def __init__(self):
        rospy.init_node('grasp_object_controller')
        
        # Define the subscriber to the /start_grasp_object topic
        self.subscriber = rospy.Subscriber('/start_grasp_action', Bool, self.callback_start_grasp)
        self.object_in_gripper_pub = rospy.Publisher("/object_in_gripper", Bool, queue_size=1)
        # Wait for the /grasp_object/trigger_grasp_object service to be available
        rospy.loginfo("Waiting for /grasp_object/trigger_grasp_object service...")
        rospy.wait_for_service('/grasp_object/trigger_grasp_object')
        self.grasp_object_service = rospy.ServiceProxy('/grasp_object/trigger_grasp_object', Trigger)
        rospy.loginfo("Connected to /grasp_object/trigger_grasp_object service.")

    def callback_start_grasp(self, msg):
        # Check if the received message is True
        if msg.data:
            rospy.loginfo("Received signal to start grasping.")
            try:
                # Call the /grasp_object/trigger_grasp_object service
                response = self.grasp_object_service(TriggerRequest())
                if response.success:
                    rospy.loginfo("Grasping operation succeeded: %s", response.message)
                    self.object_in_gripper_pub.publish(True)
                else:
                    rospy.loginfo("Grasping operation failed: %s", response.message)
                    self.object_in_gripper_pub.publish(False)
            except rospy.ServiceException as e:
                rospy.logerr("Service call failed: %s", e)
        else:
            rospy.loginfo("Received signal to stop or do not grasp.")

if __name__ == '__main__':
    try:
        grasp_object_controller = GraspObjectController()
        rospy.spin()  # Keep the node running until interrupted
    except rospy.ROSInterruptException:
        pass
