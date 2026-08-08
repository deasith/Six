# 🤖 JARVIS — tu asistente para Windows (sin micrófono)

> Proyecto **independiente y desde cero**. Todo lo de Jarvis vive en esta
> carpeta (`jarvis/`) y no depende de ningún otro archivo del repositorio.
> Solo necesitas `jarvis.py` (y opcionalmente `jarvis.bat` para abrirlo con
> doble clic).

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
| `abre gmail` / `abre whatsapp` | abre webs (gmail, whatsapp, youtube, maps, netflix, instagram…) |
| `busca recetas de pizza` | busca en Google |
| `pon música relajante en youtube` | abre YouTube |
| `clima` o `clima en Madrid` | te dice el tiempo (sin clave) |
| `recuérdame en 10 minutos sacar la pizza` | te avisa cuando toca |
| `cuánto es 8 * 7` | calcula |
| `cuéntame un chiste` | chiste al instante |
| `explícame los agujeros negros` | responde con IA (necesita clave) |
| `ayuda` | lista de lo que puede hacer |
| `adiós` | se cierra |

## 🖥️ Conocimiento y acceso a tu PC

Jarvis ahora "conoce" tu equipo y puede acceder a cosas (de forma segura):

| Escribes… | Jarvis hace… |
|---|---|
| `info del sistema` | resumen: equipo, RAM, disco, batería, IP |
| `cuánta batería` · `cuánto espacio` · `cuánta ram` · `mi ip` | datos concretos |
| `qué consume mi pc` | programas que más memoria usan |
| `abre la carpeta descargas` | abre carpetas (escritorio, documentos, descargas, imágenes, música, vídeos) |
| `busca el archivo factura` → `abre el 1` | busca archivos en tus carpetas y los abre por número |
| `sube el volumen` · `baja el volumen` · `silencia` | control de volumen |
| `bloquea la pantalla` | bloquea Windows |

Además, cuando la IA está activa, **ya sabe** tu sistema, hora, batería y disco,
así que responde teniéndolo en cuenta.

> 🔒 **Seguridad:** Jarvis solo puede hacer estas acciones concretas. La IA
> **no** ejecuta comandos sueltos en tu PC, así que no puede romper nada.

## 🔑 Poner la clave de IA (con botón Pegar)

En **"🔑 Clave IA"** ya no hace falta escribirla letra por letra: copia la
clave en la web de Groq (Ctrl+C) y en la app pulsa **"📋 Pegar"** (o clic
derecho → Pegar).

## 🔊 Voz (Jarvis te habla)

- Botón **"🔊 Voz: ON/OFF"** para activar o silenciar la voz.
- La voz nativa de Windows funciona sin instalar nada.
- ¿Quieres mejor voz? En CMD: `pip install pyttsx3` y reinicia Jarvis.

## 🎤 Micrófono (hablarle a Jarvis)

- Pulsa **"🎤 Hablar"**, di tu frase y Jarvis la escribe y responde solo.
- Funciona con el reconocimiento nativo de Windows **sin instalar nada**.
- Para la **mejor calidad** (reconocimiento por Google, muy bueno en español),
  en CMD: `pip install SpeechRecognition pyaudio` y reinicia Jarvis.
  Jarvis calibra el ruido de fondo y elige la mejor interpretación.
- La barra de estado de abajo te dice si el micro está listo.

## 🧩 Te entiende aunque te equivoques

Jarvis tiene **reconocimiento tolerante a erratas**: si escribes o dices
*"ke ora es"*, *"cuentame un chizte"*, *"avre la calculadora"*, *"abre whatsap"*
o *"suve el volumen"*, igual te entiende. Y si de verdad no es un comando,
se lo pasa a la IA sin molestarte.

## ❓ Problemas

- **No se abre / dice que falta Python** → instala Python y marca *"Add Python
  to PATH"*.
- **No habla** → revisa el volumen y que el botón diga *"🔊 Voz: ON"*.
- **La IA da error de clave** → vuelve a *"🔑 Clave IA"* y pega la clave bien.
