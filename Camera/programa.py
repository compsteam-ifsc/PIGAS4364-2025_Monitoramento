import cv2
import threading
import queue
import time
import os
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from ultralytics import YOLO


RTSP_URL = "rtsp://Projeto:23022010@192.168.0.102:554/stream1"
OUTPUT_DIR = "/media/sf_SLA32/videos"
LOG_DIR = "./logs"
COOLDOWN_TIME = 5.0
YOLO_INFERENCE_INTERVAL = 3
CAPTURE_QUEUE_SIZE = 500
YOLO_QUEUE_SIZE = 5
RTSP_RECONNECT_DELAY = 5.0
VIDEO_FPS = 25.0
VIDEO_CODEC = "mp4v"
VIDEO_EXTENSION = ".mp4"
YOLO_MODEL = "yolov8n.pt"
YOLO_CONFIDENCE = 0.4
YOLO_CLASSES = [0]

def setup_logging(log_dir: str) -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger = logging.getLogger("surveillance")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")
    fh_system = logging.FileHandler(
        os.path.join(log_dir, f"system_{timestamp}.txt"), encoding="utf-8"
    )
    fh_system.setLevel(logging.INFO)
    fh_system.setFormatter(formatter)
    fh_events = logging.FileHandler(
        os.path.join(log_dir, f"events_{timestamp}.txt"), encoding="utf-8"
    )
    fh_events.setLevel(logging.DEBUG)
    fh_events.setFormatter(formatter)
    fh_errors = logging.FileHandler(
        os.path.join(log_dir, f"errors_{timestamp}.txt"), encoding="utf-8"
    )
    fh_errors.setLevel(logging.WARNING)
    fh_errors.setFormatter(formatter)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(fh_system)
    logger.addHandler(fh_events)
    logger.addHandler(fh_errors)
    logger.addHandler(ch)

    return logger

@dataclass
class SharedState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    recording: bool = False
    last_detection_time: float = 0.0
    writer: Optional[cv2.VideoWriter] = None
    current_clip_path: str = ""
    stop_event: threading.Event = field(default_factory=threading.Event)
    frame_size: Optional[tuple] = None
    camera_fps: float = 0.0
    dropped_capture_queue: int = 0
    dropped_yolo_queue: int = 0

class CaptureThread(threading.Thread):

    def __init__(self, rtsp_url: str, capture_queue: queue.Queue,
                 yolo_queue: queue.Queue, state: SharedState,
                 logger: logging.Logger):
        super().__init__(name="CaptureThread", daemon=True)
        self.rtsp_url = rtsp_url
        self.capture_queue = capture_queue
        self.yolo_queue = yolo_queue
        self.state = state
        self.logger = logger
        self.frame_count = 0
        self._fps_counter = 0
        self._fps_window_start = 0.0

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            reported_fps = cap.get(cv2.CAP_PROP_FPS)
            with self.state.lock:
                self.state.frame_size = (w, h)
            self.logger.info(
                f"[Capture] Conectado ao RTSP: {self.rtsp_url} | "
                f"Resolução: {w}x{h} | FPS reportado pela câmera: {reported_fps:.2f}"
            )
            self._fps_counter = 0
            self._fps_window_start = time.time()
            return cap
        cap.release()
        return None

    def _update_real_fps(self):
        self._fps_counter += 1
        elapsed = time.time() - self._fps_window_start
        if elapsed >= 5.0:
            real_fps = self._fps_counter / elapsed
            with self.state.lock:
                self.state.camera_fps = real_fps
            self.logger.info(f"[Capture] FPS real medido: {real_fps:.2f} fps")
            self._fps_counter = 0
            self._fps_window_start = time.time()

    def run(self):
        self.logger.info("[Capture] Thread iniciada.")
        cap = None

        while not self.state.stop_event.is_set():
            if cap is None or not cap.isOpened():
                if cap is not None:
                    cap.release()
                    self.logger.warning("[Capture] RTSP desconectado. Reconectando...")
                cap = self._open_capture()
                if cap is None:
                    self.logger.error(
                        f"[Capture] Falha na conexão RTSP. Tentando em {RTSP_RECONNECT_DELAY}s..."
                    )
                    self.state.stop_event.wait(RTSP_RECONNECT_DELAY)
                    continue

            ret, frame = cap.read()
            if not ret or frame is None:
                self.logger.warning("[Capture] Falha ao ler frame. Reconectando...")
                cap.release()
                cap = None
                continue

            self.frame_count += 1
            self._update_real_fps()
            try:
                self.capture_queue.put_nowait(frame.copy())
            except queue.Full:
                try:
                    self.capture_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self.capture_queue.put_nowait(frame.copy())
                except queue.Full:
                    with self.state.lock:
                        self.state.dropped_capture_queue += 1
            if self.frame_count % YOLO_INFERENCE_INTERVAL == 0:
                try:
                    self.yolo_queue.put_nowait(frame.copy())
                except queue.Full:
                    with self.state.lock:
                        self.state.dropped_yolo_queue += 1

        if cap is not None:
            cap.release()
        self.logger.info("[Capture] Thread encerrada.")

