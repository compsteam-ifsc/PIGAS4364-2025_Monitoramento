import cv2
import threading
import queue
import time
import os
import logging
import signal
import collections
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

import torch
from ultralytics import YOLO


os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"

# ==========================================
# CONFIGURAÇÕES DO SISTEMA
# ==========================================
YOLO_MODEL = "yolo11s.pt"
YOLO_CONFIDENCE = 0.45


TARGET_YOLO_FPS = 5.0  
IMG_SIZE = 640

PRE_BUFFER_SECONDS = 3.0
POST_BUFFER_SECONDS = 3.0
MIN_DETECTED_FRAMES = 5  


CAPTURE_QUEUE_SIZE = 200 
YOLO_QUEUE_SIZE = 5

USE_GPU = True
TORCH_THREADS = 4

VIDEO_CODEC = "mp4v"
VIDEO_EXTENSION = ".mp4"
RTSP_RECONNECT_DELAY = 5.0
THREAD_RESTART_DELAY = 5.0

# Configurações Adicionais de Ambiente
RTSP_URL = "rtsp://pigas4362-c1:pigas4362-c1@192.168.0.3:554/stream1"
OUTPUT_DIR = r"D:\Projeto\videos"
LOG_DIR = "./logs"


def setup_logging(log_dir: str) -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger = logging.getLogger("surveillance")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # Evita duplicação de logs se chamado mais de uma vez

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    fh_system = logging.FileHandler(os.path.join(log_dir, f"system_{timestamp}.log"), encoding="utf-8")
    fh_system.setLevel(logging.INFO)
    fh_system.setFormatter(formatter)

    fh_events = logging.FileHandler(os.path.join(log_dir, f"events_{timestamp}.log"), encoding="utf-8")
    fh_events.setLevel(logging.DEBUG)
    fh_events.setFormatter(formatter)

    fh_errors = logging.FileHandler(os.path.join(log_dir, f"errors_{timestamp}.log"), encoding="utf-8")
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
class DetectionEvent:
    frame_ts: float  # Timestamp do frame exato em que a pessoa apareceu
    trigger_ts: float # Timestamp do momento em que o evento foi confirmado


class StateEnum:
    IDLE = 0
    DETECTING = 1
    RECORDING = 2


@dataclass
class SharedState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    status: int = StateEnum.IDLE
    
    first_detection_ts: float = 0.0
    last_detection_ts: float = 0.0
    detected_frames_count: int = 0
    
    frame_size: Optional[Tuple[int, int]] = None
    camera_fps: float = 25.0
    rtsp_connected: bool = False
    
    dropped_capture_queue: int = 0
    dropped_yolo_queue: int = 0
    device_info: str = "Uninitialized"
    stop_event: threading.Event = field(default_factory=threading.Event)


class FrameBuffer:
    def __init__(self, buffer_seconds: float):
        # O buffer precisa ser maior que o PRE_BUFFER para abrigar o tempo 
        # que o YOLO leva para confirmar o MIN_DETECTED_FRAMES
        self.keep_seconds = buffer_seconds + 6.0 
        self.buffer = collections.deque()
        self.lock = threading.Lock()

    def add_frame(self, timestamp: float, frame):
        with self.lock:
            self.buffer.append((timestamp, frame))
            cutoff = timestamp - self.keep_seconds
            while self.buffer and self.buffer[0][0] < cutoff:
                self.buffer.popleft()

    def get_snapshot(self, start_ts: float, end_ts: float) -> List[Tuple[float, any]]:
        with self.lock:
            return [(t, f) for t, f in self.buffer if start_ts <= t <= end_ts]


