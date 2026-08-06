import os
import time
import json
import cv2
import requests
from queue import Queue, Empty
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ultralytics import YOLO

model = YOLO('yolov8n.pt')

PASTA_VIDEOS = r"C:\Users\matheus-lopes\Desktop\SLA32\Videos"
EXTENSOES = ('.mp4', '.avi', '.mkv', '.mov')
ARQUIVO_PROCESSADOS = os.path.join(PASTA_VIDEOS, ".processados.json")

BASE_URL = "http://localhost:8080"
URL_LOGIN = f"{BASE_URL}/api/auth/login"
URL_RELATORIO = f"{BASE_URL}/api/relatorio"

ADMIN_USUARIO = "root"
ADMIN_SENHA = "1010"
_token = None

fila_videos = Queue()
processados = set()


def carregar_processados():
    if os.path.exists(ARQUIVO_PROCESSADOS):
        try:
            with open(ARQUIVO_PROCESSADOS, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def salvar_processados():
    with open(ARQUIVO_PROCESSADOS, "w") as f:
        json.dump(list(processados), f)


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


def arquivo_estavel(caminho, checagens=3, intervalo=1.0):
    tamanho_anterior = -1
    estavel_count = 0
    for _ in range(30):
        try:
            tamanho_atual = os.path.getsize(caminho)
        except OSError:
            return False
        if tamanho_atual == tamanho_anterior and tamanho_atual > 0:
            estavel_count += 1
            if estavel_count >= checagens:
                return True
        else:
            estavel_count = 0
        tamanho_anterior = tamanho_atual
        time.sleep(intervalo)
    return False


def processar_video(caminho):
    arquivo = os.path.basename(caminho)
    print(f"\nProcessando: {arquivo}")

    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        print("Erro ao abrir:", arquivo)
        return

    historico_posicoes = {}
    entradas = 0
    saidas = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        altura, largura, _ = frame.shape
        LINE_Y = int(altura * 0.5)

        results = model.track(frame, persist=True, conf=0.4, imgsz=640, classes=[0], verbose=False)

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)

            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = map(int, box)
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                estado_atual = 'fora' if cy > LINE_Y else 'dentro'

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

                historico_posicoes[track_id] = estado_atual

    cap.release()

    processados.add(arquivo)
    salvar_processados()


class NovoVideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(EXTENSOES):
            fila_videos.put(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        if event.dest_path.lower().endswith(EXTENSOES):
            fila_videos.put(event.dest_path)


def worker():
    while True:
        try:
            caminho = fila_videos.get(timeout=2)
        except Empty:
            continue

        arquivo = os.path.basename(caminho)
        if arquivo in processados:
            fila_videos.task_done()
            continue

        if not os.path.exists(caminho):
            fila_videos.task_done()
            continue

        if not arquivo_estavel(caminho):
            print(f"[AVISO] Arquivo não estabilizou, reenfileirando: {arquivo}")
            fila_videos.put(caminho)
            time.sleep(2)
            fila_videos.task_done()
            continue

        processar_video(caminho)
        fila_videos.task_done()


def main():
    global _token, processados

    try:
        _token = obter_token()
    except RuntimeError as e:
        print(f"[ERRO CRÍTICO] {e}")
        exit(1)

    processados = carregar_processados()

    for arquivo in os.listdir(PASTA_VIDEOS):
        if arquivo.lower().endswith(EXTENSOES) and arquivo not in processados:
            fila_videos.put(os.path.join(PASTA_VIDEOS, arquivo))

    Thread(target=worker, daemon=True).start()

    observer = Observer()
    observer.schedule(NovoVideoHandler(), PASTA_VIDEOS, recursive=False)
    observer.start()

    print(f"[SERVIÇO] Monitorando {PASTA_VIDEOS} continuamente...")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()