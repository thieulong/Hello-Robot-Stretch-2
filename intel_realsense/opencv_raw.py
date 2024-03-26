import pyrealsense2 as rs
import numpy as np
import cv2

# Configure color stream
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

try:
    while True:
        # Wait for a coherent color frame
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        # Convert color image to numpy array
        color_image = np.asanyarray(color_frame.get_data())

        # Show color image
        cv2.namedWindow('Color Image', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('Color Image', color_image)
        cv2.waitKey(1)

finally:
    # Stop streaming
    pipeline.stop()
