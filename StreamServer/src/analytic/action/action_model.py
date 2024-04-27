import os
import cv2
import time
from fastapi import HTTPException
import torch
import argparse
import numpy as np

from .Detection.Utils import ResizePadding
from .CameraLoader import CamLoader, CamLoader_Q
from .DetectorLoader import TinyYOLOv3_onecls

from .PoseEstimateLoader import SPPE_FastPose
from .fn import draw_single

from .Track.Tracker import Detection, Tracker
from .ActionsEstLoader import TSSTG

from config import CONFIG_FILE, YOLO_WEIGHT_FILE, SPPE_WEIGHT_FILE, TSSTG_WEIGHT_FILE

CONFIG_FILE = CONFIG_FILE
YOLO_WEIGHT_FILE = YOLO_WEIGHT_FILE
SPPE_WEIGHT_FILE = SPPE_WEIGHT_FILE
TSSTG_WEIGHT_FILE = TSSTG_WEIGHT_FILE

INP_DETS = 384
INP_POSE = (224, 160)
POSE_BACKBONE = 'resnet50'
SHOW_DETECTED = False
SHOW_SKELETON = True
DEVICE = 'cuda'

resize_fn = ResizePadding(INP_DETS, INP_DETS)

def preproc(image):
    """preprocess function for CameraLoader.
    """
    image = resize_fn(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image


def kpt2bbox(kpt, ex=20):
    """Get bbox that hold on all of the keypoints (x,y)
    kpt: array of shape `(N, 2)`,
    ex: (int) expand bounding box,
    """
    return np.array((kpt[:, 0].min() - ex, kpt[:, 1].min() - ex,
                     kpt[:, 0].max() + ex, kpt[:, 1].max() + ex))


def generate_action_model_frame(source):
    CAM_SOURCE = source

    # Model initialization
    detect_model = TinyYOLOv3_onecls(INP_DETS, device=DEVICE, config_file=CONFIG_FILE,
                                     weight_file=YOLO_WEIGHT_FILE)
    pose_model = SPPE_FastPose(POSE_BACKBONE, INP_POSE[0], INP_POSE[1], device=DEVICE, path=SPPE_WEIGHT_FILE)
    action_model = TSSTG(weight_file=TSSTG_WEIGHT_FILE) # action model

    # Tracker.
    max_age = 30
    tracker = Tracker(max_age=max_age, n_init=3)

    cam = CamLoader(int(CAM_SOURCE) if CAM_SOURCE.isdigit() else CAM_SOURCE,
                    preprocess=preproc).start()

    fps_time = 0
    f = 0
    while cam.grabbed():
        f += 1
        frame = cam.getitem()
        image = frame.copy()

        # Detect humans bbox in the frame with detector model.
        detected = detect_model.detect(frame, need_resize=False, expand_bb=10)

        # Predict each tracks bbox of current frame from previous frames information with Kalman filter.
        tracker.predict()
        # Merge two source of predicted bbox together.
        for track in tracker.tracks:
            det = torch.tensor([track.to_tlbr().tolist() + [0.5, 1.0, 0.0]], dtype=torch.float32)
            detected = torch.cat([detected, det], dim=0) if detected is not None else det

        detections = []  # List of Detections object for tracking.
        if detected is not None:
            #detected = non_max_suppression(detected[None, :], 0.45, 0.2)[0]
            # Predict skeleton pose of each bboxs.
            poses = pose_model.predict(frame, detected[:, 0:4], detected[:, 4])

            # Create Detections object.
            detections = [Detection(kpt2bbox(ps['keypoints'].numpy()),
                                    np.concatenate((ps['keypoints'].numpy(),
                                                    ps['kp_score'].numpy()), axis=1),
                                    ps['kp_score'].mean().numpy()) for ps in poses]

            # VISUALIZE.
            if SHOW_DETECTED:
                for bb in detected[:, 0:5]:
                    frame = cv2.rectangle(frame, (bb[0], bb[1]), (bb[2], bb[3]), (0, 0, 255), 1)

        # Update tracks by matching each track information of current and previous frame or
        # create a new track if no matched.
        tracker.update(detections)

        # Predict Actions of each track.
        for i, track in enumerate(tracker.tracks):
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            bbox = track.to_tlbr().astype(int)
            center = track.get_center().astype(int)

            action = 'pending'
            clr = (0, 255, 0)
            # Use 30 frames time-steps to prediction.
            if len(track.keypoints_list) == 30:
                pts = np.array(track.keypoints_list, dtype=np.float32)
                out = action_model.predict(pts, frame.shape[:2])
                action_name = action_model.class_names[out[0].argmax()]
                action = '{}: {:.2f}%'.format(action_name, out[0].max() * 100)
                if action_name == 'Fall Down':
                    clr = (255, 0, 0)
                elif action_name == 'Lying Down':
                    clr = (255, 200, 0)

            # VISUALIZE.
            if track.time_since_update == 0:
                if SHOW_SKELETON:
                    frame = draw_single(frame, track.keypoints_list[-1])
                frame = cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 1)
                frame = cv2.putText(frame, str(track_id), (center[0], center[1]), cv2.FONT_HERSHEY_COMPLEX,
                                    0.4, (255, 0, 0), 2)
                frame = cv2.putText(frame, action, (bbox[0] + 5, bbox[1] + 15), cv2.FONT_HERSHEY_COMPLEX,
                                    0.4, clr, 1)

        # Show Frame.
        frame = cv2.resize(frame, (0, 0), fx=2., fy=2.)
        frame = cv2.putText(frame, '%d, FPS: %f' % (f, 1.0 / (time.time() - fps_time)),
                            (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        frame = frame[:, :, ::-1]
        fps_time = time.time()

        # return frame for video streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            # If encoding fails, raise an error to stop the streaming
            raise HTTPException(status_code=500, detail="Frame encoding failed")
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


def output_action_detection():
    pass