class YOLOThread(threading.Thread):

    def __init__(self, yolo_queue: queue.Queue, state: SharedState,
                 logger: logging.Logger):
        super().__init__(name="YOLOThread", daemon=True)
        self.yolo_queue = yolo_queue
        self.state = state
        self.logger = logger
        self.model = None

    def _load_model(self):
        self.logger.info(f"[YOLO] Carregando modelo: {YOLO_MODEL}")
        self.model = YOLO(YOLO_MODEL)
        self.logger.info("[YOLO] Modelo carregado com sucesso.")

    def run(self):
        self.logger.info("[YOLO] Thread iniciada.")
        try:
            self._load_model()
        except Exception as e:
            self.logger.error(f"[YOLO] Falha ao carregar modelo: {e}")
            return

        while not self.state.stop_event.is_set():
            try:
                frame = self.yolo_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                results = self.model.predict(
                    frame,
                    classes=YOLO_CLASSES,
                    conf=YOLO_CONFIDENCE,
                    verbose=False
                )
                person_detected = False
                for r in results:
                    if r.boxes is not None and len(r.boxes) > 0:
                        person_detected = True
                        break

                if person_detected:
                    now = time.time()
                    with self.state.lock:
                        self.state.last_detection_time = now
                        if not self.state.recording:
                            self.state.recording = True
                            self.logger.info("[YOLO] Pessoa detectada. Sinalizando início de gravação.")
                        else:
                            self.logger.debug("[YOLO] Pessoa detectada. Gravação em andamento.")

            except Exception as e:
                self.logger.error(f"[YOLO] Erro na inferência: {e}")

        self.logger.info("[YOLO] Thread encerrada.")

class RecordThread(threading.Thread):

    def __init__(self, capture_queue: queue.Queue, state: SharedState,
                 output_dir: str, logger: logging.Logger):
        super().__init__(name="RecordThread", daemon=True)
        self.capture_queue = capture_queue
        self.state = state
        self.output_dir = output_dir
        self.logger = logger
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _new_clip_path(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"clip_{ts}{VIDEO_EXTENSION}")

    def _open_writer(self, path: str, frame_size: tuple, fps: float) -> cv2.VideoWriter:
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
        writer = cv2.VideoWriter(path, fourcc, fps, frame_size)
        self.logger.info(f"[Record] Novo clipe iniciado: {path} | FPS: {fps:.2f}")
        return writer

    def _close_writer(self, writer: cv2.VideoWriter, path: str):
        writer.release()
        self.logger.info(f"[Record] Clipe finalizado: {path}")

    def run(self):
        self.logger.info("[Record] Thread iniciada.")
        writer: Optional[cv2.VideoWriter] = None
        clip_path = ""

        while not self.state.stop_event.is_set() or not self.capture_queue.empty():
            try:
                frame = self.capture_queue.get(timeout=0.5)
            except queue.Empty:
                self._check_cooldown(writer, clip_path)
                if writer is None:
                    continue
                writer, clip_path = self._maybe_close(writer, clip_path)
                continue
            with self.state.lock:
                should_record = self.state.recording
                last_det = self.state.last_detection_time
                frame_size = self.state.frame_size
                camera_fps = self.state.camera_fps

            now = time.time()
            cooldown_expired = (now - last_det) > COOLDOWN_TIME if last_det > 0 else False
            if writer is not None and cooldown_expired:
                self._close_writer(writer, clip_path)
                writer = None
                clip_path = ""
                with self.state.lock:
                    self.state.recording = False
                    self.state.last_detection_time = 0.0
                self.logger.info("[Record] Cooldown expirado. Gravação encerrada.")
                continue
            if should_record and writer is None and frame_size is not None:
                clip_path = self._new_clip_path()
                fps = camera_fps if camera_fps > 0 else VIDEO_FPS
                writer = self._open_writer(clip_path, frame_size, fps)
            if writer is not None:
                try:
                    writer.write(frame)
                except Exception as e:
                    self.logger.error(f"[Record] Erro ao escrever frame: {e}")
        if writer is not None:
            self._close_writer(writer, clip_path)

        self.logger.info("[Record] Thread encerrada.")

    def _check_cooldown(self, writer, clip_path):
        pass

    def _maybe_close(self, writer, clip_path):
        with self.state.lock:
            last_det = self.state.last_detection_time
        now = time.time()
        if writer is not None and last_det > 0 and (now - last_det) > COOLDOWN_TIME:
            self._close_writer(writer, clip_path)
            with self.state.lock:
                self.state.recording = False
                self.state.last_detection_time = 0.0
            return None, ""
        return writer, clip_path