class CaptureThread(threading.Thread):
    def __init__(self, rtsp_url: str, capture_queue: queue.Queue, yolo_queue: queue.Queue,
                 frame_buffer: FrameBuffer, state: SharedState, logger: logging.Logger):
        super().__init__(name="CaptureThread", daemon=True)
        self.rtsp_url = rtsp_url
        self.capture_queue = capture_queue
        self.yolo_queue = yolo_queue
        self.frame_buffer = frame_buffer
        self.state = state
        self.logger = logger
        
        self.fps_start_time = 0.0
        self.fps_frame_counter = 0
        self.last_yolo_put_time = 0.0

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print(cap)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            reported_fps = cap.get(cv2.CAP_PROP_FPS)
            print("opened")
            with self.state.lock:
                self.state.frame_size = (w, h)
                self.state.rtsp_connected = True
                if 5.0 <= reported_fps <= 120.0:
                    self.state.camera_fps = reported_fps

            self.logger.info(f"[Câmera] Conectado ao RTSP: {self.rtsp_url} | Resolução: {w}x{h} | FPS: {reported_fps:.2f}")
            self.fps_start_time = time.monotonic()
            self.fps_frame_counter = 0
            return cap

        if cap is not None:
            cap.release()
        with self.state.lock:
            self.state.rtsp_connected = False
        return None

    def _update_real_fps(self):
        self.fps_frame_counter += 1
        now = time.monotonic()
        elapsed = now - self.fps_start_time
        if elapsed >= 3.0:
            real_fps = self.fps_frame_counter / elapsed
            if real_fps > 1.0:
                with self.state.lock:
                    self.state.camera_fps = (self.state.camera_fps * 0.7) + (real_fps * 0.3)
            self.fps_start_time = now
            self.fps_frame_counter = 0

    def _put_with_drop_oldest(self, q: queue.Queue, item, is_capture_queue: bool):
        try:
            q.put_nowait(item)
        except queue.Full:
            try:
                q.get_nowait() # Remove o mais antigo
            except queue.Empty:
                pass
            try:
                q.put_nowait(item) # Tenta colocar novamente
            except queue.Full:
                pass
            
            with self.state.lock:
                if is_capture_queue:
                    self.state.dropped_capture_queue += 1
                else:
                    self.state.dropped_yolo_queue += 1

    def run(self):
        self.logger.info("[CaptureThread] Iniciada.")
        cap = None
        yolo_interval_sec = 1.0 / TARGET_YOLO_FPS if TARGET_YOLO_FPS > 0 else 0

        try:
            while not self.state.stop_event.is_set():
                if cap is None or not cap.isOpened():
                    if cap is not None:
                        cap.release()
                        self.logger.warning("[Câmera] Desconexão detectada. Tentando reconectar...")

                    with self.state.lock:
                        self.state.rtsp_connected = False

                    cap = self._open_capture()
                    if cap is None:
                        self.state.stop_event.wait(RTSP_RECONNECT_DELAY)
                        continue

                ret, frame = cap.read()
                ts = time.monotonic()

                if not ret or frame is None:
                    self.logger.warning("[Câmera] Falha na leitura do frame (provável queda). Reiniciando...")
                    cap.release()
                    cap = None
                    with self.state.lock:
                        self.state.rtsp_connected = False
                    continue

                self._update_real_fps()
                self.frame_buffer.add_frame(ts, frame)
                
                item = (ts, frame)
                self._put_with_drop_oldest(self.capture_queue, item, is_capture_queue=True)

                # Controle explícito de FPS para o YOLO
                if yolo_interval_sec == 0 or (ts - self.last_yolo_put_time) >= yolo_interval_sec:
                    self._put_with_drop_oldest(self.yolo_queue, item, is_capture_queue=False)
                    self.last_yolo_put_time = ts

        except Exception as e:
            self.logger.exception(f"[CaptureThread] Erro fatal: {e}")
        finally:
            if cap is not None:
                cap.release()
            with self.state.lock:
                self.state.rtsp_connected = False
            self.logger.info("[CaptureThread] Encerrada.")


