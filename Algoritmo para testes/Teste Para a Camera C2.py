# Teste Para a Camera C1 Sem  Mandar para o Servidor, Apenas para Conferir a Contagem Localmente
# Baseado no testeC1.py, mas sem enviar os dados para o servidor e com logs locais para conferência

import os
import cv2
import re
from ultralytics import YOLO

# ==========================================
# MODELO
# ==========================================

model = YOLO("yolo11s.pt")

# ==========================================
# PASTAS DOS VÍDEOS
# ==========================================

pastas_videos = [
    r"C:\Users\eduardo-heck\Desktop\Gravacao - 2904 - 0705\C2\clips_1",
    r"C:\Users\eduardo-heck\Desktop\Gravacao - 2904 - 0705\C2\clips_2",
    r"C:\Users\eduardo-heck\Desktop\Gravacao - 2904 - 0705\C2\clips_3",
    r"C:\Users\eduardo-heck\Desktop\Gravacao - 2904 - 0705\C2\clips_4"
]

extensoes = (
    ".mp4",
    ".avi",
    ".mkv",
    ".mov"
)

# ==========================================
# PASTA DOS LOGS
# ==========================================

pasta_script = os.path.dirname(os.path.abspath(__file__))

pasta_logs = os.path.join(
    pasta_script,
    "logs"
)

# Cria pasta logs se não existir
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

    arquivo_saida = os.path.join(
        pasta_logs
        ,
        f"log_{nome_pasta}.txt"
    )

    arquivo_resumo = os.path.join(
        pasta_logs,
        f"resumo_{nome_pasta}.txt"
    )

    # Dicionário temporário para acumular os dados consolidados do resumo da pasta atual
    dados_resumo_pasta = {}

    # Cria o TXT se não existir
    if not os.path.exists(arquivo_saida):

        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write(
                f"RELATORIO DA PASTA {nome_pasta}\n\n"
            )

    with open(arquivo_saida, "a", encoding="utf-8") as relatorio:

        for arquivo in os.listdir(pasta_videos):

            if not arquivo.lower().endswith(extensoes):
                continue

            caminho = os.path.join(pasta_videos, arquivo)

            print(f"\nProcessando: {arquivo}")

            cap = cv2.VideoCapture(caminho)

            if not cap.isOpened():
                print(f"Erro ao abrir: {arquivo}")
                continue

            historico_posicoes = {}

            entradas = 0
            saidas = 0

            frame_count = 0

            while True:

                ret, frame = cap.read()

                if not ret:
                    break

                frame_count += 1

                # Processa metade dos frames
                if frame_count % 2 != 0:
                    continue

                altura, largura, _ = frame.shape

                LINE_Y = int(altura * 0.5)

                # ==========================================
                # TRACKING
                # ==========================================

                results = model.track(
                    frame,
                    persist=True,
                    tracker="botsort.yaml",
                    conf=0.5,
                    imgsz=640,
                    classes=[0],
                    verbose=False
                )

                if (
                    results[0].boxes is not None
                    and results[0].boxes.id is not None
                ):

                    boxes = (
                        results[0]
                        .boxes
                        .xyxy
                        .cpu()
                        .numpy()
                    )

                    ids = (
                        results[0]
                        .boxes
                        .id
                        .cpu()
                        .numpy()
                        .astype(int)
                    )

                    for box, track_id in zip(boxes, ids):

                        x1, y1, x2, y2 = map(int, box)

                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)

                        estado_atual = (
                            "fora"
                            if cy > LINE_Y
                            else "dentro"
                        )

                        if track_id in historico_posicoes:

                            estado_anterior = (
                                historico_posicoes[track_id]
                            )

                            # Entrada (invertida)
                            if (
                                estado_anterior == "dentro"
                                and estado_atual == "fora"
                            ):

                                entradas += 1

                                print(
                                    f">>> [ID {track_id}] Entrada"
                                )

                            # Saída (invertida)
                            elif (
                                estado_anterior == "fora"
                                and estado_atual == "dentro"
                            ):

                                saidas += 1

                                print(
                                    f">>> [ID {track_id}] Saída"
                                )

                        historico_posicoes[track_id] = estado_atual

                        # ==========================================
                        # VISUAL
                        # ==========================================

                        cv2.rectangle(
                            frame,
                            (x1, y1),
                            (x2, y2),
                            (0, 255, 0),
                            2
                        )

                        cv2.circle(
                            frame,
                            (cx, cy),
                            4,
                            (0, 255, 0),
                            -1
                        )

                        cv2.putText(
                            frame,
                            f"ID {track_id}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2
                        )

                # ==========================================
                # LINHA
                # ==========================================

                cv2.line(
                    frame,
                    (0, LINE_Y),
                    (largura, LINE_Y),
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    f"Entradas: {entradas} | Saidas: {saidas}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

                # ==========================================
                # MOSTRA VIDEO
                # ==========================================

                cv2.imshow("Contagem", frame)

                # Q = próximo vídeo
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()

            # ==========================================
            # SALVA RESULTADO
            # ==========================================

            linha = (
                f"{arquivo}: "
                f"Entradas={entradas} | "
                f"Saidas={saidas}\n"
            )

            relatorio.write(linha)

            print(f"\n{linha.strip()}")

            # Lógica Adicional: Extrai o prefixo removendo o sufixo do clipe para o relatório resumido
            # Exemplo: "tapo_2026-04-29_17-05-29_clipe___0000001.mp4" vira "tapo_2026-04-29_17-05-29"
            prefixo_video = re.sub(r'_clipe___\d+', '', os.path.splitext(arquivo)[0])
            
            if prefixo_video not in dados_resumo_pasta:
                dados_resumo_pasta[prefixo_video] = {"entradas": 0, "saidas": 0}
                
            dados_resumo_pasta[prefixo_video]["entradas"] += entradas
            dados_resumo_pasta[prefixo_video]["saidas"] += saidas

    # Salva o arquivo de resumo consolidado da pasta caso dados tenham sido coletados
    if dados_resumo_pasta:
        with open(arquivo_resumo, "w", encoding="utf-8") as resumo_file:
            resumo_file.write(f"RESUMO CONSOLIDADO DA PASTA {nome_pasta}\n\n")
            for prefixo, totais in dados_resumo_pasta.items():
                resumo_file.write(
                    f"{prefixo}: Entradas={totais['entradas']} | Saidas={totais['saidas']}\n"
                )

# ==========================================
# FINALIZAÇÃO
# ==========================================

cv2.destroyAllWindows()

print("\nProcessamento finalizado.")