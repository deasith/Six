"""
JARVIS - asistente de escritorio para Windows (sin microfono).

Escribes lo que quieres y Jarvis te responde por escrito Y en voz alta.
No necesitas microfono: la entrada es por teclado. La voz de salida usa
la voz que ya trae Windows, asi que NO tienes que instalar nada extra.

Como usarlo en Windows:
    1. Instala Python 3 desde https://www.python.org/downloads/
       (marca la casilla "Add Python to PATH" al instalar).
    2. Haz doble clic en "jarvis.bat" (o abre CMD y escribe: python jarvis.py)

Cerebro con IA (opcional pero recomendado):
    Pega una clave gratis de Groq en el boton "Clave IA".
    Consiguela en https://console.groq.com  (gratis, sin tarjeta).
    Sin clave, Jarvis igual funciona con sus comandos rapidos.

Voz (opcional, mejor calidad):
    Si instalas 'pyttsx3' (pip install pyttsx3) la voz suena mejor y
    puedes elegirla. Si no, Jarvis usa la voz nativa de Windows via
    PowerShell, que funciona sin instalar nada.
"""

import datetime
import json
import os
import platform
import queue
import re
import ssl
import subprocess
import threading
import urllib.parse
import urllib.request
import webbrowser

import tkinter as tk
from tkinter import scrolledtext

# ----------------------------------------------------------------------------
# Configuracion y colores (tema oscuro estilo "Jarvis")
# ----------------------------------------------------------------------------
ARCHIVO_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "jarvis_config.json")

FONDO = "#0b1220"
FONDO_CHAT = "#0f1830"
PANEL = "#131f3d"
ACENTO = "#39d0ff"       # cian estilo Jarvis
ACENTO2 = "#7c5cff"      # violeta
TEXTO = "#e8f0ff"
TEXTO_TENUE = "#8aa0c8"
USUARIO = "#ffd479"      # amarillo suave para lo que escribes tu
VERDE = "#4be089"
ROJO = "#ff6b6b"

ES_WINDOWS = platform.system() == "Windows"


def cargar_config():
    try:
        with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_config(cfg):
    try:
        with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def limpiar_clave_api(txt):
    """Quita espacios, saltos de linea, comillas o un 'Bearer ' de mas."""
    if not txt:
        return ""
    txt = txt.strip().strip('"').strip("'").strip()
    if txt.lower().startswith("bearer "):
        txt = txt[7:].strip()
    return txt