class YOLOThread(threading.Thread):
    def __init__(self, yolo_queue: queue.Queue, event_queue: queue.Queue, state: SharedState, logger: logging.Logger):
        super().__init__(name="YOLOThread", daemon=True)
        self.yolo_queue = yolo_queue
        self.event_queue = event_queue
        self.state = state
        self.logger = logger
        self.model = None

    def _load_model(self):
        torch.set_num_threads(TORCH_THREADS)
        device = "cuda" if (USE_GPU and torch.cuda.is_available()) else "cpu"
        device_str = f"GPU: {torch.cuda.get_device_name(0)} (CUDA)" if device == "cuda" else "CPU"

        with self.state.lock:
            self.state.device_info = device_str

        while not self.state.stop_event.is_set():
            try:
                self.logger.info(f"[YOLO] Carregando modelo: {YOLO_MODEL} em {device_str}")
                self.model = YOLO(YOLO_MODEL)
                self.model.to(device)
                self.logger.info("[YOLO] Carregamento concluído.")
                return
            except Exception as e:
                self.logger.error(f"[YOLO] Falha ao carregar modelo: {e}. Repetindo em 5s...")
                self.state.stop_event.wait(5.0)

    def run(self):
        self.logger.info("[YOLOThread] Iniciada.")
        self._load_model()

        try:
            while not self.state.stop_event.is_set():
                try:
                    ts, frame = self.yolo_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    results = self.model.predict(source=frame, classes=[0], conf=YOLO_CONFIDENCE, imgsz=IMG_SIZE, verbose=False)
                    person_detected = any(r.boxes is not None and len(r.boxes) > 0 for r in results)

                    with self.state.lock:
                        now = time.monotonic()
                        
                        if person_detected:
                            if self.state.status == StateEnum.IDLE:
                                # Inicia contagem
                                self.state.status = StateEnum.DETECTING
                                self.state.first_detection_ts = ts
                                self.state.last_detection_ts = now
                                self.state.detected_frames_count = 1
                                self.logger.debug(f"[YOLO] Detectado frame 1/{MIN_DETECTED_FRAMES}. Aguardando confirmação.")

                            elif self.state.status == StateEnum.DETECTING:
                                # Acumula confirmação
                                self.state.last_detection_ts = now
                                self.state.detected_frames_count += 1
                                
                                if self.state.detected_frames_count >= MIN_DETECTED_FRAMES:
                                    self.state.status = StateEnum.RECORDING
                                    event = DetectionEvent(frame_ts=self.state.first_detection_ts, trigger_ts=now)
                                    try:
                                        self.event_queue.put_nowait(event)
                                        self.logger.info("[Evento] Evento confirmado! Disparando gravação.")
                                    except queue.Full:
                                        pass

                            elif self.state.status == StateEnum.RECORDING:
                                # Mantém vivo
                                self.state.last_detection_ts = now
                                self.state.detected_frames_count += 1

                        else:
                            # Se perder a detecção antes de confirmar
                            if self.state.status == StateEnum.DETECTING:
                                if (now - self.state.last_detection_ts) > POST_BUFFER_SECONDS:
                                    self.logger.debug("[YOLO] Falso positivo descartado. Voltando para IDLE.")
                                    self.state.status = StateEnum.IDLE
                                    self.state.detected_frames_count = 0
                            # (Se for RECORDING, a RecordThread cuida de fechar baseada no último last_detection_ts)

                except Exception as e:
                    self.logger.error(f"[Erro YOLO] Falha pontual na inferência: {e}")
                    
        except Exception as e:
            self.logger.exception(f"[YOLOThread] Erro fatal: {e}")
        finally:
            self.logger.info("[YOLOThread] Encerrada.")


