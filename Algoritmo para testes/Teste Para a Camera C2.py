# Teste Para a Camera C1 Sem Mandar para o Servidor, Apenas para Conferir a Contagem Localmente

import os
import cv2
import re
from ultralytics import YOLO
from datetime import datetime

# ==========================================
# FUNÇÃO AUXILIAR PARA LINHAS INCLINADAS
# ==========================================
def calcular_posicao_linha(cx, cy, pt1, pt2):
    x1, y1 = pt1
    x2, y2 = pt2
    return (x2 - x1) * (cy - y1) - (y2 - y1) * (cx - x1)

# ==========================================
# MODELO E PASTAS
# ==========================================
model = YOLO("yolo11s.pt")

pastas_videos = [
    r"C:\Users\eduardo-heck\Desktop\videos"
]

extensoes = (".mp4", ".avi", ".mkv", ".mov")

pasta_script = os.path.dirname(os.path.abspath(__file__))
pasta_logs = os.path.join(pasta_script, "logs")
os.makedirs(pasta_logs, exist_ok=True)

# ==========================================
# PROCESSAMENTO
# ==========================================
for pasta_videos in pastas_videos:

    print(f"\n======== PASTA: {pasta_videos} ========")

    if not os.path.exists(pasta_videos):
        print("Pasta não encontrada.")
        continue

    nome_pasta = os.path.basename(pasta_videos)

    arquivo_saida = os.path.join(pasta_logs, f"log_{nome_pasta}.txt")
    arquivo_resumo = os.path.join(pasta_logs, f"resumo_{nome_pasta}.txt")

    dados_resumo_pasta = {}

    # LOG INICIAL
    with open(arquivo_saida, "a", encoding="utf-8") as relatorio:
        relatorio.write("\n" + "="*60 + "\n")
        relatorio.write(f"INICIO PROCESSAMENTO - {datetime.now()}\n")
        relatorio.write("="*60 + "\n\n")

    for arquivo in os.listdir(pasta_videos):

        if not arquivo.lower().endswith(extensoes):
            continue

        caminho = os.path.join(pasta_videos, arquivo)

        print(f"\nProcessando: {arquivo}")

        cap = cv2.VideoCapture(caminho)

        if not cap.isOpened():
            print(f"Erro ao abrir: {arquivo}")
            continue

        cv2.namedWindow("Contagem", cv2.WINDOW_NORMAL)

        historico_posicoes = {}
        entradas = 0
        saidas = 0
        frame_count = 0

        while True:

            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            altura, largura, _ = frame.shape

            L1_PT1 = (int(largura * 0.03), int(altura * 0.50))
            L1_PT2 = (int(largura * 0.99), int(altura * 0.80))

            L2_PT1 = (int(largura * 0.10), int(altura * 0.28))
            L2_PT2 = (int(largura * 0.67), int(altura * 0.36))

            results = model.track(
                frame,
                persist=True,
                tracker="botsort.yaml",
                conf=0.5,
                imgsz=640,
                classes=[0],
                verbose=False
            )

            if results[0].boxes is not None and results[0].boxes.id is not None:

                boxes = results[0].boxes.xyxy.cpu().numpy()
                ids = results[0].boxes.id.cpu().numpy().astype(int)

                for box, track_id in zip(boxes, ids):

                    x1, y1, x2, y2 = map(int, box)
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2

                    passou_L1 = calcular_posicao_linha(cx, cy, L1_PT1, L1_PT2) < 0
                    passou_L2 = calcular_posicao_linha(cx, cy, L2_PT1, L2_PT2) < 0

                    if not passou_L1 and not passou_L2:
                        estado_atual = "dentro"
                    elif passou_L1 and not passou_L2:
                        estado_atual = "meio"
                    elif passou_L1 and passou_L2:
                        estado_atual = "fora"
                    else:
                        estado_atual = "invalido"

                    if track_id not in historico_posicoes:
                        historico_posicoes[track_id] = [estado_atual]
                    else:
                        ultimo_estado = historico_posicoes[track_id][-1]

                        if estado_atual != ultimo_estado and estado_atual != "invalido":

                            historico_posicoes[track_id].append(estado_atual)

                            if len(historico_posicoes[track_id]) > 3:
                                historico_posicoes[track_id].pop(0)

                            seq = historico_posicoes[track_id]

                            if seq == ["fora", "meio", "dentro"]:
                                entradas += 1
                                print(f">>> ENTRADA ID {track_id}")

                            elif seq == ["dentro", "meio", "fora"]:
                                saidas += 1
                                print(f">>> SAÍDA ID {track_id}")

                    # VISUALIZAÇÃO
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    cv2.putText(frame, f"ID {track_id}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # LINHAS
            cv2.line(frame, L1_PT1, L1_PT2, (255, 0, 0), 2)
            cv2.line(frame, L2_PT1, L2_PT2, (0, 255, 255), 2)

            cv2.putText(frame,
                        f"Entradas: {entradas} | Saidas: {saidas}",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2)

            # MOSTRAR VÍDEO
            cv2.imshow("Contagem", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        cap.release()

        # LOG FINAL
        linha = f"{arquivo}: Entradas={entradas} | Saidas={saidas}"
        print(linha)

        with open(arquivo_saida, "a", encoding="utf-8") as relatorio:
            relatorio.write(f"{linha}\n")

        prefixo_video = re.sub(r'_clipe___\d+', '', os.path.splitext(arquivo)[0])

        if prefixo_video not in dados_resumo_pasta:
            dados_resumo_pasta[prefixo_video] = {"entradas": 0, "saidas": 0}

        dados_resumo_pasta[prefixo_video]["entradas"] += entradas
        dados_resumo_pasta[prefixo_video]["saidas"] += saidas

# ==========================================
# FINALIZAÇÃO
# ==========================================
cv2.destroyAllWindows()
print("\nProcessamento finalizado.")