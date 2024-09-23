#!/usr/bin/env python

import rospy
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import threading
import h5py
import json
import time
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from std_srvs.srv import SetBool, SetBoolResponse

class GraspingDetectionNode:
    def __init__(self):
        rospy.init_node('grasping_detection_node', anonymous=True)
        self.open_gripper_pub = rospy.Publisher("/grasp_detect_auto", Bool, queue_size=1)
        self.image_pub = rospy.Publisher('/grasping_detection/image', Image, queue_size=10)
        self.bridge = CvBridge()

        self.cap = cv2.VideoCapture(4)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0)

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(max_num_hands=1)
        self.mpDraw = mp.solutions.drawing_utils

        custom_objects = {
            'Orthogonal': tf.keras.initializers.Orthogonal
        }

        with h5py.File("lstm-hand-grasping.h5", 'r') as f:
            model_config = f.attrs.get('model_config')
            model_config = json.loads(model_config)

            for layer in model_config['config']['layers']:
                if 'time_major' in layer['config']:
                    del layer['config']['time_major']

            model_json = json.dumps(model_config)

            self.model = tf.keras.models.model_from_json(model_json, custom_objects=custom_objects)

            weights_group = f['model_weights']
            for layer in self.model.layers:
                layer_name = layer.name
                if layer_name in weights_group:
                    weight_names = weights_group[layer_name].attrs['weight_names']
                    layer_weights = [weights_group[layer_name][weight_name] for weight_name in weight_names]
                    layer.set_weights(layer_weights)

        self.lm_list = []
        self.label = "not grasped"
        self.neutral_label = "not grasped"
        self.grasped_start_time = None
        self.running = False

        rospy.Service('ControlGrasping', SetBool, self.control_grasping_callback)

    def control_grasping_callback(self, req):
        self.running = req.data
        return SetBoolResponse(success=True, message="Grasping detection {}.".format("started" if req.data else "stopped"))

    def make_landmark_timestep(self, results):
        c_lm = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for lm in hand_landmarks.landmark:
                    c_lm.append(lm.x)
                    c_lm.append(lm.y)
                    c_lm.append(lm.z)
        return c_lm

    def draw_landmark_on_image(self, results, frame):
        for hand_landmarks in results.multi_hand_landmarks:
            self.mpDraw.draw_landmarks(frame, hand_landmarks, self.mpHands.HAND_CONNECTIONS)
        return frame

    def draw_bounding_box_and_label(self, frame, results, label):
        for hand_landmarks in results.multi_hand_landmarks:
            x_min, y_min = 1, 1
            x_max, y_max = 0, 0
            for lm in hand_landmarks.landmark:
                x_min = min(x_min, lm.x)
                y_min = min(y_min, lm.y)
                x_max = max(x_max, lm.x)
                y_max = max(y_max, lm.y)
            h, w, c = frame.shape
            x_min = int(x_min * w)
            y_min = int(y_min * h)
            x_max = int(x_max * w)
            y_max = int(y_max * h)
            color = (0, 0, 255) if label != self.neutral_label else (0, 255, 0)
            thickness = 2 if label != self.neutral_label else 1
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, thickness)
            cv2.putText(frame, f"Status: {label}", (x_min, y_max + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 1)
        return frame

    def detect(self, model, lm_list):
        lm_list = np.array(lm_list)
        lm_list = np.expand_dims(lm_list, axis=0)
        result = model.predict(lm_list)
        percentage_result = result * 100
        rospy.loginfo(f"Model prediction result: {percentage_result}")
        if result[0][0] > 0.5:
            self.label = "neutral"
        elif result[0][1] > 0.5:
            self.label = "resting"
        elif result[0][2] > 0.5:
            self.label = "carrying"
        elif result[0][3] > 0.5:
            self.label = "cupping"
        if self.label in ["neutral", "resting"]:
            self.label = "not grasped"
        if self.label in ["carrying", "cupping"]:
            self.label = "grasped"

        if self.label == "grasped":
            if self.grasped_start_time is None:
                self.grasped_start_time = time.time()
            elif time.time() - self.grasped_start_time >= 0.5:
                self.open_gripper_pub.publish(True)
                rospy.loginfo("Release object")
                
        else:
            self.grasped_start_time = None

        return str(self.label)

    def run(self):
        cv2.namedWindow("image", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("image", 1200, 1000)

        i = 0
        warm_up_frames = 60

        while not rospy.is_shutdown():
            if self.running:
                ret, frame = self.cap.read()
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                h, w, c = frame.shape
                crop_size = 0.8
                x_center = w // 2
                y_center = h // 2
                crop_w = int(w * crop_size)
                crop_h = int(h * crop_size)

                x1 = x_center - crop_w // 2
                x2 = x_center + crop_w // 2
                y1 = y_center - crop_h // 2
                y2 = y_center + crop_h // 2
                cropped_frame = frame[y1:y2, x1:x2]

                frame_resized = cv2.resize(cropped_frame, (w, h))
                frameRGB = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frameRGB)
                i += 1
                if i > warm_up_frames:
                    if results.multi_hand_landmarks:
                        lm = self.make_landmark_timestep(results)
                        self.lm_list.append(lm)
                        if len(self.lm_list) == 20:
                            t1 = threading.Thread(target=self.detect, args=(self.model, self.lm_list))
                            t1.start()
                            self.lm_list = []
                        frame_resized = self.draw_landmark_on_image(results, frame_resized)
                        frame_resized = self.draw_bounding_box_and_label(frame_resized, results, self.label)
                    cv2.imshow("image", frame_resized)
                    img_msg = self.bridge.cv2_to_imgmsg(frame_resized, "bgr8")
                    self.image_pub.publish(img_msg)
                    if cv2.waitKey(1) == ord('q'):
                        break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    node = GraspingDetectionNode()
    node.run()