class RecordThread(threading.Thread):
    def __init__(self, capture_queue: queue.Queue, event_queue: queue.Queue, frame_buffer: FrameBuffer,
                 state: SharedState, output_dir: str, logger: logging.Logger):
        super().__init__(name="RecordThread", daemon=True)
        self.capture_queue = capture_queue
        self.event_queue = event_queue
        self.frame_buffer = frame_buffer
        self.state = state
        self.output_dir = output_dir
        self.logger = logger
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _new_clip_path(self) -> str:
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"clip_{ts_str}{VIDEO_EXTENSION}")

    def run(self):
        self.logger.info("[RecordThread] Iniciada.")
        writer: Optional[cv2.VideoWriter] = None
        current_clip_path = ""
        last_written_ts = 0.0

        try:
            while not self.state.stop_event.is_set():
                try:
                    ts, frame = self.capture_queue.get(timeout=0.1)
                    got_frame = True
                except queue.Empty:
                    got_frame = False
                    frame = None
                    ts = 0

                if writer is None:
                    # Verifica se deve iniciar a gravação
                    try:
                        event: DetectionEvent = self.event_queue.get_nowait()
                    except queue.Empty:
                        event = None

                    if event is not None:
                        with self.state.lock:
                            camera_fps = self.state.camera_fps
                            frame_size = self.state.frame_size

                        if frame_size is None or frame_size[0] == 0:
                            self.logger.error("[Record] Dimensão do frame inválida. Abortando.")
                            with self.state.lock: self.state.status = StateEnum.IDLE
                            continue

                        current_clip_path = self._new_clip_path()
                        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
                        
                        try:
                            writer = cv2.VideoWriter(current_clip_path, fourcc, camera_fps, frame_size)
                            if not writer.isOpened():
                                raise RuntimeError("isOpened() == False")
                        except Exception as e:
                            self.logger.error(f"[Record] Falha ao abrir VideoWriter: {e}")
                            writer = None
                            with self.state.lock: self.state.status = StateEnum.IDLE
                            continue

                        self.logger.info(f"[Record] Gravando clipe: {current_clip_path} | {camera_fps:.2f} FPS")
                        
                        # Resgata o PRE_BUFFER partindo exatamente de antes da *primeira* detecção do evento
                        start_ts = event.frame_ts - PRE_BUFFER_SECONDS
                        snapshot = self.frame_buffer.get_snapshot(start_ts, time.monotonic())
                        
                        try:
                            for snap_ts, snap_frame in snapshot:
                                if snap_ts > last_written_ts:
                                    writer.write(snap_frame)
                                    last_written_ts = snap_ts
                        except Exception as e:
                            self.logger.error(f"[Record] Erro ao gravar buffer: {e}")

                        # Se tiver pego um frame atual da fila
                        if got_frame and ts > last_written_ts:
                            writer.write(frame)
                            last_written_ts = ts

                else:
                    # Gravando fluxo normal
                    if got_frame:
                        h, w = frame.shape[:2]
                        with self.state.lock:
                            expected_size = self.state.frame_size

                        if expected_size and (w != expected_size[0] or h != expected_size[1]):
                            self.logger.warning("[Record] Mudança de resolução! Encerrando clipe.")
                            self._finalize_clip(writer, current_clip_path)
                            writer = None
                            continue

                        if ts > last_written_ts:
                            try:
                                writer.write(frame)
                                last_written_ts = ts
                            except Exception as e:
                                self.logger.error(f"[Erro Record] Falha ao escrever frame: {e}")

                    # Verifica se o evento terminou
                    with self.state.lock:
                        status = self.state.status
                        last_det = self.state.last_detection_ts
                        total_det = self.state.detected_frames_count

                    if status == StateEnum.RECORDING and (time.monotonic() - last_det) > POST_BUFFER_SECONDS:
                        self._finalize_clip(writer, current_clip_path, total_det)
                        writer = None
                        with self.state.lock:
                            self.state.status = StateEnum.IDLE
                            self.state.detected_frames_count = 0

        except Exception as e:
            self.logger.exception(f"[RecordThread] Erro fatal: {e}")
        finally:
            if writer is not None:
                with self.state.lock: det_count = self.state.detected_frames_count
                self._finalize_clip(writer, current_clip_path, det_count)
            self.logger.info("[RecordThread] Encerrada.")

    def _finalize_clip(self, writer: cv2.VideoWriter, clip_path: str, detected_count: int = 0):
        try:
            writer.release()
            self.logger.info(f"[Record] Arquivo salvo: {clip_path} (Detecções: {detected_count})")
        except Exception as e:
            self.logger.error(f"[Record] Erro no release() do VideoWriter: {e}")

        # Limpa eventos perdidos da fila
        while not self.event_queue.empty():
            try: self.event_queue.get_nowait()
            except queue.Empty: break


