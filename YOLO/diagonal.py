import cv2
from ultralytics import YOLO
import math
import time

# Carregar modelo YOLO
model = YOLO("yolov8n.pt")

# Abrir vídeo
cap = cv2.VideoCapture("videoDiagonal.mp4")
if not cap.isOpened():
    raise SystemExit("Erro ao abrir o vídeo")

# Configurações principais
LINE_Y = 350            # altura da linha virtual (ajuste conforme vídeo)
OFFSET = 30             # tolerância para cruzamento
MAX_DIST = 100          # distância máxima para associação
MIN_AREA = 700          # área mínima do objeto
ID_TIMEOUT = 40         # frames até descartar track

# Contadores
dentro = 0
entradas = 0
saidas = 0
frame_count = 0
NEXT_ID = 0

# Rastreadores simples
tracks = {}
prev_time = 0

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1

    # Detecção
    results = model.predict(frame, conf=0.3, imgsz=960, classes=[0], verbose=False)
    dets = []
    if results and len(results[0].boxes) > 0:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = (x2 - x1) * (y2 - y1)
            if area < MIN_AREA:
                continue
            cx, cy = (x1 + x2)//2, (y1 + y2)//2
            dets.append({'cx': cx, 'cy': cy, 'box': (x1, y1, x2, y2)})

    # Associação com rastros
    used_ids = set()
    for d in dets:
        best_id, best_dist = None, 1e9
        for tid, t in tracks.items():
            if tid in used_ids:
                continue
            d_ = dist((d['cx'], d['cy']), (t['cx'], t['cy']))
            if d_ < best_dist:
                best_id, best_dist = tid, d_
        if best_id is not None and best_dist < MAX_DIST:
            tracks[best_id].update({'cx': d['cx'], 'cy': d['cy'], 'last_seen': frame_count})
            used_ids.add(best_id)
            d['id'] = best_id
        else:
            d['id'] = NEXT_ID
            tracks[NEXT_ID] = {'cx': d['cx'], 'cy': d['cy'], 'last_seen': frame_count, 'side': 'cima' if d['cy'] < LINE_Y else 'baixo'}
            NEXT_ID += 1

    # Remove antigos
    for tid in [tid for tid, t in tracks.items() if frame_count - t['last_seen'] > ID_TIMEOUT]:
        del tracks[tid]

    # Verifica cruzamentos
    for tid, t in tracks.items():
        side_now = 'baixo' if t['cy'] > LINE_Y else 'cima'
        if t['side'] == 'cima' and side_now == 'baixo':
            entradas += 1
            dentro += 1
            tracks[tid]['side'] = side_now
        elif t['side'] == 'baixo' and side_now == 'cima':
            saidas += 1
            dentro = max(dentro - 1, 0)
            tracks[tid]['side'] = side_now

    # Desenhos
    cv2.line(frame, (0, LINE_Y), (frame.shape[1], LINE_Y), (0, 255, 255), 2)
    for d in dets:
        x1, y1, x2, y2 = d['box']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"ID {d['id']}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.putText(frame, f"Entradas: {entradas}  Saidas: {saidas}  Dentro: {dentro}", 
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time else 0
    prev_time = curr_time
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    cv2.imshow("Contagem Biblioteca", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()