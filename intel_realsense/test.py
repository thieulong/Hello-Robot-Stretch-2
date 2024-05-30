import numpy as np
from scipy.ndimage import label, find_objects

# Define the margin for ignoring NaN regions near the corners
margin = 20

# Step 1: Load and Prepare Data
depth_image = np.loadtxt('depth-array-2.txt', dtype=int)

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
            if nan_region_shape[0] >= 10 and nan_region_shape[1] >= 10:
                if not ((ny1 < margin and nx1 < margin) or (ny1 < margin and nx2 > largest_region_array.shape[1] - margin) or
                        (ny2 > largest_region_array.shape[0] - margin and nx1 < margin) or (ny2 > largest_region_array.shape[0] - margin and nx2 > largest_region_array.shape[1] - margin)):
                    valid_nan_regions += 1

        # Check if there are any valid NaN regions
        if valid_nan_regions == 0:
            # Calculate the average value in the selected region
            average_value = np.nanmean(largest_region_array)
            print(f"Average value in the selected region: {average_value:.2f}")
            print(f"Selected region start index: ({y1}, {x1})")
            print(f"Selected region end index: ({y2}, {x2})")
            
            # Calculate and print the middle point's depth value and index
            middle_y = (y1 + y2) // 2
            middle_x = (x1 + x2) // 2
            middle_value = depth_image[middle_y, middle_x]
            print(f"Middle point depth value: {middle_value:.2f}")
            print(f"Middle point index: ({middle_y}, {middle_x})")
