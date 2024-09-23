#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_srvs.srv import Empty, EmptyResponse

def set_initial_pose(req):
    pub = rospy.Publisher('/initialpose', PoseWithCovarianceStamped, queue_size=10)

    rospy.sleep(1)
    
    initial_pose = PoseWithCovarianceStamped()
    initial_pose.header.stamp = rospy.Time.now()
    initial_pose.header.frame_id = 'map'

    initial_pose.pose.pose.position.x = 3.8079967026112964
    initial_pose.pose.pose.position.y = -2.9034506326678975
    initial_pose.pose.pose.position.z = 0.0
  
    initial_pose.pose.pose.orientation.x = 0.0
    initial_pose.pose.pose.orientation.y = 0.0
    initial_pose.pose.pose.orientation.z = -0.13730452048854552
    initial_pose.pose.pose.orientation.w = 0.9905288833009417
    
    initial_pose.pose.covariance = [0.24528207360984844, -0.008683890777982484, 0.0, 0.0, 0.0, 0.0, -0.008683890777982484, 0.2453052150229933, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.06788771465558512]
    
    pub.publish(initial_pose)
    rospy.loginfo("Initial pose set to: x = {}, y = {}, z = {}, orientation: x = {}, y = {}, z = {}, w = {}".format(
        initial_pose.pose.pose.position.x,
        initial_pose.pose.pose.position.y,
        initial_pose.pose.pose.position.z,
        initial_pose.pose.pose.orientation.x,
        initial_pose.pose.pose.orientation.y,
        initial_pose.pose.pose.orientation.z,
        initial_pose.pose.pose.orientation.w))
    
    rospy.sleep(1)
    
    return EmptyResponse()

def reset_position_service():
    rospy.init_node('reset_position_service_node')
 
    service = rospy.Service('/reset_position', Empty, set_initial_pose)
    
    rospy.loginfo("Service /reset_position is ready")
    rospy.spin()

if __name__ == '__main__':
    try:
        reset_position_service()
    except rospy.ROSInterruptException:
        pass
