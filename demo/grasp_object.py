#!/usr/bin/env python3

import rospy
from std_srvs.srv import Trigger, TriggerRequest
from std_msgs.msg import Bool

import hello_helpers.hello_misc as hm


class KeyboardTeleopNode(hm.HelloNode):

    def __init__(self):
        hm.HelloNode.__init__(self)
        self.rate = 10.0

    def activate_grasp_callback(self, msg):
        if msg.data:  # If the message is True, trigger the grasping
            rospy.loginfo('Triggering grasp object operation')
            try:
                trigger_request = TriggerRequest()
                trigger_result = self.trigger_grasp_object_service(trigger_request)
                rospy.loginfo('Grasp operation result: %s', trigger_result.message)
            except rospy.ServiceException as e:
                rospy.logerr('Service call failed: %s', e)
        else:
            rospy.loginfo('Grasp operation was deactivated or stopped (received False)')

    def main(self):
        hm.HelloNode.main(self, 'keyboard_teleop', 'keyboard_teleop', wait_for_first_pointcloud=False)

        rospy.wait_for_service('/grasp_object/trigger_grasp_object')
        rospy.loginfo('Connected to /grasp_object/trigger_grasp_object.')
        self.trigger_grasp_object_service = rospy.ServiceProxy('/grasp_object/trigger_grasp_object', Trigger)

        rospy.Subscriber('/activate_grasp_object', Bool, self.activate_grasp_callback)

        rospy.spin()


if __name__ == '__main__':
    try:
        node = KeyboardTeleopNode()
        node.main()
    except rospy.ROSInterruptException:
        pass
