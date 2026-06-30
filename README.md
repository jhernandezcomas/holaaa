# 🎧 Interview Assistant — José Hernández

Asistente de entrevistas en tiempo real impulsado por Claude.  
Escucha lo que dice el entrevistador en Zoom o en llamada, traduce al español y te sugiere respuestas en inglés basadas en tu perfil real.

## Cómo funciona

```
Audio del sistema (Zoom / llamada)
        ↓
   Whisper — voz a texto
        ↓
   Claude AI — conoce tu perfil
        ↓
  Traducción al español  +  Respuesta sugerida en inglés
        ↓
  Interfaz web  →  http://localhost:8000
```

---

## Instalación (una sola vez)

### 1. Clona el repositorio

```bash
git clone https://github.com/jhernandezcomas/holaaa.git
cd holaaa
```

### 2. Instala dependencias del sistema

**Linux / Ubuntu / Debian:**
```bash
sudo apt-get install -y portaudio19-dev libsndfile1-dev
```

**macOS:**
```bash
brew install portaudio
```

**Windows:** Descarga e instala [PortAudio](http://www.portaudio.com/download.html)

### 3. Instala dependencias de Python

```bash
pip install -r requirements.txt
```

### 4. Agrega tu API Key de Anthropic

```bash
cp .env.example .env
```

Abre `.env` y reemplaza `sk-ant-...` con tu clave real de [console.anthropic.com](https://console.anthropic.com).

---

## Uso — antes de cada entrevista

```bash
python main.py
```

Abre **http://localhost:8000** en tu navegador.

### Pasos:

1. **Selecciona el dispositivo de audio** con 🔊 en el nombre (ej. `Monitor of Built-in Audio`) — este captura lo que sale por tus altavoces/auriculares (la voz del entrevistador en Zoom)
2. **Pulsa ▶ Iniciar** justo antes de que empiece la llamada
3. Cuando el entrevistador hable verás:
   - **Izquierda:** lo que dijo en inglés (en vivo)
   - **Derecha:** traducción al español + respuesta sugerida en inglés que puedes decir

### Botones:
| Botón | Para qué sirve |
|---|---|
| ▶ Iniciar | Comienza a escuchar |
| ■ Detener | Para la captura |
| ↺ Reset contexto | Nueva entrevista (borra historial de conversación) |
| 🗑 Limpiar | Limpia la pantalla |

---

## Captura de audio de Zoom

### Linux (PulseAudio / PipeWire)
Selecciona el dispositivo marcado con 🔊 — normalmente se llama  
`Monitor of Built-in Audio Analog Stereo` o similar.

Si no aparece ninguno:
```bash
pactl load-module module-loopback latency_msec=1
```

### macOS
Instala [BlackHole 2ch](https://github.com/ExistentialAudio/BlackHole) (gratis).  
En Configuración de Sonido de macOS, establece la salida a BlackHole.  
En la app, selecciona BlackHole como dispositivo.

### Windows
Descarga [VB-Cable](https://vb-audio.com/Cable/) (gratis).  
Pon la salida de Zoom en CABLE Input.  
En la app, selecciona CABLE Output como dispositivo.

---

## Variables en `.env`

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Obligatorio** |
| `WHISPER_MODEL` | `base` | Tamaño del modelo (`tiny` = más rápido, `small`/`medium` = más preciso) |
| `AUDIO_CHUNK_DURATION` | `3` | Segundos de audio por chunk |
| `SILENCE_THRESHOLD` | `2` | Chunks de silencio antes de enviar a Claude |

---

## Latencia esperada

| Fase | Tiempo |
|---|---|
| Captura de audio | ~3 seg |
| Transcripción Whisper (CPU, modelo base) | ~1–2 seg |
| Claude API | ~1–2 seg |
| **Total** | **~5–7 seg** |

Para menos latencia: cambia `WHISPER_MODEL=tiny` en `.env`.

---

## Estructura

```
.
├── main.py              # Servidor + pipeline de audio
├── profile.md           # Tu perfil profesional (ya rellenado)
├── .env                 # Tu API key (no se sube a git)
├── requirements.txt
└── src/
    ├── audio.py         # Captura de audio del sistema
    ├── transcriber.py   # Whisper (voz → texto)
    ├── assistant.py     # Claude AI (traducción + respuestas)
    └── ui/
        └── index.html   # Interfaz web
```
