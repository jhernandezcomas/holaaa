# 🎧 Zoom Interview Assistant

Asistente de entrevistas en tiempo real impulsado por Claude.  
Escucha la llamada, traduce al español lo que dice el entrevistador y te sugiere respuestas en inglés basadas en tu perfil.

## Cómo funciona

```
Audio del sistema (Zoom/celular)
        ↓
   Whisper (STT)
        ↓
    Claude AI
        ↓
  Traducción al español  +  Respuesta sugerida en inglés
        ↓
  Interfaz web en tu navegador
```

---

## Requisitos

- Python 3.9+
- Una API Key de Anthropic → [console.anthropic.com](https://console.anthropic.com)
- (Linux) PulseAudio o PipeWire para capturar el audio del sistema

---

## Instalación

### 1. Clona el repositorio y entra al directorio

```bash
git clone <repo-url>
cd zoom-interview-assistant
```

### 2. Instala dependencias del sistema (Linux)

```bash
sudo apt-get install -y portaudio19-dev libsndfile1-dev
```

En macOS:
```bash
brew install portaudio
```

### 3. Instala dependencias de Python

```bash
pip install -r requirements.txt
```

### 4. Configura tus credenciales

```bash
cp .env.example .env
# Edita .env y pon tu ANTHROPIC_API_KEY
```

### 5. Rellena tu perfil profesional

Edita el archivo `profile.md` con tu información real:
- Experiencia laboral
- Habilidades técnicas
- Proyectos
- Educación

**Cuanta más información pongas, mejores serán las respuestas sugeridas.**

---

## Uso

```bash
python main.py
```

Abre tu navegador en **http://localhost:8000**

### En la interfaz:

1. **Selecciona el dispositivo de audio** — Para capturar lo que sale por los altavoces (la voz del entrevistador en Zoom), selecciona el que tenga `monitor` en el nombre (Linux/PulseAudio)
2. **Pulsa ▶ Iniciar** antes de que empiece la entrevista
3. Cuando el entrevistador hable, verás:
   - **Izquierda**: transcripción en vivo (inglés)
   - **Derecha**: traducción al español + respuesta sugerida en inglés

---

## Cómo capturar el audio de Zoom

### Linux (PulseAudio / PipeWire)

El dispositivo correcto suele llamarse algo como:  
`Monitor of Built-in Audio Analog Stereo` o `Monitor of <tu tarjeta de sonido>`

En la interfaz web verás los dispositivos marcados con 🔊 si son monitores de salida.

Si no aparece ningún monitor, ejecuta:

```bash
pactl load-module module-loopback latency_msec=1
```

### macOS

Instala [BlackHole](https://github.com/ExistentialAudio/BlackHole) (gratis) y selecciónalo como fuente de audio en la app.

### Windows

Usa [VB-Cable](https://vb-audio.com/Cable/) y configura Zoom para que la salida vaya a ese dispositivo virtual. Luego selecciónalo en la app.

---

## Variables de entorno (`.env`)

| Variable | Default | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Obligatorio** |
| `WHISPER_MODEL` | `base` | Tamaño del modelo de transcripción (`tiny`, `base`, `small`, `medium`, `large-v3`) |
| `AUDIO_CHUNK_DURATION` | `3` | Segundos por chunk de audio |
| `SILENCE_THRESHOLD` | `2` | Chunks de silencio antes de enviar texto a Claude |

---

## Latencia esperada

| Fase | Tiempo aproximado |
|---|---|
| Captura de audio | ~3 seg (duración del chunk) |
| Transcripción Whisper (CPU, modelo base) | ~1-2 seg |
| Claude API | ~1-2 seg |
| **Total** | **~5-7 seg** |

Para reducir latencia: usa `WHISPER_MODEL=tiny` o una GPU.

---

## Estructura del proyecto

```
.
├── main.py              # Servidor FastAPI + pipeline de audio
├── profile.md           # Tu perfil profesional (editar antes de la entrevista)
├── requirements.txt
├── .env.example
└── src/
    ├── audio.py         # Captura de audio del sistema
    ├── transcriber.py   # Transcripción con faster-whisper
    ├── assistant.py     # Integración con Claude API
    └── ui/
        └── index.html   # Interfaz web
```
