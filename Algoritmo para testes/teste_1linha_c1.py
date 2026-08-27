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
        r"D:\Projeto\videos"
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
    # GABARITO (caminho fixo)
    # ==========================================

    

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
            pasta_logs,
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

                                # Entrada
                                if (
                                    estado_anterior == "fora"
                                    and estado_atual == "dentro"
                                ):

                                    entradas += 1

                                    print(
                                        f">>> [ID {track_id}] Entrada"
                                    )

                                # Saída
                                elif (
                                    estado_anterior == "dentro"
                                    and estado_atual == "fora"
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

                # Extrai o prefixo removendo o sufixo do clipe para o relatório resumido
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


    # ==========================================
    # VALIDAÇÃO AUTOMÁTICA
    # ==========================================

    def _parse_manual(caminho_manual):
        """
        Lê o gabarito manual e retorna:
            { nome_normalizado: {"entradas": int, "saidas": int} }

        Formatos aceitos por linha:
            nome:Entradas:N Saidas:M
            nome:Entradas:N
            nome:Saidas:M
            nome:              → 0 / 0
            nome               → 0 / 0
        Linhas vazias e comentários (#) são ignorados.
        """
        dados = {}

        with open(caminho_manual, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()

                if not linha or linha.startswith("#"):
                    continue

                partes = linha.split(":", 1)
                nome   = os.path.splitext(partes[0].strip())[0]

                if not nome:
                    continue

                entradas = 0
                saidas   = 0

                if len(partes) > 1:
                    resto   = partes[1]
                    match_e = re.search(r'Entradas\s*:\s*(\d+)', resto, re.IGNORECASE)
                    match_s = re.search(r'Saidas\s*:\s*(\d+)',   resto, re.IGNORECASE)

                    if match_e:
                        entradas = int(match_e.group(1))
                    if match_s:
                        saidas = int(match_s.group(1))

                dados[nome] = {"entradas": entradas, "saidas": saidas}

        return dados


    def _parse_log(caminho_log):
        """
        Lê o log gerado pelo script e retorna:
            { nome_normalizado: {"entradas": int, "saidas": int} }

        Formato esperado:
            nome_video.mp4: Entradas=N | Saidas=M
        Linhas que não casem com o padrão são ignoradas.
        """
        dados  = {}
        padrao = re.compile(
            r'^(?P<nome>.+?)\s*:\s*Entradas=(?P<e>\d+)\s*\|\s*Saidas=(?P<s>\d+)',
            re.IGNORECASE
        )

        with open(caminho_log, "r", encoding="utf-8") as f:
            for linha in f:
                m = padrao.match(linha.strip())

                if not m:
                    continue

                nome     = os.path.splitext(m.group("nome").strip())[0]
                entradas = int(m.group("e"))
                saidas   = int(m.group("s"))

                dados[nome] = {"entradas": entradas, "saidas": saidas}

        return dados


    def _log_mais_recente(pasta_logs):
        """Retorna o log_*.txt modificado mais recentemente, ou None."""
        candidatos = [
            os.path.join(pasta_logs, f)
            for f in os.listdir(pasta_logs)
            if f.startswith("log_") and f.endswith(".txt")
        ]

        return max(candidatos, key=os.path.getmtime) if candidatos else None


    def validar_contagem(arquivo_manual, pasta_logs):
        """
        Compara o gabarito manual com o log mais recente e grava comparacao.txt.

        Vídeos presentes em apenas um dos lados são registrados como ERRO
        com valores zerados no lado faltante.
        """
        SEPARADOR = "=" * 50

        # --- gabarito ausente: avisa e encerra sem criar arquivo ---
        if not os.path.exists(arquivo_manual):
            print(
                f"\n[VALIDAÇÃO] Arquivo manual não encontrado: {arquivo_manual}\n"
                "            Encerrando sem gerar comparação."
            )
            return

        # --- log ausente ---
        caminho_log = _log_mais_recente(pasta_logs)

        if caminho_log is None:
            print(
                f"\n[VALIDAÇÃO] Nenhum log_*.txt encontrado em {pasta_logs}.\n"
                "            Encerrando sem gerar comparação."
            )
            return

        print(f"\n[VALIDAÇÃO] Usando log: {os.path.basename(caminho_log)}")

        manual = _parse_manual(arquivo_manual)
        script = _parse_log(caminho_log)

        todos = sorted(set(manual.keys()) | set(script.keys()))

        # --- contadores ---
        total_comparados = 0
        total_ok         = 0
        total_erro       = 0
        soma_e_manual    = 0
        soma_s_manual    = 0
        soma_e_script    = 0
        soma_s_script    = 0

        blocos = []

        for video in todos:
            total_comparados += 1

            e_m = manual[video]["entradas"] if video in manual else 0
            s_m = manual[video]["saidas"]   if video in manual else 0
            e_s = script[video]["entradas"] if video in script else 0
            s_s = script[video]["saidas"]   if video in script else 0

            soma_e_manual += e_m
            soma_s_manual += s_m
            soma_e_script += e_s
            soma_s_script += s_s

            diff_e = e_s - e_m
            diff_s = s_s - s_m

            status = "OK" if (diff_e == 0 and diff_s == 0) else "ERRO"

            ausencia = ""
            if video not in manual:
                ausencia = "  [AUSENTE NO MANUAL — valores zerados]\n"
            elif video not in script:
                ausencia = "  [AUSENTE NO SCRIPT — valores zerados]\n"

            if status == "OK" and not ausencia:
                total_ok += 1
                blocos.append(
                    f"{SEPARADOR}\n"
                    f"VIDEO: {video}\n"
                    f"STATUS: OK\n"
                )
            else:
                total_erro += 1
                blocos.append(
                    f"{SEPARADOR}\n"
                    f"VIDEO: {video}\n"
                    f"{ausencia}"
                    f"MANUAL    Entradas: {e_m}  Saidas: {s_m}\n"
                    f"SCRIPT    Entradas: {e_s}  Saidas: {s_s}\n"
                    f"DIFERENCA Entradas: {diff_e:+d}  Saidas: {diff_s:+d}\n"
                    f"STATUS: ERRO\n"
                )

        diff_total_e = soma_e_script - soma_e_manual
        diff_total_s = soma_s_script - soma_s_manual

        arquivo_comparacao = os.path.join(pasta_logs, "comparacao.txt")

        with open(arquivo_comparacao, "w", encoding="utf-8") as f:

            f.write("COMPARACAO MANUAL x SCRIPT\n\n")

            for bloco in blocos:
                f.write(bloco + "\n")

            f.write(f"{SEPARADOR}\n")
            f.write("RESUMO\n\n")
            f.write(f"Videos comparados      : {total_comparados}\n")
            f.write(f"Acertos (OK)           : {total_ok}\n")
            f.write(f"Erros                  : {total_erro}\n")
            f.write("\n")
            f.write(f"Total entradas  MANUAL : {soma_e_manual}\n")
            f.write(f"Total entradas  SCRIPT : {soma_e_script}\n")
            f.write(f"Diferenca entradas     : {diff_total_e:+d}\n")
            f.write("\n")
            f.write(f"Total saidas    MANUAL : {soma_s_manual}\n")
            f.write(f"Total saidas    SCRIPT : {soma_s_script}\n")
            f.write(f"Diferenca saidas       : {diff_total_s:+d}\n")
            f.write(f"{SEPARADOR}\n")

        print(
            f"[VALIDAÇÃO] comparacao.txt gerado em: {arquivo_comparacao}\n"
            f"            Comparados={total_comparados} | "
            f"OK={total_ok} | "
            f"ERRO={total_erro}"
        )


    # Executa a validação ao final do script
    validar_contagem(arquivo_manual, pasta_logs)