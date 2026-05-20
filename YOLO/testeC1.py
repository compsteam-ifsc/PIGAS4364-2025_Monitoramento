import os
import cv2
import requests
from ultralytics import YOLO

# ==================== CONFIG ====================
model = YOLO('yolov8n.pt')

pasta_videos = r"C:\Users\matheus-lopes\Desktop\saindo"
extensoes    = ('.mp4', '.avi', '.mkv', '.mov')

BASE_URL      = "http://localhost:8080"
URL_LOGIN     = f"{BASE_URL}/api/auth/login"
URL_RELATORIO = f"{BASE_URL}/api/relatorio"

ADMIN_USUARIO = "root"
ADMIN_SENHA   = "1010"
# ================================================

_token = None

def obter_token() -> str:
    print("[AUTH] Autenticando na API...")
    try:
        resp = requests.post(
            URL_LOGIN,
            json={"usuario": ADMIN_USUARIO, "senha": ADMIN_SENHA},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"[AUTH] Token obtido com sucesso (role: {data.get('role')})")
            return data.get("token")
        raise RuntimeError(f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        raise RuntimeError(f"Erro na conexão de autenticação: {e}")


def enviar(tipo: str, retry: bool = True) -> None:
    global _token
    headers = {"Authorization": f"Bearer {_token}"}

    try:
        r = requests.post(
            URL_RELATORIO,
            json={"saidaEntrada": tipo},
            headers=headers,
            timeout=3
        )
        print(f"[API] {tipo} -> Status: {r.status_code}")

        if r.status_code == 401 and retry:
            print("[AUTH] Token expirado, renovando...")
            _token = obter_token()
            enviar(tipo, retry=False)
        elif r.status_code not in (200, 201):
            print(f"[ERRO BACKEND]: {r.text}")

    except requests.exceptions.RequestException as e:
        print(f"[ERRO API]: {e}")


# Autenticação Inicial
try:
    _token = obter_token()
except RuntimeError as e:
    print(f"[ERRO CRÍTICO] {e}")
    exit(1)


# Varredura dos vídeos
for arquivo in os.listdir(pasta_videos):
    if not arquivo.lower().endswith(extensoes):
        continue

    caminho = os.path.join(pasta_videos, arquivo)
    print(f"\nProcessando: {arquivo}")

    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        print("Erro ao abrir:", arquivo)
        continue

    # Dicionário limpo a cada novo vídeo
    historico_posicoes = {}
    
    entradas = 0
    saidas   = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        altura, largura, _ = frame.shape
        LINE_Y = int(altura * 0.5) 

        # =================================================================
        # TRACKING PADRÃO (Ideal para vídeos fluidos normais)
        # =================================================================
        results = model.track(frame, persist=True, conf=0.4, imgsz=640, classes=[0], verbose=False)

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)

            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = map(int, box)
                
                # Ponto central da caixa detectada
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                # Verifica onde a pessoa está
                estado_atual = 'fora' if cy > LINE_Y else 'dentro'

                # Verifica cruzamento de linha
                if track_id in historico_posicoes:
                    estado_anterior = historico_posicoes[track_id]

                    if estado_anterior == 'fora' and estado_atual == 'dentro':
                        entradas += 1
                        print(f">>> [ID {track_id}] Entrada detectada")
                        enviar("ENTRADA")
                        
                    elif estado_anterior == 'dentro' and estado_atual == 'fora':
                        saidas += 1
                        print(f">>> [ID {track_id}] Saída detectada")
                        enviar("SAIDA")

                # Salva o estado atual para o próximo frame
                historico_posicoes[track_id] = estado_atual

                # Visual
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
                cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Interface Visual
        cv2.line(frame, (0, LINE_Y), (largura, LINE_Y), (0, 255, 255), 2)
        cv2.putText(frame, f"Entradas: {entradas} | Saidas: {saidas}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Contagem Padrão", frame)

        # Aperte 'q' para pular para o próximo vídeo/sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()

cv2.destroyAllWindows()