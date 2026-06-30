import threading
import queue
import numpy as np

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


class AudioCapture:
    def __init__(self, device=None, sample_rate=16000, chunk_duration=3.0):
        self.device = device
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_samples = int(sample_rate * chunk_duration)
        self.overlap_samples = self.chunk_samples // 2

        self._buffer = []
        self._buffer_lock = threading.Lock()
        self._audio_queue = queue.Queue()
        self._running = False
        self._stream = None
        self._thread = None

    def start(self):
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice no está instalado. Ejecuta: pip install sounddevice")

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=3)

    def get_chunk(self, timeout=1.0):
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _run(self):
        def callback(indata, frames, time_info, status):
            if not self._running:
                return
            mono = indata[:, 0].copy() if indata.ndim > 1 else indata[:, 0].copy()
            with self._buffer_lock:
                self._buffer.extend(mono.tolist())
                while len(self._buffer) >= self.chunk_samples:
                    chunk = np.array(self._buffer[: self.chunk_samples], dtype=np.float32)
                    self._audio_queue.put(chunk)
                    # Keep overlap so speech at chunk boundaries isn't cut off
                    self._buffer = self._buffer[self.overlap_samples :]

        try:
            self._stream = sd.InputStream(
                device=self.device,
                channels=1,
                samplerate=self.sample_rate,
                dtype="float32",
                blocksize=1024,
                callback=callback,
            )
            with self._stream:
                while self._running:
                    threading.Event().wait(0.1)
        except Exception as e:
            print(f"[Audio] Error al capturar audio: {e}")
            self._running = False

    @staticmethod
    def list_devices():
        if not SOUNDDEVICE_AVAILABLE:
            return []
        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            result.append({
                "id": i,
                "name": d["name"],
                "input_channels": int(d["max_input_channels"]),
                "output_channels": int(d["max_output_channels"]),
                "default_samplerate": int(d["default_samplerate"]),
            })
        return result

    @staticmethod
    def rms(chunk: np.ndarray) -> float:
        return float(np.sqrt(np.mean(chunk ** 2)))
