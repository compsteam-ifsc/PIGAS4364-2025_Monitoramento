import torch
import cv2
from ultralytics import YOLO
import time
import math

model = YOLO('yolov8n'
'.pt')
cap = cv2.VideoCapture("videoBiblioteca.mp4")
if not cap.isOpened():
    raise SystemExit("Erro ao abrir o vídeo")

# CONFIG
LINE_Y = 430
OFFSET = 40
MIN_AREA = 700
MAX_DIST = 120
ID_TIMEOUT = 30
NEXT_ID = 0

# contadores
entradas = 0
saidas = 0
dentro = 0
fora = 0

# tracker simples
tracks = {}
frame_count = 0
prev_time = 0

def euclid(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1

    results = model.predict(frame, conf=0.3, imgsz=960, classes=[0], verbose=False)
    dets = []
    if len(results) > 0 and len(results[0].boxes) > 0:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = (x2-x1)*(y2-y1)
            if area < MIN_AREA: 
                continue
            cx = int((x1+x2)/2)
            cy = int((y1+y2)/2)
            dets.append({'box':(x1,y1,x2,y2),'cx':cx,'cy':cy})

    unmatched_dets = []
    used_track_ids = set()
    for d in dets:
        best_id = None
        best_dist = 1e9
        for tid, t in tracks.items():
            if tid in used_track_ids: 
                continue
            dist = euclid((d['cx'], d['cy']), (t['cx'], t['cy']))
            if dist < best_dist:
                best_dist = dist
                best_id = tid
        if best_id is not None and best_dist < MAX_DIST:
            tracks[best_id]['cx'] = d['cx']
            tracks[best_id]['cy'] = d['cy']
            tracks[best_id]['last_seen'] = frame_count
            tracks[best_id]['hits'] += 1
            used_track_ids.add(best_id)
            d['assigned_id'] = best_id
        else:
            unmatched_dets.append(d)

    # cria novos tracks
    for d in unmatched_dets:
        tracks[NEXT_ID] = {
            'cx': d['cx'],
            'cy': d['cy'],
            'last_seen': frame_count,
            'state': ('dentro' if d['cy'] < LINE_Y else 'fora'),  # INVERTIDO AQUI
            'hits': 1
        }
        d['assigned_id'] = NEXT_ID
        NEXT_ID += 1

    # remove tracks antigos
    to_delete = [tid for tid, t in tracks.items() if frame_count - t['last_seen'] > ID_TIMEOUT]
    for tid in to_delete:
        del tracks[tid]

    # Atualiza estados e contagem
    for tid, t in list(tracks.items()):
        cy = t['cy']
        prev_state = t['state']
        cur_state = 'fora' if cy > LINE_Y else 'dentro'  # INVERTIDO AQUI

        # Agora entrada = atravessou pra fora → dentro (subiu)
        if prev_state == 'fora' and cur_state == 'dentro' and t['hits'] > 1:
            entradas += 1
            dentro += 1
            if fora > 0: fora -= 1
            tracks[tid]['state'] = 'dentro'
            cv2.circle(frame, (t['cx'], t['cy']), 12, (0,255,0), -1)

        # Saída = atravessou pra dentro → fora (desceu)
        elif prev_state == 'dentro' and cur_state == 'fora' and t['hits'] > 1:
            saidas += 1
            if dentro > 0: dentro -= 1
            fora += 1
            tracks[tid]['state'] = 'fora'
            cv2.circle(frame, (t['cx'], t['cy']), 12, (0,0,255), -1)

    # Desenhos
    cv2.line(frame, (0, LINE_Y), (frame.shape[1], LINE_Y), (0,255,255), 2)
    cv2.putText(frame, f"Entradas:{entradas}  Saidas:{saidas}  Dentro:{dentro}  Fora:{fora}", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

    for d in dets:
        x1,y1,x2,y2 = d['box']
        tid = d.get('assigned_id', -1)
        cv2.rectangle(frame, (x1,y1),(x2,y2),(0,255,0),2)
        cv2.putText(frame, f"ID {tid}", (x1,y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
        cv2.circle(frame, (d['cx'], d['cy']), 4, (0,0,255), -1)

    curr_time = time.time()
    fps = 1/(curr_time - prev_time) if prev_time else 0
    prev_time = curr_time
    cv2.putText(frame, f"FPS:{fps:.1f}", (20,80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

    cv2.imshow("Contagem", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()