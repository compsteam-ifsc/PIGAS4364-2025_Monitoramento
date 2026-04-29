import os
import cv2
import math
import time
import requests
from ultralytics import YOLO

# ==================== CONFIG ====================
model = YOLO('yolov8n.pt')

pasta_videos = r"C:\Users\eduardo-heck\Desktop\outros"
extensoes    = ('.mp4', '.avi', '.mkv', '.mov')

BASE_URL      = "http://localhost:8080"
URL_LOGIN     = f"{BASE_URL}/api/auth/login"
URL_RELATORIO = f"{BASE_URL}/api/relatorio"

# Credenciais do usuário ADMIN cadastrado no banco
ADMIN_USUARIO = "root"
ADMIN_SENHA   = "1010"
# ================================================


def obter_token() -> str:
    """
    Autentica na API e retorna o JWT.
    Lança RuntimeError se as credenciais estiverem erradas ou o usuário
    não for ROLE_ADMIN.
    """
    print("[AUTH] Autenticando na API...")
    resp = requests.post(
        URL_LOGIN,
        json={"usuario": ADMIN_USUARIO, "senha": ADMIN_SENHA},
        timeout=5
    )

    if resp.status_code == 200:
        token = resp.json().get("token")
        print(f"[AUTH] Token obtido com sucesso (role: {resp.json().get('role')})")
        return token

    raise RuntimeError(
        f"[AUTH] Falha ao autenticar — status {resp.status_code}: {resp.text}"
    )


def enviar(tipo: str, token: str, retry: bool = True) -> None:
    """
    Envia ENTRADA ou SAIDA para o backend com o JWT no header Authorization.
    Em caso de 401 (token expirado) tenta renovar uma vez.
    """
    global _token  # permite renovação automática do token

    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.post(
            URL_RELATORIO,
            json={"saidaEntrada": tipo},
            headers=headers,
            timeout=3
        )

        print(f"[API] {tipo} -> Status: {r.status_code}")

        if r.status_code == 401 and retry:
            # Token expirou — renova e tenta mais uma vez
            print("[AUTH] Token expirado, renovando...")
            _token = obter_token()
            enviar(tipo, _token, retry=False)

        elif r.status_code not in (200, 201):
            print(f"[ERRO BACKEND]: {r.text}")

    except requests.exceptions.RequestException as e:
        print(f"[ERRO API]: {e}")


def testar_api(token: str) -> None:
    """Envia uma requisição de teste para verificar conectividade."""
    print("\n[TESTE] Testando API com token...")
    try:
        r = requests.post(
            URL_RELATORIO,
            json={"saidaEntrada": "ENTRADA"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=3
        )
        print(f"[TESTE] Status: {r.status_code} | Resposta: {r.text}")
    except Exception as e:
        print(f"[TESTE ERRO]: {e}")


# ==================== INÍCIO ====================

# 1. Autenticar e obter token JWT
try:
    _token = obter_token()
except RuntimeError as e:
    print(e)
    exit(1)

# 2. Teste de conexão
testar_api(_token)

# 3. Processar vídeos
def euclid(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


for arquivo in os.listdir(pasta_videos):
    if not arquivo.lower().endswith(extensoes):
        continue

    caminho = os.path.join(pasta_videos, arquivo)
    print(f"\nProcessando: {arquivo}")

    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        print("Erro ao abrir:", arquivo)
        continue

    LINE_Y     = 320
    MIN_AREA   = 300
    MAX_DIST   = 200
    ID_TIMEOUT = 60
    NEXT_ID    = 0

    entradas = 0
    saidas   = 0
    tracks   = {}
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
                area = (x2 - x1) * (y2 - y1)
                if area < MIN_AREA:
                    continue
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                dets.append({'cx': cx, 'cy': cy})

        unmatched_dets = []
        used_ids = set()

        for d in dets:
            best_id   = None
            best_dist = 1e9

            for tid, t in tracks.items():
                if tid in used_ids:
                    continue
                dist = euclid((d['cx'], d['cy']), (t['cx'], t['cy']))
                if dist < best_dist:
                    best_dist = dist
                    best_id   = tid

            if best_id is not None and best_dist < MAX_DIST:
                tracks[best_id]['cx']        = d['cx']
                tracks[best_id]['cy']        = d['cy']
                tracks[best_id]['last_seen'] = frame_count
                tracks[best_id]['hits']     += 1
                used_ids.add(best_id)
            else:
                unmatched_dets.append(d)

        for d in unmatched_dets:
            tracks[NEXT_ID] = {
                'cx':        d['cx'],
                'cy':        d['cy'],
                'last_seen': frame_count,
                'state':     'dentro' if d['cy'] < LINE_Y else 'fora',
                'hits':      1
            }
            NEXT_ID += 1

        # Remover tracks antigos
        to_delete = [
            tid for tid, t in tracks.items()
            if frame_count - t['last_seen'] > ID_TIMEOUT
        ]
        for tid in to_delete:
            del tracks[tid]

        # Contagem e envio
        for tid, t in tracks.items():
            cy   = t['cy']
            prev = t['state']
            cur  = 'fora' if cy > LINE_Y else 'dentro'

            if prev == 'fora' and cur == 'dentro' and t['hits'] > 1:
                entradas += 1
                t['state'] = 'dentro'
                print(">>> Entrada detectada")
                enviar("ENTRADA", _token)

            elif prev == 'dentro' and cur == 'fora' and t['hits'] > 1:
                saidas += 1
                t['state'] = 'fora'
                print(">>> Saída detectada")
                enviar("SAIDA", _token)

        # UI
        cv2.line(frame, (0, LINE_Y), (frame.shape[1], LINE_Y), (0, 255, 255), 2)
        cv2.putText(frame, f"{arquivo}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Entradas:{entradas} Saidas:{saidas}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Contagem", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()

cv2.destroyAllWindows()
