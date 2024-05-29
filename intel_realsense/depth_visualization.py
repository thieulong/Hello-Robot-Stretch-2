import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Load the depth array from the file
depth_image = np.loadtxt('depth-array-1.txt', dtype=int)

# Get the dimensions of the depth image
height, width = depth_image.shape

# Generate x, y coordinates for each point
x, y = np.meshgrid(np.arange(width), np.arange(height))

# Flatten the arrays
x = x.flatten()
y = y.flatten()
z = depth_image.flatten()

# Filter out points where depth is zero (assuming zero depth means no data)
mask = z > 0
x = x[mask]
y = y[mask]
z = z[mask]

# Invert the depth values
z = -z

# Create a 3D scatter plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(x, y, z, c=-z, cmap='viridis', s=1)  # Use -z for color to maintain original color scheme

# Add color bar which maps values to colors
plt.colorbar(sc)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Inverted Depth')

plt.show()
