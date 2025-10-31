import cv2
from ultralytics import YOLO
import time

# Load YOLOv8 model (nano for speed)
model = YOLO("yolov8n.pt")


#Video 
cap = cv2.VideoCapture("videoBiblioteca.mp4")

# Open webcam
#cap = cv2.VideoCapture(0)
#if not cap.isOpened():
#    raise SystemExit("❌ Cannot open webcam")

# Set webcam resolution (adjust as needed)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Fullscreen window
cv2.namedWindow("YOLOv8 Human Detection", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("YOLOv8 Human Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

prev_time = 0
frame_count = 0
last_results = None  # store last YOLO results

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # Run YOLO only every 2 frames (you can change to 3 for more speed)
    if frame_count % 1 == 0:
        last_results = model.predict(frame, conf=0.2, classes=[0], iou=0.45, imgsz = 640, verbose=False)

    # Draw detections from last_results
    if last_results is not None:
        for box in last_results[0].boxes:
            cls_id = int(box.cls)
            conf = float(box.conf)
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # bounding box coords

            if cls_id == 0:  # person
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                # Confidence text
                cv2.putText(frame, f"Human {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # FPS counter
    curr_time = time.time()
    fps_display = 1 / (curr_time - prev_time) if prev_time else 0
    prev_time = curr_time
    cv2.putText(frame, f"FPS: {fps_display:.1f}", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 2)

    # Show fullscreen
    cv2.imshow("YOLOv8 Human Detection", frame)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
