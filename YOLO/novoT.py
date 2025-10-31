import cv2
import time
from ultralytics import YOLO

# ======= CONFIGURAÇÕES =======
MODEL_NAME = "yolov8n.pt"
VIDEO_SOURCE = "videoBiblioteca.mp4"
CONF_THRESHOLD = 0.6
IMGSZ = 640
LINE_POSITION = 0.5
LINE_THICKNESS = 2
MIN_BOX_AREA = 1500
COOLDOWN_SECONDS = 0.1
# ==============================

model = YOLO(MODEL_NAME)

# Usa o tracker padrão mas mais estável
tracker_cfg = "bytetrack.yaml"

cap = cv2.VideoCapture(VIDEO_SOURCE)
tracks = {}
entries, exits = 0, 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    line_y = int(h * LINE_POSITION)
    now = time.time()

    results = model.track(
        frame,
        conf=CONF_THRESHOLD,
        persist=True,
        tracker=tracker_cfg,
        classes=[0],
        imgsz=IMGSZ,
        verbose=False
    )

    if results and len(results) > 0 and results[0].boxes is not None:
        ids = results[0].boxes.id
        for i, box in enumerate(results[0].boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = (x2 - x1) * (y2 - y1)
            if area < MIN_BOX_AREA:
                continue

            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            track_id = int(ids[i]) if ids is not None else None
            if track_id is None:
                continue

            current_side = "outside" if cy > line_y else "inside"

            if track_id not in tracks:
                tracks[track_id] = {
                    "last_side": current_side,
                    "last_time": 0
                }
            else:
                prev_side = tracks[track_id]["last_side"]
                last_time = tracks[track_id]["last_time"]

                if prev_side != current_side and (now - last_time) > COOLDOWN_SECONDS:
                    if prev_side == "inside" and current_side == "outside":
                        exits += 1
                        direction = "SAINDO"
                        color = (0, 0, 255)
                    else:
                        entries += 1
                        direction = "ENTRANDO"
                        color = (0, 255, 0)

                    tracks[track_id]["last_time"] = now
                    cv2.putText(frame, direction, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                    print(f"[{track_id}] {direction}")

                tracks[track_id]["last_side"] = current_side

            # desenha retângulo e ID
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(frame, f"ID {track_id}", (x1, y1 - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)

    # desenha linha e contagem
    cv2.line(frame, (0, line_y), (w, line_y), (0, 0, 255), LINE_THICKNESS)
    cv2.putText(frame, "INSIDE", (10, line_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.putText(frame, "OUTSIDE", (10, line_y + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    current_inside = max(0, entries - exits)
    cv2.putText(frame, f"Entradas: {entries}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
    cv2.putText(frame, f"Saídas: {exits}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
    cv2.putText(frame, f"Dentro: {current_inside}", (10, 130),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,0), 2)

    cv2.imshow("Contagem Entrada/Saída", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()