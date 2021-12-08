import numpy as np
import cv2
import glob

cam_image_names = sorted(glob.glob('city_of_lights/scans_np/*.npy'))
for i in range(len(cam_image_names)):
    events = np.load(cam_image_names[i])
    print(cam_image_names[i])
    cv2.imshow('viz', (events))
    cv2.waitKey(0)
