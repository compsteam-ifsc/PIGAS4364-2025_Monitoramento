import os
import cv2
import math
import time
import requests
from ultralytics import YOLO

# ---------------- CONFIG ----------------
model = YOLO('yolov8n.pt')

pasta_videos = r"C:\Users\eduardo-heck\Desktop\teste"
extensoes = ('.mp4', '.avi', '.mkv', '.mov')

URL_BACKEND = "http://localhost:8080/api/relatorio"
# ---------------------------------------

def euclid(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def testar_api():
    print("\n[TESTE] Testando API...")
    try:
        r = requests.post(URL_BACKEND, json={"saidaEntrada": "ENTRADA"}, timeout=3)
        print("[TESTE] Status:", r.status_code)
        print("[TESTE] Resposta:", r.text)
    except Exception as e:
        print("[TESTE ERRO]:", e)


def enviar(tipo):
    try:
        r = requests.post(
            URL_BACKEND,
            json={"saidaEntrada": tipo},
            timeout=3
        )

        print(f"[API] {tipo} -> Status:", r.status_code)

        if r.status_code != 200:
            print("[ERRO BACKEND]:", r.text)

    except Exception as e:
        print("[ERRO API]:", e)


testar_api()


for arquivo in os.listdir(pasta_videos):
    if not arquivo.lower().endswith(extensoes):
        continue

    caminho = os.path.join(pasta_videos, arquivo)
    print(f"\nProcessando: {arquivo}")

    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        print("Erro ao abrir:", arquivo)
        continue

    LINE_Y = 320
    MIN_AREA = 300
    MAX_DIST = 200
    ID_TIMEOUT = 60
    NEXT_ID = 0

    entradas = 0
    saidas = 0

    tracks = {}
    frame_count = 0

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

                dets.append({'cx': cx, 'cy': cy})

        unmatched_dets = []
        used_ids = set()

        for d in dets:
            best_id = None
            best_dist = 1e9

            for tid, t in tracks.items():
                if tid in used_ids:
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
                used_ids.add(best_id)
            else:
                unmatched_dets.append(d)

        for d in unmatched_dets:
            tracks[NEXT_ID] = {
                'cx': d['cx'],
                'cy': d['cy'],
                'last_seen': frame_count,
                'state': ('dentro' if d['cy'] < LINE_Y else 'fora'),
                'hits': 1
            }
            NEXT_ID += 1

        # remover antigos
        to_delete = [
            tid for tid, t in tracks.items()
            if frame_count - t['last_seen'] > ID_TIMEOUT
        ]
        for tid in to_delete:
            del tracks[tid]

        # ---------------- CONTAGEM + ENVIO ----------------
        for tid, t in tracks.items():
            cy = t['cy']
            prev = t['state']
            cur = 'fora' if cy > LINE_Y else 'dentro'

            # ENTRADA
            if prev == 'fora' and cur == 'dentro' and t['hits'] > 1:
                entradas += 1
                t['state'] = 'dentro'

                print(">>> Entrada detectada")
                enviar("ENTRADA")

            # SAÍDA
            elif prev == 'dentro' and cur == 'fora' and t['hits'] > 1:
                saidas += 1
                t['state'] = 'fora'

                print(">>> Saída detectada")
                enviar("SAIDA")

        # UI
        cv2.line(frame, (0, LINE_Y), (frame.shape[1], LINE_Y), (0,255,255), 2)

        cv2.putText(frame, f"{arquivo}", (20,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        cv2.putText(frame, f"Entradas:{entradas} Saidas:{saidas}", (20,60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        cv2.imshow("Contagem", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()

cv2.destroyAllWindows()