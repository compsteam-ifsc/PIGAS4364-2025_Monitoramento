import os
import json
import time
import logging
from queue import Queue, Empty
from threading import Thread, Event

import cv2
import requests
from requests.adapters import HTTPAdapter, Retry
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ultralytics import YOLO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("monitor_videos")

logging.getLogger("ultralytics").setLevel(logging.ERROR)


class Config:
    def __init__(self):
        self.yolo_model = "yolo11s.pt"
        self.use_gpu = False
        self.use_half_precision = True
        self.img_size = 640
        self.confidence = 0.4

        self.pasta_videos = r"D:\videos"
        self.extensoes = (".mp4", ".avi", ".mkv", ".mov")
        self.max_tentativas_estabilidade = 3

        self.inverter_direcao_contagem = False

        self.base_url = "http://127.0.0.1:8080"
        self.admin_usuario = "root"
        self.admin_senha = "1010"

        self.arquivo_processados = os.path.join(
            self.pasta_videos,
            ".processados.json"
        )
        self.url_login = f"{self.base_url}/api/auth/login"
        self.url_relatorio = f"{self.base_url}/api/relatorio"

        self.max_tentativas_envio = 3
        self.backoff_base_envio = 1.5


CFG = Config()


class ApiClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self._token = None
        self._session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504]
        )

        self._session.mount(
            "http://",
            HTTPAdapter(max_retries=retries)
        )
        self._session.mount(
            "https://",
            HTTPAdapter(max_retries=retries)
        )

        self.fila_eventos = Queue()
        self._worker_envio = None

    def autenticar(self):
        log.info("Autenticando na API...")

        try:
            resp = self._session.post(
                self.cfg.url_login,
                json={
                    "usuario": self.cfg.admin_usuario,
                    "senha": self.cfg.admin_senha
                },
                timeout=5,
            )

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Erro na conexão de autenticação: {e}"
            ) from e

        if resp.status_code != 200:
            raise RuntimeError(
                f"Status {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        self._token = data.get("token")

        log.info(
            "Token obtido com sucesso (role: %s)",
            data.get("role")
        )

    def enfileirar(self, tipo):
        self.fila_eventos.put(tipo)

        log.info(
            "Evento %s colocado na fila (tamanho atual: %d)",
            tipo,
            self.fila_eventos.qsize()
        )

    def _enviar_sincrono(self, tipo, retry=True):
        headers = {
            "Authorization": f"Bearer {self._token}"
        }

        try:
            r = self._session.post(
                self.cfg.url_relatorio,
                json={
                    "saidaEntrada": tipo
                },
                headers=headers,
                timeout=10,
            )

        except requests.exceptions.Timeout:
            log.error(
                "Timeout ao enviar %s para a API.",
                tipo
            )
            return False

        except requests.exceptions.RequestException as e:
            log.error(
                "Erro de conexão ao enviar %s: %s",
                tipo,
                e
            )
            return False

        if r.status_code in (200, 201):
            log.info(
                "%s enviado com sucesso -> status %s",
                tipo,
                r.status_code
            )
            return True

        if r.status_code == 401 and retry:
            log.warning(
                "Token expirado, renovando..."
            )

            try:
                self.autenticar()

            except RuntimeError as e:
                log.error(
                    "Falha ao renovar token: %s",
                    e
                )
                return False

            return self._enviar_sincrono(
                tipo,
                retry=False
            )

        log.error(
            "Erro no backend ao enviar %s: status %s - %s",
            tipo,
            r.status_code,
            r.text
        )

        return False

    def iniciar_worker(self, parar_event):
        def _worker():
            while True:
                try:
                    tipo = self.fila_eventos.get(
                        timeout=1
                    )

                except Empty:
                    if parar_event.is_set():
                        break
                    continue

                sucesso = False
                tentativa = 0

                while (
                    not sucesso
                    and tentativa
                    < self.cfg.max_tentativas_envio
                ):
                    tentativa += 1

                    sucesso = self._enviar_sincrono(
                        tipo
                    )

                    if (
                        not sucesso
                        and tentativa
                        < self.cfg.max_tentativas_envio
                    ):
                        espera = (
                            self.cfg.backoff_base_envio
                            * tentativa
                        )

                        log.warning(
                            "Falha ao enviar %s "
                            "(tentativa %d/%d). "
                            "Nova tentativa em %.1fs...",
                            tipo,
                            tentativa,
                            self.cfg.max_tentativas_envio,
                            espera,
                        )

                        time.sleep(espera)

                if not sucesso:
                    log.error(
                        "Falha definitiva ao enviar %s "
                        "após %d tentativas. "
                        "Evento descartado.",
                        tipo,
                        tentativa,
                    )

                self.fila_eventos.task_done()

        self._worker_envio = Thread(
            target=_worker,
            daemon=True,
            name="EnvioEventosThread"
        )

        self._worker_envio.start()

        log.info(
            "Worker de envio de eventos iniciado."
        )

    def aguardar_fila_eventos(self):
        pendentes = self.fila_eventos.qsize()

        if pendentes:
            log.info(
                "Aguardando %d evento(s) pendente(s) "
                "na fila antes de encerrar...",
                pendentes
            )

        self.fila_eventos.join()

        log.info(
            "Fila de eventos esvaziada."
        )


class RegistroProcessados:
    def __init__(self, caminho):
        self.caminho = caminho
        self._itens = self._carregar()

    def _carregar(self):
        if os.path.exists(self.caminho):
            try:
                with open(
                    self.caminho,
                    "r",
                    encoding="utf-8"
                ) as f:
                    return set(json.load(f))

            except (
                json.JSONDecodeError,
                OSError
            ) as e:
                log.warning(
                    "Não foi possível ler %s (%s); "
                    "começando do zero.",
                    self.caminho,
                    e
                )

        return set()

    def contem(self, arquivo):
        return arquivo in self._itens

    def marcar(self, arquivo):
        self._itens.add(arquivo)
        self._salvar()

    def _salvar(self):
        tmp = f"{self.caminho}.tmp"

        try:
            with open(
                tmp,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    sorted(self._itens),
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            os.replace(
                tmp,
                self.caminho
            )

        except OSError as e:
            log.error(
                "Falha ao salvar registro de processados: %s",
                e
            )


def arquivo_estavel(
    caminho,
    checagens=3,
    intervalo=1.0,
    tentativas_max=30
):
    tamanho_anterior = -1
    estavel_count = 0

    for _ in range(tentativas_max):
        try:
            tamanho_atual = os.path.getsize(
                caminho
            )

        except OSError:
            return False

        if (
            tamanho_atual == tamanho_anterior
            and tamanho_atual > 0
        ):
            estavel_count += 1

            if estavel_count >= checagens:
                return True

        else:
            estavel_count = 0

        tamanho_anterior = tamanho_atual

        time.sleep(intervalo)

    return False


class ProcessadorVideo:
    def __init__(self, cfg, api):
        self.cfg = cfg
        self.api = api

        device = (
            "cuda"
            if cfg.use_gpu
            else "cpu"
        )

        half = (
            cfg.use_half_precision
            and device == "cuda"
        )

        log.info(
            "Dispositivo selecionado: %s%s",
            device.upper(),
            " (FP16)" if half else ""
        )

        self.model = YOLO(
            cfg.yolo_model
        )

        self.device = device
        self.half = half

    def processar(self, caminho):
        arquivo = os.path.basename(
            caminho
        )

        log.info("=" * 42)
        log.info(
            "Processando: %s",
            arquivo
        )

        cap = cv2.VideoCapture(
            caminho
        )

        if not cap.isOpened():
            log.error(
                "Não foi possível abrir: %s",
                arquivo
            )
            return False

        try:
            video_fps = (
                cap.get(cv2.CAP_PROP_FPS)
                or 0
            )

            total_frames = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            largura = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_WIDTH
                )
            )

            altura = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_HEIGHT
                )
            )

            duracao = (
                total_frames / video_fps
                if video_fps > 0
                else 0
            )

            log.info(
                "Metadados: FPS=%.2f Frames=%d "
                "Resolução=%dx%d Duração=%.2fs",
                video_fps,
                total_frames,
                largura,
                altura,
                duracao,
            )

            LINE_Y = int(
                altura * 0.5
            )

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

                results = self.model.track(
                    frame,
                    persist=True,
                    tracker="botsort.yaml",
                    conf=self.cfg.confidence,
                    imgsz=self.cfg.img_size,
                    classes=[0],
                    device=self.device,
                    half=self.half,
                    verbose=False,
                )

                if (
                    results
                    and results[0].boxes is not None
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

                    for box, track_id in zip(
                        boxes,
                        ids
                    ):
                        x1, y1, x2, y2 = map(
                            int,
                            box
                        )

                        cx = int(
                            (x1 + x2) / 2
                        )

                        cy = int(
                            (y1 + y2) / 2
                        )

                        estado_atual = (
                            "fora"
                            if cy > LINE_Y
                            else "dentro"
                        )

                        if (
                            track_id
                            in historico_posicoes
                        ):
                            estado_anterior = (
                                historico_posicoes[
                                    track_id
                                ]
                            )

                            if (
                                estado_anterior
                                == "fora"
                                and estado_atual
                                == "dentro"
                            ):
                                entradas += 1

                                log.info(
                                    "Entrada detectada | "
                                    "ID %d | frame %d | %.2fs",
                                    track_id,
                                    frame_idx,
                                    (
                                        frame_idx
                                        / video_fps
                                        if video_fps > 0
                                        else 0
                                    ),
                                )

                                if (
                                    self.cfg
                                    .inverter_direcao_contagem
                                ):
                                    self.api.enfileirar(
                                        "SAIDA"
                                    )
                                else:
                                    self.api.enfileirar(
                                        "ENTRADA"
                                    )

                            elif (
                                estado_anterior
                                == "dentro"
                                and estado_atual
                                == "fora"
                            ):
                                saidas += 1

                                log.info(
                                    "Saída detectada | "
                                    "ID %d | frame %d | %.2fs",
                                    track_id,
                                    frame_idx,
                                    (
                                        frame_idx
                                        / video_fps
                                        if video_fps > 0
                                        else 0
                                    ),
                                )

                                if (
                                    self.cfg
                                    .inverter_direcao_contagem
                                ):
                                    self.api.enfileirar(
                                        "ENTRADA"
                                    )
                                else:
                                    self.api.enfileirar(
                                        "SAIDA"
                                    )

                        historico_posicoes[
                            track_id
                        ] = estado_atual

            duracao_processamento = (
                time.monotonic()
                - t_inicio
            )

            log.info(
                "Concluído: %s | entradas=%d "
                "saídas=%d tempo=%.1fs",
                arquivo,
                entradas,
                saidas,
                duracao_processamento,
            )

            return True

        except Exception:
            log.exception(
                "Falha ao processar %s",
                arquivo
            )
            return False

        finally:
            cap.release()


class NovoVideoHandler(
    FileSystemEventHandler
):
    def __init__(
        self,
        fila,
        extensoes
    ):
        self.fila = fila
        self.extensoes = extensoes

    def on_created(self, event):
        if (
            not event.is_directory
            and event.src_path
            .lower()
            .endswith(self.extensoes)
        ):
            self.fila.put(
                event.src_path
            )

    def on_moved(self, event):
        if (
            not event.is_directory
            and event.dest_path
            .lower()
            .endswith(self.extensoes)
        ):
            self.fila.put(
                event.dest_path
            )


def worker(
    fila,
    registro,
    processador,
    parar,
    cfg
):
    tentativas_instabilidade = {}
    ultimo_log = time.monotonic()

    while not parar.is_set():
        try:
            caminho = fila.get(
                timeout=2
            )

        except Empty:
            if (
                time.monotonic()
                - ultimo_log
                >= 30
            ):
                log.info(
                    "Nenhum vídeo novo"
                )

                ultimo_log = time.monotonic()

            continue

        arquivo = os.path.basename(
            caminho
        )

        if (
            registro.contem(arquivo)
            or not os.path.exists(caminho)
        ):
            fila.task_done()
            continue

        if not arquivo_estavel(
            caminho
        ):
            tentativas_instabilidade[
                arquivo
            ] = (
                tentativas_instabilidade.get(
                    arquivo,
                    0
                ) + 1
            )

            if (
                tentativas_instabilidade[
                    arquivo
                ]
                >= cfg.max_tentativas_estabilidade
            ):
                log.error(
                    "Desistindo de %s após %d "
                    "tentativas (arquivo nunca estabilizou).",
                    arquivo,
                    tentativas_instabilidade[
                        arquivo
                    ],
                )

                fila.task_done()
                continue

            log.warning(
                "Arquivo não estabilizou, "
                "reenfileirando: %s (tentativa %d)",
                arquivo,
                tentativas_instabilidade[
                    arquivo
                ],
            )

            fila.put(caminho)
            fila.task_done()
            continue

        sucesso = processador.processar(
            caminho
        )

        if sucesso:
            registro.marcar(
                arquivo
            )

        else:
            log.error(
                "%s não foi marcado como processado; "
                "será tentado novamente na próxima execução.",
                arquivo,
            )

        fila.task_done()


def main():
    cfg = CFG

    api = ApiClient(cfg)
    parar = Event()

    try:
        api.autenticar()

    except RuntimeError as e:
        log.critical(
            "%s",
            e
        )
        raise SystemExit(1)

    api.iniciar_worker(
        parar
    )

    registro = RegistroProcessados(
        cfg.arquivo_processados
    )

    processador = ProcessadorVideo(
        cfg,
        api
    )

    fila = Queue()

    for arquivo in os.listdir(
        cfg.pasta_videos
    ):
        if (
            arquivo.lower().endswith(
                cfg.extensoes
            )
            and not registro.contem(
                arquivo
            )
        ):
            fila.put(
                os.path.join(
                    cfg.pasta_videos,
                    arquivo
                )
            )

    thread_worker = Thread(
        target=worker,
        args=(
            fila,
            registro,
            processador,
            parar,
            cfg,
        ),
        daemon=True,
    )

    thread_worker.start()

    observer = Observer()

    observer.schedule(
        NovoVideoHandler(
            fila,
            cfg.extensoes
        ),
        cfg.pasta_videos,
        recursive=False,
    )

    observer.start()

    log.info(
        "Monitorando %s continuamente...",
        cfg.pasta_videos
    )

    try:
        while True:
            time.sleep(5)

    except KeyboardInterrupt:
        log.info(
            "Encerrando..."
        )

        parar.set()
        observer.stop()

        api.aguardar_fila_eventos()

    observer.join()


if __name__ == "__main__":
    main()