class SurveillanceSystem:
    def __init__(self):
        self.logger = setup_logging(LOG_DIR)
        self.state = SharedState()
        self.capture_queue = queue.Queue(maxsize=CAPTURE_QUEUE_SIZE)
        self.yolo_queue = queue.Queue(maxsize=YOLO_QUEUE_SIZE)

        self.capture_thread = CaptureThread(
            rtsp_url=RTSP_URL,
            capture_queue=self.capture_queue,
            yolo_queue=self.yolo_queue,
            state=self.state,
            logger=self.logger
        )
        self.yolo_thread = YOLOThread(
            yolo_queue=self.yolo_queue,
            state=self.state,
            logger=self.logger
        )
        self.record_thread = RecordThread(
            capture_queue=self.capture_queue,
            state=self.state,
            output_dir=OUTPUT_DIR,
            logger=self.logger
        )

    def start(self):
        self.logger.info("=" * 60)
        self.logger.info("Sistema de Vigilância iniciado.")
        self.logger.info(f"  RTSP URL   : {RTSP_URL}")
        self.logger.info(f"  Output Dir : {OUTPUT_DIR}")
        self.logger.info(f"  Cooldown   : {COOLDOWN_TIME}s")
        self.logger.info(f"  YOLO Model : {YOLO_MODEL}")
        self.logger.info("=" * 60)

        self.capture_thread.start()
        self.yolo_thread.start()
        self.record_thread.start()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        try:
            while not self.state.stop_event.is_set():
                time.sleep(10)
                self._health_check()
        except Exception as e:
            self.logger.error(f"[Main] Exceção no loop principal: {e}")
        finally:
            self.stop()

    def _health_check(self):
        threads = [
            ("CaptureThread", self.capture_thread),
            ("YOLOThread", self.yolo_thread),
            ("RecordThread", self.record_thread),
        ]
        for name, t in threads:
            if not t.is_alive():
                self.logger.error(f"[Health] Thread {name} morreu inesperadamente!")

        with self.state.lock:
            real_fps = self.state.camera_fps
            dropped_cq = self.state.dropped_capture_queue
            dropped_yq = self.state.dropped_yolo_queue
            recording = self.state.recording

        cq = self.capture_queue.qsize()
        yq = self.yolo_queue.qsize()

        self.logger.info(
            f"[Health] FPS_real={real_fps:.2f} | "
            f"capture_queue={cq}/{CAPTURE_QUEUE_SIZE} | "
            f"yolo_queue={yq}/{YOLO_QUEUE_SIZE} | "
            f"gravando={recording} | "
            f"frames_descartados_gravacao={dropped_cq} | "
            f"frames_descartados_yolo={dropped_yq}"
        )

        if cq >= CAPTURE_QUEUE_SIZE * 0.9:
            self.logger.warning(
                f"[Health] ALERTA: capture_queue quase cheia ({cq}/{CAPTURE_QUEUE_SIZE}). "
               
            )
        if dropped_cq > 0:
            self.logger.warning(
                f"[Health] ALERTA: {dropped_cq} frames descartados da fila de gravação "
                f"(VideoWriter lento ou CPU sobrecarregada)."
            )
        if dropped_yq > 0:
            self.logger.debug(
                f"[Health] {dropped_yq} frames descartados da fila YOLO "
                
            )

    def _signal_handler(self, signum, frame):
        self.logger.info(f"[Main] Sinal {signum} recebido. Encerrando...")
        self.stop()

    def stop(self):
        self.logger.info("[Main] Encerrando sistema...")
        self.state.stop_event.set()

        for t in [self.capture_thread, self.yolo_thread, self.record_thread]:
            if t.is_alive():
                t.join(timeout=15)
                if t.is_alive():
                    self.logger.warning(f"[Main] Thread {t.name} não encerrou a tempo.")

        self.logger.info("[Main] Sistema encerrado com sucesso.")
        sys.exit(0)

if __name__ == "__main__":
    system = SurveillanceSystem()
    system.start()