# ----------------------------------------------------------------------------
# VOZ (texto a voz). Funciona sin instalar nada en Windows.
# ----------------------------------------------------------------------------
class Voz:
    """Reproduce texto en voz alta. Intenta, por orden:
       1) pyttsx3  (mejor, si esta instalado)
       2) PowerShell System.Speech  (nativo de Windows, sin instalar nada)
       3) macOS 'say' / Linux 'spd-say' o 'espeak'  (por si acaso)
    Cada frase se dice en un hilo aparte para no congelar la ventana.
    """

    def __init__(self):
        self.activa = True
        self.cola = queue.Queue()
        self.motor = None
        self.metodo = "ninguno"
        self._preparar_pyttsx3()
        if self.metodo == "ninguno" and ES_WINDOWS:
            self.metodo = "powershell"
        if self.metodo == "ninguno" and platform.system() == "Darwin":
            self.metodo = "macos"
        if self.metodo == "ninguno":
            self.metodo = "linux"
        self.hilo = threading.Thread(target=self._bucle, daemon=True)
        self.hilo.start()

    def _preparar_pyttsx3(self):
        try:
            import pyttsx3
            self.motor = pyttsx3.init()
            # Intenta elegir una voz en espanol si existe.
            try:
                for v in self.motor.getProperty("voices"):
                    datos = (getattr(v, "id", "") + " " +
                             getattr(v, "name", "")).lower()
                    if "spanish" in datos or "espa" in datos or "helena" in datos \
                            or "sabina" in datos or "es-" in datos or "es_" in datos:
                        self.motor.setProperty("voice", v.id)
                        break
            except Exception:
                pass
            self.motor.setProperty("rate", 175)
            self.metodo = "pyttsx3"
        except Exception:
            self.motor = None

    def decir(self, texto):
        if not texto:
            return
        # No leer bloques de codigo enormes ni URLs larguisimas.
        limpio = re.sub(r"`{1,3}[^`]*`{1,3}", " ", texto)
        limpio = re.sub(r"https?://\S+", " un enlace ", limpio)
        limpio = limpio.strip()
        if limpio:
            self.cola.put(limpio)

    def callar(self):
        # Vacia la cola pendiente.
        try:
            while True:
                self.cola.get_nowait()
        except queue.Empty:
            pass

    def _bucle(self):
        while True:
            texto = self.cola.get()
            if not self.activa:
                continue
            try:
                if self.metodo == "pyttsx3" and self.motor:
                    self.motor.say(texto)
                    self.motor.runAndWait()
                elif self.metodo == "powershell":
                    self._decir_powershell(texto)
                elif self.metodo == "macos":
                    subprocess.run(["say", texto], check=False)
                elif self.metodo == "linux":
                    if not self._run(["spd-say", "-w", texto]):
                        self._run(["espeak", "-v", "es", texto])
            except Exception:
                pass

    def _run(self, cmd):
        try:
            subprocess.run(cmd, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def _decir_powershell(self, texto):
        # Usa la voz nativa de Windows. Escribimos el texto a un archivo
        # temporal para evitar problemas con comillas y acentos.
        seguro = texto.replace("\x00", " ")
        script = (
            "Add-Type -AssemblyName System.Speech;"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "try { $s.SelectVoiceByHints('NotSet','NotSet',0,"
            "[System.Globalization.CultureInfo]'es-ES') } catch {};"
            "$t = [Console]::In.ReadToEnd();"
            "$s.Speak($t);"
        )
        try:
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", script],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.communicate(input=seguro.encode("utf-8", errors="ignore"))
        except Exception:
            pass


# ----------------------------------------------------------------------------
# COMANDOS RAPIDOS (funcionan sin internet ni clave de IA)
# ----------------------------------------------------------------------------
DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Programas comunes de Windows que Jarvis puede abrir.
PROGRAMAS = {
    "bloc de notas": "notepad", "notepad": "notepad", "notas": "notepad",
    "calculadora": "calc", "calc": "calc",
    "paint": "mspaint", "pintura": "mspaint",
    "explorador": "explorer", "archivos": "explorer", "carpeta": "explorer",
    "cmd": "cmd", "terminal": "cmd", "consola": "cmd",
    "navegador": "__navegador__", "chrome": "__navegador__",
    "word": "winword", "excel": "excel", "powerpoint": "powerpnt",
    "spotify": "spotify", "configuracion": "ms-settings:", "ajustes": "ms-settings:",
}


def comando_local(texto):
    """Devuelve una respuesta si el texto es un comando rapido, o None
    si hay que pasarselo a la IA."""
    t = texto.lower().strip()

    # --- Hora y fecha ---
    if re.search(r"\bque hora\b|\bla hora\b|\bhora es\b", t):
        ahora = datetime.datetime.now()
        return "Son las %02d:%02d." % (ahora.hour, ahora.minute)

    if re.search(r"\bque dia\b|\bque fecha\b|\bla fecha\b|\bfecha de hoy\b|\bque dia es\b", t):
        hoy = datetime.date.today()
        return "Hoy es %s %d de %s de %d." % (
            DIAS[hoy.weekday()], hoy.day, MESES[hoy.month - 1], hoy.year)

    # --- Abrir programas ---
    m = re.search(r"\b(abre|abrir|inicia|iniciar|ejecuta|lanza)\b\s+(.+)", t)
    if m:
        objetivo = m.group(2).strip().strip(".!?")
        # quita "el/la/mi" del principio
        objetivo = re.sub(r"^(el|la|mi|un|una)\s+", "", objetivo)
        return abrir_programa(objetivo)

    # --- Buscar en la web ---
    m = re.search(r"\b(busca|buscar|google|googlea|investiga)\b\s+(.+)", t)
    if m:
        consulta = m.group(2).strip()
        url = "https://www.google.com/search?q=" + urllib.parse.quote(consulta)
        webbrowser.open(url)
        return "Buscando \"%s\" en tu navegador." % consulta

    # --- YouTube ---
    m = re.search(r"\b(pon|reproduce|escuchar|ver)\b\s+(.+)\s+en youtube", t)
    if not m:
        m = re.search(r"\byoutube\b\s+(.+)", t)
        if m:
            consulta = m.group(1)
        else:
            consulta = None
    else:
        consulta = m.group(2)
    if consulta:
        url = "https://www.youtube.com/results?search_query=" + \
            urllib.parse.quote(consulta.strip())
        webbrowser.open(url)
        return "Abriendo YouTube con \"%s\"." % consulta.strip()

    # --- Calculadora sencilla ("cuanto es 5 * 3", "calcula 12/4") ---
    m = re.search(r"\b(cuanto es|calcula|calcular)\b\s+(.+)", t)
    if m:
        r = calcular(m.group(2))
        if r is not None:
            return r

    # --- Saludos y despedidas rapidas ---
    if re.fullmatch(r"(hola|hey|buenas|hola jarvis|jarvis)\W*", t):
        return ("Hey. Aqui estoy, sin cafe pero con ganas. Dime que necesitas.")
    if re.search(r"\b(adios|hasta luego|chao|nos vemos|apagate|cierra)\b", t):
        return "__salir__"
    if re.search(r"\b(gracias|muchas gracias)\b", t):
        return "A mandar. Para algo soy tu asistente favorito (y el unico)."

    # --- Ayuda ---
    if re.fullmatch(r"(ayuda|help|comandos|que puedes hacer)\W*", t):
        return ("Puedo: decirte la hora y la fecha, abrir programas "
                "(\"abre la calculadora\"), buscar en la web (\"busca gatos\"), "
                "poner videos (\"pon musica en youtube\"), calcular "
                "(\"cuanto es 8*7\") y, si pones tu clave de IA, responder "
                "cualquier pregunta.")

    return None  # -> lo maneja la IA


def abrir_programa(nombre):
    clave = None
    for k in PROGRAMAS:
        if k in nombre:
            clave = k
            break
    if clave is None:
        # Intenta abrirlo tal cual (por si es un programa instalado).
        objetivo = nombre.split()[0] if nombre else ""
        if ES_WINDOWS and objetivo:
            try:
                os.startfile(objetivo)  # type: ignore[attr-defined]
                return "Intentando abrir \"%s\"." % nombre
            except Exception:
                pass
        return ("No conozco \"%s\". Prueba: calculadora, bloc de notas, "
                "navegador, explorador, cmd, paint." % nombre)

    destino = PROGRAMAS[clave]
    try:
        if destino == "__navegador__":
            webbrowser.open("https://www.google.com")
            return "Abriendo el navegador."
        if destino.startswith("ms-settings:"):
            if ES_WINDOWS:
                os.startfile(destino)  # type: ignore[attr-defined]
            return "Abriendo la configuracion."
        if ES_WINDOWS:
            os.startfile(destino)  # type: ignore[attr-defined]
        else:
            subprocess.Popen([destino])
        return "Listo, abriendo %s." % clave
    except Exception:
        return "No pude abrir %s. Puede que no este instalado." % clave


def calcular(expr):
    """Evalua una operacion matematica simple de forma segura."""
    expr = expr.lower()
    expr = expr.replace("mas", "+").replace("menos", "-")
    expr = expr.replace("por", "*").replace("entre", "/").replace("dividido", "/")
    expr = expr.replace("x", "*").replace("^", "**").replace(",", ".")
    # Solo permitimos numeros y operadores basicos.
    if not re.fullmatch(r"[0-9\.\s\+\-\*/\(\)]+", expr):
        return None
    try:
        resultado = eval(expr, {"__builtins__": {}}, {})  # entorno vacio = seguro
    except Exception:
        return None
    if isinstance(resultado, float) and resultado.is_integer():
        resultado = int(resultado)
    return "El resultado es %s." % resultado


# ----------------------------------------------------------------------------
# CEREBRO IA (Groq, gratis, sin tarjeta)
# ----------------------------------------------------------------------------
def preguntar_ia(historial, clave_api):
    turnos = [m for m in historial if m.get("role") in ("user", "assistant")][-20:]
    mensajes = [{"role": "system", "content":
                 "Eres JARVIS, un asistente de escritorio con IA, inspirado en "
                 "el de las peliculas de Iron Man, pero en tu propia version: "
                 "colega, gracioso y con un sarcasmo elegante. Hablas en espanol "
                 "y SIEMPRE tuteas al usuario (nada de 'usted'), como si fuera tu "
                 "amigo. Sueltas comentarios ingeniosos y algo de sarcasmo carinoso, "
                 "pero SIEMPRE ayudas de verdad y das la informacion correcta. "
                 "No te pases de largo: respuestas utiles y con chispa, no ladrillos "
                 "de texto. Si algo es obvio, puedes picarle un poco con humor. "
                 "Nunca eres borde ni ofensivo; el sarcasmo es de buen rollo. "
                 "De vez en cuando puedes rematar con una frase con estilo, como "
                 "haria un asistente de peli de ciencia ficcion."}]
    mensajes.extend({"role": m["role"], "content": m["content"]} for m in turnos)
    cuerpo = {
        "model": "llama-3.3-70b-versatile",
        "messages": mensajes,
        "max_tokens": 1024,
    }
    clave = limpiar_clave_api(clave_api)
    datos = json.dumps(cuerpo).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=datos, method="POST",
        headers={"Authorization": "Bearer " + clave,
                 "content-type": "application/json",
                 "User-Agent": "Jarvis/1.0 (Windows)"})
    try:
        import certifi
        contexto = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            contexto = ssl.create_default_context()
        except Exception:
            contexto = None
    with urllib.request.urlopen(req, timeout=60, context=contexto) as resp:
        r = json.loads(resp.read().decode("utf-8"))
    opciones = r.get("choices", [])
    if not opciones:
        return "No obtuve respuesta de la IA. Intenta de nuevo."
    return opciones[0].get("message", {}).get("content", "").strip() or "(sin texto)"


