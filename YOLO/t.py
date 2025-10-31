import cv2
from ultralytics import YOLO
import time

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture("videoBiblioteca.mp4")
if not cap.isOpened():
    raise SystemExit("❌ Erro ao abrir o vídeo")

# --- CONFIGURAÇÕES ---
LINE_Y = 430   # linha divisória (ajuste fino conforme a porta)
OFFSET = 40    # margem de tolerância
MIN_AREA = 800 # ignora detecções pequenas

entradas = 0
saidas = 0
dentro = 0
fora = 0

# Estado de cada pessoa
estado_pessoa = {}

prev_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, conf=0.1, imgsz=960, classes=[0], persist=True, verbose=False)
    boxes = results[0].boxes

    cv2.line(frame, (0, LINE_Y), (frame.shape[1], LINE_Y), (0, 255, 255), 3)
    cv2.putText(frame, "LINHA DE CONTAGEM", (30, LINE_Y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    if boxes.id is not None:
        for box, track_id in zip(boxes.xyxy, boxes.id):
            x1, y1, x2, y2 = map(int, box)
            area = (x2 - x1) * (y2 - y1)
            if area < MIN_AREA:
                continue

            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Estado inicial: fora ou dentro
            if track_id not in estado_pessoa:
                estado_pessoa[track_id] = "fora" if cy < LINE_Y else "dentro"

            estado_atual = estado_pessoa[track_id]

            # Fora → Dentro
            if estado_atual == "fora" and cy > LINE_Y + OFFSET:
                entradas += 1
                dentro += 1
                if fora > 0:
                    fora -= 1
                estado_pessoa[track_id] = "dentro"
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

            # Dentro → Fora
            elif estado_atual == "dentro" and cy < LINE_Y - OFFSET:
                saidas += 1
                if dentro > 0:
                    dentro -= 1
                fora += 1
                estado_pessoa[track_id] = "fora"
                cv2.circle(frame, (cx, cy), 10, (0, 0, 255), -1)

            # Desenha bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.putText(frame, f"ID {int(track_id)}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)

    # FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time else 0
    prev_time = curr_time

    # Mostra contagens
    cv2.putText(frame, f"FPS: {fps:.1f}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
    cv2.putText(frame, f"Entradas: {entradas}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Saidas: {saidas}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, f"Dentro: {dentro}", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.imshow("Contagem Biblioteca", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()