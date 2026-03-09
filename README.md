# 🌐 WEBCductor

> **Desktop AI Chat Translator** — Captura texto de cualquier ventana en pantalla, lo procesa con OCR y lo traduce en tiempo real usando un modelo de lenguaje local (Ollama), mostrando el resultado en un overlay transparente siempre visible.

---

## 📋 Tabla de contenidos

- [Características](#-características)
- [Arquitectura del proyecto](#-arquitectura-del-proyecto)
- [Requisitos previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Configuración](#-configuración)
- [Estructura de archivos](#-estructura-de-archivos)
- [Módulos](#-módulos)
- [Pipeline de datos](#-pipeline-de-datos)
- [Hotkeys](#-hotkeys)
- [Pendientes / Roadmap](#-pendientes--roadmap)

---

## ✨ Características

| Característica | Detalle |
|---|---|
| 🖥️ Captura de pantalla en tiempo real | Captura una zona configurable de cualquier ventana activa |
| 🔍 OCR con PaddleOCR | Extracción de texto optimizada para chats (Twitch, Discord, etc.) |
| 🤖 Traducción con LLM local | Usa Ollama (`llama3.2` por defecto) sin enviar datos a la nube |
| 🪟 Overlay siempre visible | Ventana transparente, sin bordes, sobre cualquier aplicación |
| ✍️ Entrada inversa | Escribe en tu idioma y envía la traducción al portapapeles |
| ⚙️ Configuración en vivo | Panel de ajustes sin reiniciar la aplicación |
| 🧠 Memoria de contexto | Historial de mensajes para traducciones más coherentes |
| ⌨️ Hotkey global | Muestra/oculta el overlay con `Ctrl+Shift+T` (configurable) |
| 💾 Persistencia de ajustes | Configuración guardada en `settings.json` automáticamente |

---

## 🏗️ Arquitectura del proyecto

```
WEBCductor/
│
├── main.py                          # Punto de entrada — orquesta todos los módulos
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # AppSettings (dataclass) + carga/guardado JSON
│
├── modules/
│   ├── __init__.py
│   │
│   ├── screen_capture/              # Captura de pantalla
│   │   ├── __init__.py
│   │   ├── capture_engine.py        # QThread que emite frames a intervalos
│   │   └── window_selector.py       # Lista ventanas activas (Win32)
│   │
│   ├── ocr/                         # Reconocimiento óptico de caracteres
│   │   ├── __init__.py
│   │   ├── ocr_engine.py            # PaddleOCR wrapper → lista de OCRLine
│   │   └── error_corrector.py       # Corrección de errores OCR comunes
│   │
│   ├── parser/                      # Parseo de mensajes de chat
│   │   ├── __init__.py
│   │   ├── message_parser.py        # Extrae usuario + mensaje → ChatMessage
│   │   └── username_patterns.py     # Patrones regex por plataforma (Twitch, Discord…)
│   │
│   ├── history/                     # Memoria de conversación
│   │   ├── __init__.py
│   │   └── context_memory.py        # Cola FIFO con deduplicación
│   │
│   ├── translation/                 # Motor de traducción LLM
│   │   ├── __init__.py
│   │   ├── llm_engine.py            # LLMEngine + TranslationWorker (QThread)
│   │   └── ollama_checker.py        # Verifica que Ollama esté disponible
│   │
│   └── overlay/                     # Interfaz gráfica (PyQt6)
│       ├── __init__.py
│       ├── overlay_window.py        # Ventana principal transparente
│       ├── message_widget.py        # Widget de un mensaje traducido
│       ├── reverse_input.py         # Barra de entrada inversa
│       ├── settings_panel.py        # Panel de configuración en vivo
│       └── wizard.py                # Asistente de configuración inicial
│
└── assets/
    └── styles/
        └── overlay.qss              # Hoja de estilos Qt (tema oscuro)
```

---

## 📦 Requisitos previos

### Sistema operativo
- **Windows 10 / 11** (requerido por `pywin32` y la captura de ventanas Win32)

### Software externo
- [**Python 3.11+**](https://www.python.org/downloads/)
- [**Ollama**](https://ollama.com/) instalado y corriendo localmente
- Modelo de Ollama descargado:
  ```bash
  ollama pull llama3.2
  ```

---

## 🚀 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/Sebas-r11/WEBCductor.git
cd WEBCductor

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate      # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

> ⚠️ **PaddleOCR** puede tardar varios minutos en instalar y descarga modelos en el primer uso (~1 GB).

---

## ▶️ Uso

```bash
# Asegúrate de que Ollama esté corriendo:
ollama serve

# En otra terminal, lanza WEBCductor:
python main.py
```

Al iniciar:
1. Se abre el **asistente de configuración** (wizard)
2. Seleccionas la ventana a capturar y la zona de pantalla
3. Configuras idiomas de origen y destino, y el modelo Ollama
4. El overlay aparece y empieza a traducir en tiempo real

---

## ⚙️ Configuración

Los ajustes se guardan automáticamente en `settings.json` al cerrar la app.

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `ollama_model` | `llama3.2` | Modelo Ollama a usar |
| `source_language` | `English` | Idioma origen del chat |
| `target_language` | `Spanish` | Idioma destino de la traducción |
| `history_size` | `35` | Mensajes en la memoria de contexto |
| `overlay_opacity` | `0.85` | Opacidad del overlay (0.1 – 1.0) |
| `capture_interval_ms` | `1000` | Intervalo de captura en milisegundos |
| `username_pattern` | `twitch` | Patrón de parseo de nombres de usuario |
| `hotkey_toggle` | `ctrl+shift+t` | Hotkey para mostrar/ocultar overlay |
| `font_size` | `12` | Tamaño de fuente en el overlay |
| `capture_zone` | `{x:0,y:0,w:400,h:300}` | Zona de captura en píxeles |

También puedes editar `settings.json` manualmente mientras la app no está corriendo.

---

## 📂 Módulos

### `config/settings.py`
Define `AppSettings` como un `dataclass` con valores por defecto. Provee métodos `.save()` y `.load()` con serialización JSON. Si el archivo no existe, devuelve valores por defecto sin error.

### `modules/screen_capture/capture_engine.py`
`CaptureEngine` es un `QThread` que usa `mss` para capturar la zona de pantalla configurada a intervalos regulares. Emite la señal `frame_ready(np.ndarray)` con cada frame capturado.

### `modules/screen_capture/window_selector.py`
Usa `pywin32` para enumerar ventanas activas del sistema. Permite al wizard listar y seleccionar la ventana objetivo.

### `modules/ocr/ocr_engine.py`
Wrapper sobre `PaddleOCR`. El método `.extract(frame)` devuelve una lista de `OCRLine` con el texto detectado y su posición.

### `modules/ocr/error_corrector.py`
Aplica correcciones heurísticas al texto OCR (sustituciones de caracteres confundibles, limpieza de ruido).

### `modules/parser/message_parser.py`
`MessageParser` aplica el patrón regex de la plataforma seleccionada para separar `usuario` y `mensaje`. Devuelve objetos `ChatMessage`.

### `modules/parser/username_patterns.py`
Diccionario de patrones regex por plataforma. Incluye `twitch`, `discord` y soporte para patrones personalizados.

### `modules/history/context_memory.py`
`ContextMemory` mantiene una cola FIFO de `ChatMessage` con tamaño máximo configurable. Detecta duplicados y formatea el historial para incluirlo en el prompt del LLM.

### `modules/translation/llm_engine.py`
- `TranslationWorker`: `QThread` de un solo uso que llama a `ollama.chat()` de forma asíncrona.
- `LLMEngine`: gestiona los workers, construye el prompt con contexto y conecta las señales `translation_ready` / `translation_error` a los callbacks del overlay.

### `modules/translation/ollama_checker.py`
Verifica que el servidor Ollama esté disponible y que el modelo configurado exista antes de iniciar la app.

### `modules/overlay/overlay_window.py`
`OverlayWindow`: ventana `FramelessWindowHint + WindowStaysOnTopHint` con fondo translúcido. Contiene la barra de título arrastrable, el scroll de mensajes y la barra de entrada inversa.

### `modules/overlay/message_widget.py`
Widget que muestra un mensaje traducido con el nombre del usuario, texto original y traducción.

### `modules/overlay/reverse_input.py`
`ReverseInputBar`: permite escribir texto en el idioma destino, traducirlo al idioma origen y copiarlo al portapapeles con un clic.

### `modules/overlay/settings_panel.py`
Panel de configuración que abre sobre el overlay. Permite cambiar todos los parámetros de `AppSettings` en vivo sin reiniciar.

### `modules/overlay/wizard.py`
`SetupWizard`: asistente multipágina (PyQt6 `QWizard`) que guía la configuración inicial: selección de ventana, zona de captura, idiomas y modelo.

---

## 🔄 Pipeline de datos

```
[Pantalla]
    │
    ▼  cada capture_interval_ms
[CaptureEngine] ──frame_ready──▶ [on_frame()]
                                      │
                                      ▼
                                 [OCREngine.extract()]
                                      │ lista de OCRLine
                                      ▼
                                 [error_corrector.correct()]
                                      │ texto limpio
                                      ▼
                                 [MessageParser.parse()]
                                      │ lista de ChatMessage
                                      ▼
                                 [ContextMemory.is_duplicate()]
                                      │ mensajes nuevos
                                      ▼
                                 [LLMEngine.translate_async()]
                                      │ QThread → Ollama
                                      ▼
                                 [OverlayWindow.add_message()]
                                      │
                                      ▼
                                 [MessageWidget en el overlay]
```

---

## ⌨️ Hotkeys

| Hotkey | Acción |
|---|---|
| `Ctrl+Shift+T` | Mostrar / ocultar el overlay |

El hotkey se puede cambiar en el panel de configuración o en `settings.json`.

---

## 🗺️ Pendientes / Roadmap

- [ ] Eliminar el archivo `modules/translation/llm.engine.py` (nombre inválido, duplicado de `llm_engine.py`)
- [ ] Soporte multi-plataforma (Linux / macOS) — actualmente requiere Windows
- [ ] Tests unitarios para `MessageParser`, `ContextMemory` y `LLMEngine`
- [ ] Soporte para múltiples zonas de captura simultáneas
- [ ] Empaquetado como ejecutable con PyInstaller (`.exe`)
- [ ] Soporte para más modelos Ollama configurables desde el wizard
- [ ] Internacionalización (i18n) de la interfaz

---

## 📄 Licencia

Este proyecto no tiene licencia definida aún. Por defecto, todos los derechos pertenecen al autor.

---

<div align="center">
  Hecho con 🧠 + 🐍 + PyQt6 + PaddleOCR + Ollama
</div>