# ----------------------------------------------------------------------------
# INTERFAZ (ventana de chat con Tkinter)
# ----------------------------------------------------------------------------
class Jarvis:
    def __init__(self):
        self.config = cargar_config()
        self.voz = Voz()
        self.voz.activa = self.config.get("voz", True)
        self.historial = []

        self.ventana = tk.Tk()
        self.ventana.title("JARVIS")
        self.ventana.configure(bg=FONDO)
        # Ajusta el tamano para que SIEMPRE quepa en la pantalla (dejando
        # espacio para la barra de tareas de Windows), y centra la ventana.
        ancho = 760
        alto_pantalla = self.ventana.winfo_screenheight()
        alto = min(620, alto_pantalla - 90)
        pos_x = max(0, (self.ventana.winfo_screenwidth() - ancho) // 2)
        pos_y = 10
        self.ventana.geometry("%dx%d+%d+%d" % (ancho, alto, pos_x, pos_y))
        self.ventana.minsize(520, 380)
        self._construir()
        self._saludo_inicial()

    # ---- construccion de la interfaz ----
    def _construir(self):
        cab = tk.Frame(self.ventana, bg=FONDO)
        cab.pack(fill="x", padx=16, pady=(14, 6))

        tk.Label(cab, text="◆ J.A.R.V.I.S.", bg=FONDO, fg=ACENTO,
                 font=("Consolas", 20, "bold")).pack(side="left")
        tk.Label(cab, text="  asistente de escritorio", bg=FONDO, fg=TEXTO_TENUE,
                 font=("Segoe UI", 10)).pack(side="left", pady=(8, 0))

        botones = tk.Frame(cab, bg=FONDO)
        botones.pack(side="right")

        self.btn_voz = tk.Button(
            botones, text=self._texto_voz(), command=self.alternar_voz,
            bg=PANEL, fg=TEXTO, activebackground=ACENTO2, relief="flat",
            font=("Segoe UI", 9, "bold"), padx=10, pady=4, cursor="hand2")
        self.btn_voz.pack(side="left", padx=4)

        tk.Button(botones, text="🔑 Clave IA", command=self.pedir_clave,
                  bg=PANEL, fg=TEXTO, activebackground=ACENTO2, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=10, pady=4,
                  cursor="hand2").pack(side="left", padx=4)

        tk.Button(botones, text="🧹 Limpiar", command=self.limpiar,
                  bg=PANEL, fg=TEXTO, activebackground=ACENTO2, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=10, pady=4,
                  cursor="hand2").pack(side="left", padx=4)

        # IMPORTANTE: empaquetamos la barra de escribir ANTES que el chat y
        # anclada abajo (side="bottom"). Asi Tkinter le reserva su sitio
        # primero y nunca queda tapada, aunque la ventana sea pequena.
        barra = tk.Frame(self.ventana, bg=FONDO)
        barra.pack(side="bottom", fill="x", padx=16, pady=(6, 14))

        self.entrada = tk.Entry(
            barra, bg=PANEL, fg=TEXTO, relief="flat", font=("Segoe UI", 13),
            insertbackground=ACENTO)
        self.entrada.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entrada.bind("<Return>", lambda e: self.enviar())
        self.entrada.focus_set()

        self.btn_enviar = tk.Button(
            barra, text="Enviar  ➤", command=self.enviar,
            bg=ACENTO, fg=FONDO, activebackground=ACENTO2, relief="flat",
            font=("Segoe UI", 11, "bold"), padx=18, pady=6, cursor="hand2")
        self.btn_enviar.pack(side="right")

        # Zona del chat (rellena el espacio que queda arriba de la barra)
        self.chat = scrolledtext.ScrolledText(
            self.ventana, bg=FONDO_CHAT, fg=TEXTO, relief="flat",
            font=("Segoe UI", 12), wrap="word", state="disabled",
            padx=14, pady=12, insertbackground=TEXTO)
        self.chat.pack(side="top", fill="both", expand=True, padx=16, pady=8)
        self.chat.tag_config("jarvis", foreground=ACENTO,
                             font=("Segoe UI", 12, "bold"))
        self.chat.tag_config("jarvis_txt", foreground=TEXTO)
        self.chat.tag_config("tu", foreground=USUARIO,
                             font=("Segoe UI", 12, "bold"))
        self.chat.tag_config("tu_txt", foreground=USUARIO)
        self.chat.tag_config("sistema", foreground=TEXTO_TENUE,
                             font=("Segoe UI", 10, "italic"))

    def _texto_voz(self):
        return "🔊 Voz: ON" if self.voz.activa else "🔇 Voz: OFF"

    # ---- utilidades de chat ----
    def _escribir(self, quien, texto, tag_nombre, tag_txt):
        self.chat.config(state="normal")
        if self.chat.index("end-1c") != "1.0":
            self.chat.insert("end", "\n")
        self.chat.insert("end", quien + "  ", tag_nombre)
        self.chat.insert("end", texto + "\n", tag_txt)
        self.chat.config(state="disabled")
        self.chat.see("end")

    def msg_jarvis(self, texto, hablar=True):
        self._escribir("JARVIS", texto, "jarvis", "jarvis_txt")
        if hablar and self.voz.activa:
            self.voz.decir(texto)

    def msg_tu(self, texto):
        self._escribir("TU", texto, "tu", "tu_txt")

    def msg_sistema(self, texto):
        self.chat.config(state="normal")
        self.chat.insert("end", "\n" + texto + "\n", "sistema")
        self.chat.config(state="disabled")
        self.chat.see("end")

    def _saludo_inicial(self):
        hora = datetime.datetime.now().hour
        if hora < 12:
            saludo = "Buenos dias"
        elif hora < 20:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"
        self.msg_jarvis("%s. Jarvis en linea y listo para lo que necesites. "
                        "Puedo abrir programas, buscar en la web, decirte la hora "
                        "y, si me das mi cerebro de IA, resolverte casi cualquier "
                        "cosa. Tu solo escribe, que yo me encargo." % saludo)
        if not self.config.get("api_key"):
            self.msg_sistema("Oye, todavia estoy en modo basico. Pulsa "
                             "\"🔑 Clave IA\", pega una clave gratis de "
                             "console.groq.com y despierto mi cerebro completo. "
                             "Mientras tanto, hago los comandos rapidos sin quejarme "
                             "(mucho).")

    # ---- acciones ----
    def alternar_voz(self):
        self.voz.activa = not self.voz.activa
        if not self.voz.activa:
            self.voz.callar()
        self.btn_voz.config(text=self._texto_voz())
        self.config["voz"] = self.voz.activa
        guardar_config(self.config)

    def limpiar(self):
        self.historial = []
        self.chat.config(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.config(state="disabled")
        self.msg_jarvis("Listo, empecemos de nuevo.", hablar=False)

    def pedir_clave(self):
        top = tk.Toplevel(self.ventana)
        top.title("Clave de IA (Groq)")
        top.configure(bg=FONDO)
        top.geometry("520x230")
        top.transient(self.ventana)
        tk.Label(top, text="Pega tu clave gratis de Groq:", bg=FONDO, fg=TEXTO,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(18, 6))
        entrada = tk.Entry(top, bg=PANEL, fg=TEXTO, relief="flat",
                           font=("Consolas", 11), insertbackground=ACENTO)
        entrada.pack(fill="x", padx=18, ipady=6)
        entrada.insert(0, self.config.get("api_key", ""))
        tk.Label(top, text="Es gratis y sin tarjeta: entra a console.groq.com, "
                           "crea una cuenta,\nve a \"API Keys\" y crea una. "
                           "Luego pegala aqui.",
                 bg=FONDO, fg=TEXTO_TENUE, justify="left",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=10)

        def guardar():
            self.config["api_key"] = limpiar_clave_api(entrada.get())
            guardar_config(self.config)
            top.destroy()
            self.msg_jarvis("Clave guardada. Ya puedo responder cualquier pregunta.",
                            hablar=False)

        fila = tk.Frame(top, bg=FONDO)
        fila.pack(pady=8)
        tk.Button(fila, text="Abrir Groq", command=lambda: webbrowser.open(
            "https://console.groq.com/keys"),
            bg=PANEL, fg=TEXTO, relief="flat", font=("Segoe UI", 10, "bold"),
            padx=14, pady=6, cursor="hand2").pack(side="left", padx=6)
        tk.Button(fila, text="Guardar", command=guardar,
                  bg=ACENTO, fg=FONDO, relief="flat", font=("Segoe UI", 10, "bold"),
                  padx=20, pady=6, cursor="hand2").pack(side="left", padx=6)

    def enviar(self):
        texto = self.entrada.get().strip()
        if not texto:
            return
        self.entrada.delete(0, "end")
        self.msg_tu(texto)
        self.historial.append({"role": "user", "content": texto})

        # 1) Comandos rapidos (instantaneos, sin internet)
        respuesta = comando_local(texto)
        if respuesta == "__salir__":
            self.msg_jarvis("Hasta luego. Cerrando en un momento.")
            self.ventana.after(1800, self.ventana.destroy)
            return
        if respuesta is not None:
            self.msg_jarvis(respuesta)
            self.historial.append({"role": "assistant", "content": respuesta})
            return

        # 2) Cerebro IA
        if not self.config.get("api_key"):
            self.msg_jarvis("Para responder eso necesito el cerebro de IA. Pulsa "
                            "\"🔑 Clave IA\" y pega una clave gratis de Groq. "
                            "Mientras tanto prueba: \"que hora es\", \"abre la "
                            "calculadora\" o \"busca ...\".")
            return

        self.btn_enviar.config(state="disabled", text="Pensando…")
        self.msg_sistema("Jarvis esta pensando…")
        threading.Thread(target=self._pensar, daemon=True).start()

    def _pensar(self):
        try:
            respuesta = preguntar_ia(self.historial, self.config.get("api_key", ""))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                respuesta = "Tu clave de IA no es valida. Revisala en \"🔑 Clave IA\"."
            else:
                respuesta = "Error de la IA (codigo %s). Intenta de nuevo." % e.code
        except Exception:
            respuesta = ("No pude conectar con la IA. Revisa tu internet e "
                         "intenta otra vez.")
        # Volver al hilo de la ventana para actualizar la interfaz.
        self.ventana.after(0, self._mostrar_respuesta, respuesta)

    def _mostrar_respuesta(self, respuesta):
        self.btn_enviar.config(state="normal", text="Enviar  ➤")
        self.msg_jarvis(respuesta)
        self.historial.append({"role": "assistant", "content": respuesta})

    def run(self):
        self.ventana.mainloop()


if __name__ == "__main__":
    Jarvis().run()
