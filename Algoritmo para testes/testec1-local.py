import os
import time
import json
import cv2
import torch
import requests
from queue import Queue, Empty
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ultralytics import YOLO

# ==========================================
# CONFIGURAÇÕES DE PERFORMANCE
# ==========================================
YOLO_MODEL = "yolov8n.pt"
USE_GPU = False
USE_HALF_PRECISION = True   # FP16 - só tem efeito em GPU
IMG_SIZE = 640
CONFIDENCE = 0.4

# Em vez de rodar o YOLO em 100% dos frames, processa 1 a cada N.
# Ex.: vídeo a 25 fps com TARGET_PROCESS_FPS = 5 -> FRAME_SKIP = 5
TARGET_PROCESS_FPS = 3.0

PASTA_VIDEOS = r"D:\Projeto/videos"
EXTENSOES = ('.mp4', '.avi', '.mkv', '.mov')
ARQUIVO_PROCESSADOS = os.path.join(PASTA_VIDEOS, ".processados.json")








model = YOLO(YOLO_MODEL)
def _calcular_frame_skip(cap: cv2.VideoCapture) -> int:
    """Determina de quantos em quantos frames rodar o YOLO, baseado no FPS real do vídeo."""
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if not video_fps or video_fps <= 0:
        video_fps = 25.0  # fallback razoável

    if TARGET_PROCESS_FPS <= 0:
        return 1  # processa todos os frames

    skip = max(1, round(video_fps / TARGET_PROCESS_FPS))
    return skip


def processar_video(caminho):
    arquivo = os.path.basename(caminho)
    print(f"\nProcessando: {arquivo}")

    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        print("Erro ao abrir:", arquivo)
        return

    frame_skip = _calcular_frame_skip(cap)
    print(f"[Perf] Frame skip = {frame_skip} (1 a cada {frame_skip} frames será analisado)")

    historico_posicoes = {}
    entradas = 0
    saidas = 0
    frame_idx = -1

    t_inicio = time.monotonic()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Pula frames para reduzir custo de inferência.
        # OBS: como o rastreamento (track) depende de continuidade entre frames,
        # pular frames reduz um pouco a precisão de reidentificação, mas em troca
        # de um ganho grande de velocidade — assim como já é feito no YOLOThread
        # do sistema de captura em tempo real (TARGET_YOLO_FPS).
        if frame_idx % frame_skip != 0:
            continue

        altura, largura, _ = frame.shape
        LINE_Y = int(altura * 0.5)

        results = model.track(
            frame,
            persist=True,
            conf=CONFIDENCE,
            imgsz=IMG_SIZE,
            classes=[0], 
            verbose=False,
            
        )
        frame_desenhado = results[0].plot()


        cv2.imshow("YOLO Tracking", frame_desenhado)
        

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
    processar_video(r"D:\Projeto\videos\clip_20260821_001325.mp4")