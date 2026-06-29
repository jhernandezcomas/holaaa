import numpy as np


class Transcriber:
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        from faster_whisper import WhisperModel

        compute_type = "int8" if device == "cpu" else "float16"
        print(f"[Whisper] Cargando modelo '{model_size}' en {device} ({compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[Whisper] Modelo listo.")

    def transcribe(self, audio: np.ndarray, language: str = "en") -> str:
        segments, _ = self.model.transcribe(
            audio,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 400},
        )
        text = " ".join(seg.text for seg in segments).strip()
        return text
