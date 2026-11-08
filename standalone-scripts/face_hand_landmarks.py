# Находит ориентиры лица и рук с помощью MediaPipe и OpenCV.
import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


PHONE_STREAM_URL = "http://192.168.0.103:8080/video"
MODEL_DIR = Path("/home/satashi/mediapipe_models")
FACE_MODEL = MODEL_DIR / "face_landmarker.task"
HAND_MODEL = MODEL_DIR / "hand_landmarker.task"

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]
FINGER_TIPS = [4, 8, 12, 16, 20]


def normalized_to_pixel(landmark, width, height):
    return int(landmark.x * width), int(landmark.y * height)


def inside_frame(point, width, height):
    x, y = point
    return 0 <= x < width and 0 <= y < height


def draw_face_mesh(frame, landmarks):
    height, width, _ = frame.shape
    points = [normalized_to_pixel(point, width, height) for point in landmarks]
    points = [point for point in points if inside_frame(point, width, height)]
    if len(points) < 3:
        return

    subdiv = cv2.Subdiv2D((0, 0, width, height))
    for point in points:
        subdiv.insert(point)

    for triangle in subdiv.getTriangleList():
        p1 = (int(triangle[0]), int(triangle[1]))
        p2 = (int(triangle[2]), int(triangle[3]))
        p3 = (int(triangle[4]), int(triangle[5]))
        if inside_frame(p1, width, height) and inside_frame(p2, width, height) and inside_frame(p3, width, height):
            cv2.line(frame, p1, p2, (0, 220, 255), 1)
            cv2.line(frame, p2, p3, (0, 220, 255), 1)
            cv2.line(frame, p3, p1, (0, 220, 255), 1)

    for point in points[::2]:
        cv2.circle(frame, point, 1, (255, 255, 255), -1)


def draw_hand_lines(frame, landmarks):
    height, width, _ = frame.shape
    points = [normalized_to_pixel(point, width, height) for point in landmarks]

    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], (80, 255, 120), 2)

    wrist = landmarks[0]
    middle_base = landmarks[9]
    center = (
        int(((wrist.x + middle_base.x) / 2) * width),
        int(((wrist.y + middle_base.y) / 2) * height) - 60,
    )

    cv2.circle(frame, center, 9, (0, 0, 255), -1)
    for tip_id in FINGER_TIPS:
        point = points[tip_id]
        cv2.circle(frame, point, 7, (0, 255, 255), -1)
        cv2.line(frame, point, center, (255, 0, 255), 3)


def build_landmarkers():
    face_options = vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(FACE_MODEL)),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    hand_options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(HAND_MODEL)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    return (
        vision.FaceLandmarker.create_from_options(face_options),
        vision.HandLandmarker.create_from_options(hand_options),
    )


def main():
    if not FACE_MODEL.exists() or not HAND_MODEL.exists():
        print(f"Missing model files in {MODEL_DIR}")
        return

    cap = cv2.VideoCapture(PHONE_STREAM_URL)
    if not cap.isOpened():
        print("Camera stream is not available.")
        print(f"Check this URL in the browser first: {PHONE_STREAM_URL}")
        return

    face_landmarker, hand_landmarker = build_landmarkers()
    start_time = time.monotonic()

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No frame from phone stream.")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((time.monotonic() - start_time) * 1000)

        face_result = face_landmarker.detect_for_video(mp_image, timestamp_ms)
        hand_result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)

        for face_landmarks in face_result.face_landmarks:
            draw_face_mesh(frame, face_landmarks)

        for hand_landmarks in hand_result.hand_landmarks:
            draw_hand_lines(frame, hand_landmarks)

        cv2.imshow("Face Mesh + Hand Lines", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    face_landmarker.close()
    hand_landmarker.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
