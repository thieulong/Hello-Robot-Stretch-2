## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2015-2017 Intel Corporation. All Rights Reserved.

###############################################
##      Open CV and Numpy integration        ##
###############################################

import pyrealsense2 as rs
import numpy as np
import cv2
from scipy.ndimage import label, find_objects

margin = 10
nan_tolerant = 20
nan_threshold = 10
flat_threshold = 2
crop_percentage = 0.1  

def flat_area_search(depth_image):

    depth_image = depth_image.astype(float)
    depth_image[depth_image == 0] = np.nan

    def is_flat_surface(depth_image, x, y, threshold=flat_threshold):
        current_value = depth_image[y, x]
        if np.isnan(current_value):
            return False

        neighbors = []
        if y-1 >= 0 and not np.isnan(depth_image[y-1, x]):
            neighbors.append(depth_image[y-1, x])
        if y+1 < depth_image.shape[0] and not np.isnan(depth_image[y+1, x]):
            neighbors.append(depth_image[y+1, x])
        if x-1 >= 0 and not np.isnan(depth_image[y, x-1]):
            neighbors.append(depth_image[y, x-1])
        if x+1 < depth_image.shape[1] and not np.isnan(depth_image[y, x+1]):
            neighbors.append(depth_image[y, x+1])
        
        return all(np.abs(current_value - neighbor) <= threshold for neighbor in neighbors)

    flat_surface_mask = np.zeros_like(depth_image, dtype=bool)
    for y in range(depth_image.shape[0]):
        for x in range(depth_image.shape[1]):
            if is_flat_surface(depth_image, x, y):
                flat_surface_mask[y, x] = True

    labeled_array, num_features = label(flat_surface_mask)

    largest_region = None
    largest_region_size = 0

    for region_slice in find_objects(labeled_array):
        if region_slice is not None:
            region_height = region_slice[0].stop - region_slice[0].start
            region_width = region_slice[1].stop - region_slice[1].start
            region_size = region_height * region_width
            if region_size > largest_region_size:
                largest_region_size = region_size
                largest_region = region_slice

    if largest_region is not None:
        y1, x1 = largest_region[0].start, largest_region[1].start
        y2, x2 = largest_region[0].stop, largest_region[1].stop

        crop_width = int((x2 - x1) * crop_percentage)
        x1 += crop_width
        x2 -= crop_width

        largest_region_array = depth_image[y1:y2, x1:x2]
        nan_count = np.isnan(largest_region_array).sum()

        total_values = largest_region_array.size

        nan_percentage = (nan_count / total_values) * 100

        if nan_percentage <= nan_threshold:
            nan_mask = np.isnan(largest_region_array)
            labeled_nan_array, num_nan_features = label(nan_mask)

            valid_nan_regions = 0
            for nan_region_slice in find_objects(labeled_nan_array):
                nan_region_shape = (nan_region_slice[0].stop - nan_region_slice[0].start, nan_region_slice[1].stop - nan_region_slice[1].start)
                ny1, nx1 = nan_region_slice[0].start, nan_region_slice[1].start
                ny2, nx2 = nan_region_slice[0].stop, nan_region_slice[1].stop

                if nan_region_shape[0] >= nan_tolerant and nan_region_shape[1] >= nan_tolerant:
                    if not ((ny1 < margin and nx1 < margin) or (ny1 < margin and nx2 > largest_region_array.shape[1] - margin) or
                            (ny2 > largest_region_array.shape[0] - margin and nx1 < margin) or (ny2 > largest_region_array.shape[0] - margin and nx2 > largest_region_array.shape[1] - margin)):
                        valid_nan_regions += 1

            if valid_nan_regions == 0:
                average_value = np.nanmean(largest_region_array)

                middle_y = (y1 + y2) // 2
                middle_x = (x1 + x2) // 2
                middle_value = depth_image[middle_y, middle_x]
                
                return {
                    "average_value": average_value,
                    "start_index": (y1, x1),
                    "end_index": (y2, x2),
                    "middle_point_value": middle_value,
                    "middle_point_index": (middle_y, middle_x)
                }
    return None

pipeline = rs.pipeline()
config = rs.config()

pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()
device_product_line = str(device.get_info(rs.camera_info.product_line))

found_rgb = False
for s in device.sensors:
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The program requires Depth camera with Color sensor")
    exit(0)

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

if device_product_line == 'L500':
    config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
else:
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        if not depth_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())
        depth_image = cv2.rotate(depth_image, cv2.ROTATE_90_CLOCKWISE)

        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        result = flat_area_search(depth_image)
        if result:
            y1, x1 = result["start_index"]
            y2, x2 = result["end_index"]
            middle_y, middle_x = result["middle_point_index"]

            cv2.rectangle(depth_colormap, (x1, y1), (x2, y2), (0, 0, 255), 2)

            cv2.circle(depth_colormap, (middle_x, middle_y), 5, (0, 255, 0), -1)

            print(f"Average value in the selected region: {result['average_value']:.2f}")
            print(f"Selected region start index: {result['start_index']}")
            print(f"Selected region end index: {result['end_index']}")
            print(f"Middle point depth value: {result['middle_point_value']:.2f}")
            print(f"Middle point index: {result['middle_point_index']}")

        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', depth_colormap)

        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
