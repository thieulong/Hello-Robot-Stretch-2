#!/usr/bin/env python3
import rospy
import tf
import sensor_msgs.point_cloud2 as pc2
from sensor_msgs.msg import PointCloud2, PointCloud
from geometry_msgs.msg import Point32
from std_msgs.msg import Header
import open3d as o3d
import numpy as np

class PointCloudTransformer:
    """
    A class that takes in a PointCloud2 message and stores its points into a
    PointCloud message. Then that PointCloud is transformed to reference the
    'base_link' frame.
    """
    def __init__(self):
        """
        Function that initializes the subscriber, publisher, and other variables.
        :param self: The self reference.
        """
        self.pointcloud2_sub = rospy.Subscriber("/camera/depth/color/points", PointCloud2, self.callback_pcl2, queue_size=1)
        self.pointcloud_pub = rospy.Publisher("/camera_cloud", PointCloud, queue_size=1)
        self.pcl2_cloud = None
        self.listener = tf.TransformListener(True, rospy.Duration(10.0))
        rospy.loginfo('Publishing transformed PointCloud. Use RViz to visualize')

    def callback_pcl2(self, msg):
        """
        Callback function that stores the PointCloud2 message.
        :param self: The self reference.
        :param msg: The PointCloud2 message type.
        """
        self.pcl2_cloud = msg

    def pcl_transformer(self):
        """
        A function that extracts the points from the stored PointCloud2 message
        and appends those points to a PointCloud message. Then the function transforms
        the PointCloud from its the header frame id, 'camera_color_optical_frame'
        to the 'base_link' frame.
        :param self: The self reference.
        """
        temp_cloud = PointCloud()
        temp_cloud.header = self.pcl2_cloud.header
        for data in pc2.read_points(self.pcl2_cloud, skip_nans=True):
            temp_cloud.points.append(Point32(data[0], data[1], data[2]))

        transformed_cloud = self.transform_pointcloud(temp_cloud)
        self.pointcloud_pub.publish(transformed_cloud)

    def transform_pointcloud(self, msg):
        """
        Function that transforms the PointCloud2 message.
        :param self: The self reference.
        :param msg: The PointCloud message.
        :returns new_cloud: The transformed PointCloud message.
        """
        while not rospy.is_shutdown():
            try:
                new_cloud = self.listener.transformPointCloud("base_link", msg)
                return new_cloud
                if new_cloud:
                    break
            except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                pass

    def plane_segmentation(self):
        """
        Function to perform plane segmentation on the PointCloud.
        :param self: The self reference.
        """
        points = []
        for data in pc2.read_points(self.pcl2_cloud, field_names=("x", "y", "z"), skip_nans=True):
            points.append([data[0], data[1], data[2]])
        
        # Convert to Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        # Perform plane segmentation
        plane_model, inliers = pcd.segment_plane(distance_threshold=0.01, ransac_n=3, num_iterations=1000)

        if len(inliers) == 0:
            rospy.loginfo("Could not find any plane in the point cloud.")
            return

        # Extract inlier points
        inlier_cloud = pcd.select_by_index(inliers)
        inlier_points = np.asarray(inlier_cloud.points)

        # Publish the segmented plane point cloud
        plane_cloud = PointCloud()
        plane_cloud.header = self.pcl2_cloud.header
        for point in inlier_points:
            plane_cloud.points.append(Point32(point[0], point[1], point[2]))

        self.pointcloud_pub.publish(plane_cloud)
        rospy.loginfo("Published segmented plane point cloud.")

if __name__ == "__main__":
    rospy.init_node('pointcloud_transformer', anonymous=True)
    PCT = PointCloudTransformer()
    rate = rospy.Rate(1)
    rospy.sleep(1)

    while not rospy.is_shutdown():
        PCT.pcl_transformer()  # Transform point cloud
        PCT.plane_segmentation()  # Perform plane segmentation
        rate.sleep()
