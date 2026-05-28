import cv2
import os
import torch
import logging
from ultralytics import YOLO
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== CONFIGURAÇÕES ====================
PASTA_BASE = r"C:\Users\matheus-lopes\Desktop\Gravacao 2904 - 0705\C1"
FPS_SAIDA = 20
MIN_FRAMES = 15
BUFFER_FRAMES = 10
PASTAS = ["1", "2", "3", "4"]

CONF_IA = 0.45

# ================= SELEÇÃO DE HARDWARE =================
USAR_GPU = False  # Mude para True se tiver acesso à GPU dedicada de 20GB

if USAR_GPU:
    MAX_WORKERS = 6
    DEVICE_IA = 0
else:
    MAX_WORKERS = 2    # Reduzido na CPU para não fritar o processador em 1280px
    DEVICE_IA = "cpu"
    # Otimizações exclusivas para execução em CPU
    torch.set_num_threads(4)

MANTER_RESOLUCAO_ORIGINAL = True
# =======================================================

logging.basicConfig(
    filename=os.path.join(PASTA_BASE, "processamento_clips.txt"),
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    encoding="utf-8"
)

cv2.setUseOptimized(True)

def processar_video(nome_pasta, video):
    caminho_pasta = os.path.join(PASTA_BASE, nome_pasta)
    caminho_video = os.path.join(caminho_pasta, video)
    OUTPUT_DIR = os.path.join(PASTA_BASE, f"clips_{nome_pasta}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[{nome_pasta}] Iniciando: {video}")
    logging.info(f"[{nome_pasta}] Iniciando: {video}")

    cap = cv2.VideoCapture(caminho_video)
    if not cap.isOpened():
        print(f"[{nome_pasta}] ERRO AO ABRIR: {video}")
        return

    # CORREÇÃO: Modelo carregado por thread para evitar erros de concorrência na memória
    model_local = YOLO("yolo11n.pt")

    gravando = False
    frames_sem_pessoa = 0
    frames_com_pessoa = 0
    out = None
    clip_count = 1

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model_local.predict(
                source=frame,
                imgsz=1280,
                conf=CONF_IA,
                classes=[0],
                verbose=False,
                device=DEVICE_IA
            )

            pessoa_detectada = False
            r = results[0]

            if r.boxes is not None and len(r.boxes) > 0:
                pessoa_detectada = True

            if pessoa_detectada:
                frames_com_pessoa += 1
                frames_sem_pessoa = 0

                if not gravando:
                    h, w = frame.shape[:2]
                    nome_arquivo = os.path.join(
                        OUTPUT_DIR,
                        f"{os.path.splitext(video)[0]}_clipe___{clip_count:07d}.mp4"
                    )
                    out = cv2.VideoWriter(
                        nome_arquivo,
                        cv2.VideoWriter_fourcc(*"mp4v"),
                        FPS_SAIDA,
                        (w, h)
                    )
                    gravando = True

                out.write(frame)

            else:
                if gravando:
                    frames_sem_pessoa += 1

                    if frames_sem_pessoa <= BUFFER_FRAMES:
                        out.write(frame)
                    else:
                        if frames_com_pessoa >= MIN_FRAMES:
                            logging.info(f"[{nome_pasta}] CLIP {clip_count} SALVO | VIDEO={video}")
                            clip_count += 1
                        else:
                            try:
                                out.release()
                                os.remove(nome_arquivo)
                            except:
                                pass

                        if out is not None:
                            out.release()

                        out = None
                        gravando = False
                        frames_com_pessoa = 0
                        frames_sem_pessoa = 0
    finally:
        # Garante o fechamento dos arquivos mesmo se houver erro crítico no laço
        cap.release()
        if out is not None:
            out.release()
            if frames_com_pessoa < MIN_FRAMES:
                try:
                    os.remove(nome_arquivo)
                except:
                    pass

    print(f"[{nome_pasta}] Finalizado: {video}")

if __name__ == "__main__":
    print(f"\n🚀 ALOCANDO HARDWARE... MODO: {'GPU' if USAR_GPU else 'CPU'}")
    print("MAPEANDO ARQUIVOS DE VÍDEO...")
    tarefas = []

    for pasta in PASTAS:
        caminho_pasta = os.path.join(PASTA_BASE, pasta)
        if not os.path.exists(caminho_pasta):
            continue

        videos = sorted([
            f for f in os.listdir(caminho_pasta)
            if f.lower().endswith((".mp4", ".mkv", ".avi", ".mov"))
        ])

        for video in videos:
            tarefas.append((pasta, video))

    print(f"TOTAL DE VÍDEOS ENCONTRADOS: {len(tarefas)}")
    print(f"PROCESSANDO COM MAX_WORKERS={MAX_WORKERS}... AGUARDE.")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(processar_video, pasta, video)
            for pasta, video in tarefas
        ]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Erro em uma das threads: {e}")

    print("\n🏁 PROCESSO TOTAL DE CORTE CONCLUÍDO!")