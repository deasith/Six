# 🤖 JARVIS — tu asistente para Windows (sin micrófono)

Un asistente de escritorio al que le **escribes** (no necesitas micro) y él te
responde **por escrito y en voz alta**. La voz usa la que ya trae Windows, así
que no tienes que instalar nada extra.

## ▶️ Cómo abrirlo

1. Instala **Python 3** desde https://www.python.org/downloads/
   → Al instalar, marca la casilla **"Add Python to PATH"**.
2. Haz **doble clic en `jarvis.bat`**.
   (O abre CMD en esta carpeta y escribe: `python jarvis.py`)

Se abre una ventana oscura estilo Jarvis. Escribe abajo y pulsa **Enter**.

## 🧠 Activar el cerebro de IA (gratis)

Para que responda cualquier pregunta necesita una clave de IA gratuita:

1. Pulsa el botón **"🔑 Clave IA"** dentro de la app.
2. Pulsa **"Abrir Groq"**, crea una cuenta gratis (sin tarjeta) en
   https://console.groq.com , ve a **API Keys** y crea una.
3. Pega la clave en la app y pulsa **Guardar**.

Sin clave, Jarvis igual funciona con sus comandos rápidos.

## 💬 Qué le puedes decir

| Escribes… | Jarvis hace… |
|---|---|
| `qué hora es` | te dice la hora |
| `qué día es hoy` | te dice la fecha |
| `abre la calculadora` | abre programas (calculadora, bloc de notas, navegador, paint, cmd, explorador…) |
| `busca recetas de pizza` | busca en Google |
| `pon música relajante en youtube` | abre YouTube |
| `cuánto es 8 * 7` | calcula |
| `explícame los agujeros negros` | responde con IA (necesita clave) |
| `ayuda` | lista de lo que puede hacer |
| `adiós` | se cierra |

## 🔊 Voz

- Botón **"🔊 Voz: ON/OFF"** para activar o silenciar la voz.
- La voz nativa de Windows funciona sin instalar nada.
- ¿Quieres mejor voz? En CMD: `pip install pyttsx3` y reinicia Jarvis.

## ❓ Problemas

- **No se abre / dice que falta Python** → instala Python y marca *"Add Python
  to PATH"*.
- **No habla** → revisa el volumen y que el botón diga *"🔊 Voz: ON"*.
- **La IA da error de clave** → vuelve a *"🔑 Clave IA"* y pega la clave bien.
