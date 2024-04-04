#!/usr/bin/env python3

import rospy
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from move_base_msgs.msg import MoveBaseActionResult

class Navigator:
    def __init__(self):
        rospy.init_node('navigator_node')

        self.points = {
            "point_1": {"frame_id": "map", "position": {"x": 1.474995732307434, "y": -0.7403491735458374, "z": 0.0}, "orientation": {"x": 0.0, "y": 0.0, "z": 0.09095735556819132, "w": 0.9958547883441851}},
            "point_2": {"frame_id": "map", "position": {"x": 4.546082019805908, "y": -0.15103840827941895, "z": 0.0}, "orientation": {"x": 0.0, "y": 0.0, "z": 0.09799457266414581, "w": 0.9951869491348706}},
            "point_3": {"frame_id": "map", "position": {"x": 4.249485969543457, "y": 2.4389090538024902, "z": 0.0}, "orientation": {"x": 0.0, "y": 0.0, "z": 0.7218964864814394, "w": 0.6920010569397658}}
        }
        
        self.goal_pub = rospy.Publisher("/move_base_simple/goal", PoseStamped, queue_size=1)
        
        rospy.Subscriber("/move_base/destination", String, self.navigate_to_point)
        rospy.Subscriber("/move_base/result", MoveBaseActionResult, self.check_result)
    
    def navigate_to_point(self, data):
        point_name = data.data
        if point_name in self.points:
            point = self.points[point_name]
            goal = PoseStamped()
            goal.header.frame_id = point["frame_id"]
            goal.pose.position.x = point["position"]["x"]
            goal.pose.position.y = point["position"]["y"]
            goal.pose.position.z = point["position"]["z"]
            goal.pose.orientation.x = point["orientation"]["x"]
            goal.pose.orientation.y = point["orientation"]["y"]
            goal.pose.orientation.z = point["orientation"]["z"]
            goal.pose.orientation.w = point["orientation"]["w"]

            self.goal_pub.publish(goal)
            rospy.loginfo(f"Navigating to {point_name}...")
        else:
            rospy.logwarn("Point name not recognized.")

    def check_result(self, data):
        if data.status:
            status = data.status.text
            if status == "Goal reached.":
                rospy.loginfo("Goal reached.")
            else:
                rospy.loginfo("Goal not reached.")

if __name__ == '__main__':
    navigator = Navigator()
    rospy.spin()
