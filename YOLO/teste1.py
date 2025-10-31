import cv2
from ultralytics import YOLO
import time

# === Configurações iniciais ===
model = YOLO("yolov8n.pt")  # modelo leve
cap = cv2.VideoCapture("videoBiblioteca.mp4")

# Define resolução
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Janelas
cv2.namedWindow("Contagem Biblioteca", cv2.WINDOW_NORMAL)

# === Linhas de contagem (ajuste se necessário) ===
# Y da linha de fora (área preta)
line_out_y = 300
# Y da linha de dentro (sensores)
line_in_y = 400

# === Variáveis de contagem ===
inside_count = 0
outside_count = 0
entered_count = 0
exited_count = 0
last_cross_time = {}

# === Loop principal ===
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, persist=True, conf=0.45, iou=0.5, classes=[0], verbose=False)
    detections = results[0].boxes if results and results[0].boxes is not None else []

    # Linhas de referência
    cv2.line(frame, (0, line_out_y), (frame.shape[1], line_out_y), (0, 0, 255), 3)
    cv2.line(frame, (0, line_in_y), (frame.shape[1], line_in_y), (0, 255, 0), 3)

    current_time = time.time()

    if detections is not None:
        for box in detections:
            if box.id is None:
                continue  # ignora se sem ID
            track_id = int(box.id.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # centro da pessoa

            # Desenha
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
            cv2.putText(frame, f"ID {track_id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Verifica cruzamento de linha
            last_y = last_cross_time.get(track_id, {}).get("y", cy)
            last_time = last_cross_time.get(track_id, {}).get("time", 0)

            # Evita contar o mesmo ID várias vezes seguidas
            if current_time - last_time > 2:  
                # Entrou: de fora (y < out) para dentro (y > in)
                if last_y < line_out_y and cy > line_in_y:
                    entered_count += 1
                    inside_count += 1
                    if inside_count > 0:
                        outside_count = max(0, outside_count - 1)
                    last_cross_time[track_id] = {"y": cy, "time": current_time}
                # Saiu: de dentro (y > in) para fora (y < out)
                elif last_y > line_in_y and cy < line_out_y:
                    exited_count += 1
                    outside_count += 1
                    inside_count = max(0, inside_count - 1)
                    last_cross_time[track_id] = {"y": cy, "time": current_time}
                else:
                    last_cross_time[track_id] = {"y": cy, "time": last_time}
            else:
                last_cross_time[track_id]["y"] = cy

    # === Exibe contagem ===
    cv2.putText(frame, f"Dentro: {inside_count}", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
    cv2.putText(frame, f"Fora: {outside_count}", (30, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    cv2.putText(frame, f"Entraram: {entered_count}", (30, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)
    cv2.putText(frame, f"Sairam: {exited_count}", (30, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)

    # Mostra imagem
    cv2.imshow("Contagem Biblioteca", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()