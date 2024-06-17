#!/usr/bin/env python3
import rospy
import tf
import sensor_msgs.point_cloud2 as pc2
from sensor_msgs.msg import PointCloud2
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
        self.pointcloud_pub = rospy.Publisher("/camera_cloud", PointCloud2, queue_size=1)
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
        temp_cloud = self.pcl2_cloud  # Directly use stored message
        transformed_cloud = self.transform_pointcloud(temp_cloud)
        self.pointcloud_pub.publish(transformed_cloud)

    def transform_pointcloud(self, msg):
        """
        Function that transforms the PointCloud2 message.
        :param self: The self reference.
        :param msg: The PointCloud2 message.
        :returns new_cloud: The transformed PointCloud2 message.
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
        Function to perform plane segmentation on the PointCloud2.
        :param self: The self reference.
        """
        points = []
        for data in pc2.read_points(self.pcl2_cloud, field_names=("x", "y", "z"), skip_nans=True):
            points.append([data[0], data[1], data[2]])
        
        # Convert to Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        # Perform plane segmentation
        plane_model, inliers = pcd.segment_plane(distance_threshold=0.01, ransac_n=3, num_iterations=500)

        if len(inliers) == 0:
            rospy.loginfo("Could not find any plane in the point cloud.")
            return

        # Extract inlier points
        inlier_cloud = pcd.select_by_index(inliers)
        inlier_points = np.asarray(inlier_cloud.points)

        # Filter points with z > 0.3m
        filtered_points = inlier_points[inlier_points[:, 2] > 0.3]

        if len(filtered_points) == 0:
            rospy.loginfo("No points found with z > 0.3m in the segmented plane point cloud.")
            return

        # Create a new PointCloud2 message for the segmented plane
        header = Header()
        header.stamp = rospy.Time.now()
        header.frame_id = "base_link"  # Adjust frame ID as needed
        cloud_out = pc2.create_cloud_xyz32(header, filtered_points.tolist())

        # Publish the segmented plane point cloud
        self.pointcloud_pub.publish(cloud_out)
        rospy.loginfo("Published segmented plane point cloud with z > 0.3m.")

if __name__ == "__main__":
    rospy.init_node('pointcloud_transformer', anonymous=True)
    PCT = PointCloudTransformer()
    rate = rospy.Rate(1)
    rospy.sleep(1)

    while not rospy.is_shutdown():
        PCT.pcl_transformer()  # Transform point cloud
        PCT.plane_segmentation()  # Perform plane segmentation
        rate.sleep()
