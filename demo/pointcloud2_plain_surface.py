#!/usr/bin/env python3
import rospy
import tf
import sensor_msgs.point_cloud2 as pc2
from sensor_msgs.msg import PointCloud2, PointCloud
from geometry_msgs.msg import Point32
from std_msgs.msg import Header
import open3d as o3d
import numpy as np
from scipy.spatial import ConvexHull

class PointCloudTransformer:
    def __init__(self):
        self.pointcloud2_sub = rospy.Subscriber("/camera/depth/color/points", PointCloud2, self.callback_pcl2, queue_size=1)
        self.transformed_cloud_pub = rospy.Publisher("/transformed_cloud", PointCloud, queue_size=1)
        self.plane_cloud_pub = rospy.Publisher("/plain_surface", PointCloud, queue_size=1)
        self.selected_area_pub = rospy.Publisher("/selected_area", PointCloud, queue_size=1)
        self.pcl2_cloud = None
        self.listener = tf.TransformListener(True, rospy.Duration(10.0))
        rospy.loginfo('Publishing transformed PointCloud. Use RViz to visualize')

    def callback_pcl2(self, msg):
        self.pcl2_cloud = msg

    def pcl_transformer(self):
        temp_cloud = PointCloud()
        temp_cloud.header = self.pcl2_cloud.header
        for data in pc2.read_points(self.pcl2_cloud, skip_nans=True):
            temp_cloud.points.append(Point32(data[0], data[1], data[2]))

        transformed_cloud = self.transform_pointcloud(temp_cloud)
        self.transformed_cloud_pub.publish(transformed_cloud)

    def transform_pointcloud(self, msg):
        while not rospy.is_shutdown():
            try:
                new_cloud = self.listener.transformPointCloud("base_link", msg)
                return new_cloud
                if new_cloud:
                    break
            except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                pass

    def plane_segmentation(self):
        points = []
        for data in pc2.read_points(self.pcl2_cloud, field_names=("x", "y", "z"), skip_nans=True):
            points.append([data[0], data[1], data[2]])

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        plane_model, inliers = pcd.segment_plane(distance_threshold=0.01, ransac_n=3, num_iterations=500)

        if len(inliers) == 0:
            rospy.loginfo("Could not find any plane in the point cloud.")
            return

        inlier_cloud = pcd.select_by_index(inliers)
        inlier_points = np.asarray(inlier_cloud.points)

        plane_cloud = PointCloud()
        plane_cloud.header = self.pcl2_cloud.header
        for point in inlier_points:
            plane_cloud.points.append(Point32(point[0], point[1], point[2]))

        # Calculate the convex hull of the inlier points
        hull = ConvexHull(inlier_points[:, :2])  # Use only x and y for 2D convex hull

        # Get the vertices of the convex hull
        hull_points = inlier_points[hull.vertices]

        # Find the largest inscribed rectangle (simplified approach)
        min_x = np.min(hull_points[:, 0])
        max_x = np.max(hull_points[:, 0])
        min_y = np.min(hull_points[:, 1])
        max_y = np.max(hull_points[:, 1])

        rectangle_width = max_x - min_x
        rectangle_height = max_y - min_y

        # Print the size of the rectangle
        rospy.loginfo(f"Rectangle width: {rectangle_width}, height: {rectangle_height}")

        # Calculate the center of the rectangle
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Select points near the center of the rectangle
        center_tolerance = 0.1  # Adjust this value as needed
        center_points = [p for p in inlier_points if 
                         (center_x - center_tolerance <= p[0] <= center_x + center_tolerance) and 
                         (center_y - center_tolerance <= p[1] <= center_y + center_tolerance)]

        if len(center_points) == 0:
            rospy.loginfo("No points found near the center of the rectangle.")
            return

        # Calculate the height (z-coordinate range) of the center points
        center_points = np.array(center_points)
        min_z = np.min(center_points[:, 2])
        max_z = np.max(center_points[:, 2])
        height = max_z - min_z

        # Print the height of the center point cloud
        rospy.loginfo(f"Height of the center point cloud: {height}")

        # Create a PointCloud message for the selected area
        selected_area_cloud = PointCloud()
        selected_area_cloud.header = self.pcl2_cloud.header
        for point in center_points:
            selected_area_cloud.points.append(Point32(point[0], point[1], point[2]))

        # Publish the selected area point cloud
        self.selected_area_pub.publish(selected_area_cloud)
        rospy.loginfo("Published selected area point cloud.")

        # Publish the plane cloud
        self.plane_cloud_pub.publish(plane_cloud)
        rospy.loginfo("Published segmented plane point cloud.")

if __name__ == "__main__":
    rospy.init_node('pointcloud_transformer', anonymous=True)
    PCT = PointCloudTransformer()
    rate = rospy.Rate(1)
    rospy.sleep(1)

    while not rospy.is_shutdown():
        if PCT.pcl2_cloud is not None:
            PCT.pcl_transformer()
            PCT.plane_segmentation()
        rate.sleep()
