## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2015-2017 Intel Corporation. All Rights Reserved.

###############################################
##      Open CV and Numpy integration        ##
###############################################

import pyrealsense2 as rs
import numpy as np
import cv2
from scipy.ndimage import label, find_objects

# Define the margin for ignoring NaN regions near the corners
margin = 20
nan_tolerant = 20
crop_percentage = 0.1  # 10% crop on each side

# Step 1: Define Flat Area Search Function
def flat_area_search(depth_image):

    # Convert the depth image to float to handle NaN values
    depth_image = depth_image.astype(float)

    # Replace 0s with NaN
    depth_image[depth_image == 0] = np.nan

    # Step 2: Define Flat Region Detection
    def is_flat_surface(depth_image, x, y, threshold=1):
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

    # Step 3: Detect Flat Regions
    flat_surface_mask = np.zeros_like(depth_image, dtype=bool)
    for y in range(depth_image.shape[0]):
        for x in range(depth_image.shape[1]):
            if is_flat_surface(depth_image, x, y):
                flat_surface_mask[y, x] = True

    # Step 4: Label All Detected Flat Regions
    labeled_array, num_features = label(flat_surface_mask)

    # Step 5: Find the Largest Region
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

    # Process the largest region
    if largest_region is not None:
        y1, x1 = largest_region[0].start, largest_region[1].start
        y2, x2 = largest_region[0].stop, largest_region[1].stop

        # Crop the left and right sides by the specified percentage
        crop_width = int((x2 - x1) * crop_percentage)
        x1 += crop_width
        x2 -= crop_width

        # Count the number of NaN values in the largest region
        largest_region_array = depth_image[y1:y2, x1:x2]
        nan_count = np.isnan(largest_region_array).sum()

        # Count the total number of values in the largest region
        total_values = largest_region_array.size

        # Calculate the percentage of NaN values in the largest region
        nan_percentage = (nan_count / total_values) * 100

        # Decide whether to select the region based on the NaN percentage
        if nan_percentage <= 10:
            # Step 6: Detect NaN Regions within the Largest Region
            nan_mask = np.isnan(largest_region_array)
            labeled_nan_array, num_nan_features = label(nan_mask)

            valid_nan_regions = 0
            for nan_region_slice in find_objects(labeled_nan_array):
                nan_region_shape = (nan_region_slice[0].stop - nan_region_slice[0].start, nan_region_slice[1].stop - nan_region_slice[1].start)
                ny1, nx1 = nan_region_slice[0].start, nan_region_slice[1].start
                ny2, nx2 = nan_region_slice[0].stop, nan_region_slice[1].stop

                # Ignore NaN regions with width or height < 10 and near corners
                if nan_region_shape[0] >= nan_tolerant and nan_region_shape[1] >= nan_tolerant:
                    if not ((ny1 < margin and nx1 < margin) or (ny1 < margin and nx2 > largest_region_array.shape[1] - margin) or
                            (ny2 > largest_region_array.shape[0] - margin and nx1 < margin) or (ny2 > largest_region_array.shape[0] - margin and nx2 > largest_region_array.shape[1] - margin)):
                        valid_nan_regions += 1

            # Check if there are any valid NaN regions
            if valid_nan_regions == 0:
                # Calculate the average value in the selected region
                average_value = np.nanmean(largest_region_array)
                
                # Calculate the middle point's depth value and index
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

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()

# Get device product line for setting a supporting resolution
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

# Start streaming
pipeline.start(config)

try:
    while True:
        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        if not depth_frame:
            continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        depth_image = cv2.rotate(depth_image, cv2.ROTATE_90_CLOCKWISE)

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        # Use flat_area_search to find the flat area
        result = flat_area_search(depth_image)
        if result:
            y1, x1 = result["start_index"]
            y2, x2 = result["end_index"]
            middle_y, middle_x = result["middle_point_index"]

            # Draw rectangle around the flat region
            cv2.rectangle(depth_colormap, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # Draw a small circle at the middle point
            cv2.circle(depth_colormap, (middle_x, middle_y), 5, (0, 255, 0), -1)

            # Print the results
            print(f"Average value in the selected region: {result['average_value']:.2f}")
            print(f"Selected region start index: {result['start_index']}")
            print(f"Selected region end index: {result['end_index']}")
            print(f"Middle point depth value: {result['middle_point_value']:.2f}")
            print(f"Middle point index: {result['middle_point_index']}")

        # Display the depth colormap
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', depth_colormap)

        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break

finally:
    # Stop streaming
    pipeline.stop()
