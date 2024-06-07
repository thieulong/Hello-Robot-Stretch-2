import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label, find_objects
from mpl_toolkits.mplot3d import Axes3D

margin = 10
nan_tolerant = 20
nan_threshold = 10
flat_threshold = 2
crop_percentage = 0.1  

depth_image = np.loadtxt('depth-array-4.txt', dtype=int)


depth_image = depth_image.astype(float)

depth_image[depth_image == 0] = np.nan

print(f"Loaded depth array of shape: {depth_image.shape}")

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

print("Flat surface mask detected values:", np.sum(flat_surface_mask))

labeled_array, num_features = label(flat_surface_mask)

fig, ax = plt.subplots()
ax.imshow(depth_image, cmap='viridis')
ax.imshow(flat_surface_mask, cmap='jet', alpha=0.5)

print(f"Number of detected flat regions: {num_features}")

for region_slice in find_objects(labeled_array):
    y1, x1 = region_slice[0].start, region_slice[1].start
    y2, x2 = region_slice[0].stop, region_slice[1].stop
    rect = plt.Rectangle((x1, y1), x2-x1, y2-y1, edgecolor='red', facecolor='none')
    ax.add_patch(rect)

plt.show()

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
    print(f"Largest region size: {largest_region_size}")

    y1, x1 = largest_region[0].start, largest_region[1].start
    y2, x2 = largest_region[0].stop, largest_region[1].stop

    crop_width = int((x2 - x1) * crop_percentage)
    x1 += crop_width
    x2 -= crop_width

    largest_region_shape = (y2 - y1, x2 - x1)
    print(f"Shape of the cropped flat surface: {largest_region_shape}")
    print(f"Cropped region start index: ({y1, x1})")
    print(f"Cropped region end index: ({y2, x2})")

    largest_region_array = depth_image[y1:y2, x1:x2]
    nan_count = np.isnan(largest_region_array).sum()
    print(f"Number of NaN values in the cropped region: {nan_count}")

    total_values = largest_region_array.size
    print(f"Total number of values in the cropped region: {total_values}")

    nan_percentage = (nan_count / total_values) * 100
    print(f"Percentage of NaN values in the cropped region: {nan_percentage:.2f}%")

    if nan_percentage > nan_threshold:
        print(f"The percentage of NaN values is above {nan_threshold}%. The cropped region will not be selected.")
    else:
        y, x = np.indices(largest_region_array.shape)
        y = y + largest_region[0].start
        x = x + largest_region[1].start
        z = largest_region_array

        x = x.flatten()
        y = y.flatten()
        z = z.flatten()

        z = -z

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        sc = ax.scatter(x, y, z, c=-z, cmap='viridis', s=1)  

        plt.colorbar(sc)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Inverted Depth')

        plt.show()

        nan_mask = np.isnan(largest_region_array)
        labeled_nan_array, num_nan_features = label(nan_mask)
        print(f"Number of NaN regions after filtering: {num_nan_features}")

        fig, ax = plt.subplots()
        ax.imshow(largest_region_array, cmap='viridis')
        valid_nan_regions = 0
        for nan_region_slice in find_objects(labeled_nan_array):
            nan_region_shape = (nan_region_slice[0].stop - nan_region_slice[0].start, nan_region_slice[1].stop - nan_region_slice[1].start)
            ny1, nx1 = nan_region_slice[0].start, nan_region_slice[1].start
            ny2, nx2 = nan_region_slice[0].stop, nan_region_slice[1].stop

            if nan_region_shape[0] >= nan_tolerant and nan_region_shape[1] >= nan_tolerant:
                if not ((ny1 < margin and nx1 < margin) or (ny1 < margin and nx2 > largest_region_array.shape[1] - margin) or
                        (ny2 > largest_region_array.shape[0] - margin and nx1 < margin) or (ny2 > largest_region_array.shape[0] - margin and nx2 > largest_region_array.shape[1] - margin)):
                    print(f"NaN region shape: {nan_region_shape}")
                    nan_rect = plt.Rectangle((nx1, ny1), nx2-nx1, ny2-ny1, edgecolor='red', facecolor='none')
                    ax.add_patch(nan_rect)
                    valid_nan_regions += 1

        plt.show()

        print(f"Number of valid NaN regions: {valid_nan_regions}")

        if valid_nan_regions > 0:
            print("Valid NaN regions found. The cropped region will not be selected.")
        else:
            print("No valid NaN regions found. The cropped region is selected.")
else:
    print("No valid flat regions found.")