class SurveillanceSystem:
    def __init__(self):
        self.logger = setup_logging(LOG_DIR)
        self.state = SharedState()
        self.frame_buffer = FrameBuffer(buffer_seconds=PRE_BUFFER_SECONDS)
        
        self.capture_queue = queue.Queue(maxsize=CAPTURE_QUEUE_SIZE)
        self.yolo_queue = queue.Queue(maxsize=YOLO_QUEUE_SIZE)
        self.event_queue = queue.Queue(maxsize=5)

        self.restarts = {"CaptureThread": 0, "YOLOThread": 0, "RecordThread": 0}
        self.restarting_flags = {"CaptureThread": False, "YOLOThread": False, "RecordThread": False}
        self.thread_lock = threading.Lock()
        self.restart_lock = threading.Lock()

        self.capture_thread = self._create_capture_thread()
        self.yolo_thread = self._create_yolo_thread()
        self.record_thread = self._create_record_thread()

    def _create_capture_thread(self):
        return CaptureThread(RTSP_URL, self.capture_queue, self.yolo_queue, self.frame_buffer, self.state, self.logger)

    def _create_yolo_thread(self):
        return YOLOThread(self.yolo_queue, self.event_queue, self.state, self.logger)

    def _create_record_thread(self):
        return RecordThread(self.capture_queue, self.event_queue, self.frame_buffer, self.state, OUTPUT_DIR, self.logger)

    def start(self):
        self.logger.info("=" * 60)
        self.logger.info("SISTEMA DE VIGILÂNCIA RTSP 24/7 INICIADO")
        self.logger.info("=" * 60)

        with self.thread_lock:
            self.capture_thread.start()
            self.yolo_thread.start()
            self.record_thread.start()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            while not self.state.stop_event.is_set():
                self.state.stop_event.wait(10.0)
                if not self.state.stop_event.is_set():
                    self._health_check()
        except Exception as e:
            self.logger.error(f"[Erro Crítico] Main loop: {e}")
        finally:
            self.stop()

    def _restart_thread(self, thread_name: str):
        if self.state.stop_event.is_set():
            return

        with self.restart_lock:
            if self.restarting_flags[thread_name]:
                return
            self.restarting_flags[thread_name] = True

        threading.Thread(target=self._restart_worker, args=(thread_name,), daemon=True).start()

    def _restart_worker(self, thread_name: str):
        self.logger.warning(f"[Health] Recriando {thread_name} em {THREAD_RESTART_DELAY}s...")
        time.sleep(THREAD_RESTART_DELAY)

        if self.state.stop_event.is_set():
            with self.restart_lock:
                self.restarting_flags[thread_name] = False
            return

        with self.thread_lock:
            self.restarts[thread_name] += 1
            if thread_name == "CaptureThread" and not self.capture_thread.is_alive():
                self.capture_thread = self._create_capture_thread()
                self.capture_thread.start()
            elif thread_name == "YOLOThread" and not self.yolo_thread.is_alive():
                self.yolo_thread = self._create_yolo_thread()
                self.yolo_thread.start()
            elif thread_name == "RecordThread" and not self.record_thread.is_alive():
                self.record_thread = self._create_record_thread()
                self.record_thread.start()

        self.logger.info(f"[Health] {thread_name} iniciada! (Restarts: {self.restarts[thread_name]})")
        with self.restart_lock:
            self.restarting_flags[thread_name] = False

    def _get_memory_usage(self) -> str:
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024 * 1024)
            return f"{mem_mb:.2f} MB"
        return "N/A"

    def _health_check(self):
        with self.thread_lock:
            threads = {
                "CaptureThread": self.capture_thread,
                "YOLOThread": self.yolo_thread,
                "RecordThread": self.record_thread
            }

        for t_name, t_instance in threads.items():
            if not t_instance.is_alive():
                self.logger.error(f"[Health] {t_name} MORREU. Iniciando Auto-Healing...")
                self._restart_thread(t_name)

        with self.state.lock:
            rtsp_ok = self.state.rtsp_connected
            real_fps = self.state.camera_fps
            dropped_cq = self.state.dropped_capture_queue
            dropped_yq = self.state.dropped_yolo_queue
            
            status_map = {StateEnum.IDLE: "IDLE", StateEnum.DETECTING: "CONFIRMANDO", StateEnum.RECORDING: "GRAVANDO"}
            status_str = status_map.get(self.state.status, "UNKNOWN")
            det_count = self.state.detected_frames_count
            dev_info = self.state.device_info

        cq_len = self.capture_queue.qsize()
        yq_len = self.yolo_queue.qsize()
        ram = self._get_memory_usage()

        status_msg = (
            f"\n[Métricas] RTSP: {'OK' if rtsp_ok else 'OFF'} | Câmera FPS: {real_fps:.1f} | RAM: {ram} | {dev_info}\n"
            f"           Filas -> Cap: {cq_len}/{CAPTURE_QUEUE_SIZE} (Drops: {dropped_cq}) | YOLO: {yq_len}/{YOLO_QUEUE_SIZE} (Drops: {dropped_yq})\n"
            f"           Estado: {status_str} (Detecções ativas: {det_count})\n"
            f"           Restarts: Cap({self.restarts['CaptureThread']}), YOLO({self.restarts['YOLOThread']}), Rec({self.restarts['RecordThread']})"
        )
        self.logger.info(status_msg)

    def _signal_handler(self, signum, frame):
        self.logger.info(f"\n[Sistema] Sinal de parada ({signum}) recebido...")
        self.stop()

    def stop(self):
        if self.state.stop_event.is_set():
            return
        
        self.state.stop_event.set()
        
        with self.thread_lock:
            threads_to_join = [self.capture_thread, self.yolo_thread, self.record_thread]

        for t in threads_to_join:
            if t.is_alive():
                # Timeout curto. Se a thread travou no OpenCV, Python não vai pendurar
                # porque as threads são daemon e vão morrer com o processo.
                t.join(timeout=3.0) 

        self.logger.info("[Sistema] Encerramento concluído com sucesso.")


if __name__ == "__main__":
    system = SurveillanceSystem()
    system.start()