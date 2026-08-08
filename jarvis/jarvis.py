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
import getpass
import os
import platform
import queue
import re
import shutil
import socket
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

FONDO = "#070b16"          # fondo general, casi negro azulado
FONDO_CHAT = "#0b1424"     # zona de chat
PANEL = "#16243f"          # botones y cajas
PANEL_HOVER = "#20345c"    # botones al pasar el raton
ACENTO = "#3fd8ff"         # cian estilo Jarvis (arc reactor)
ACENTO2 = "#8a6cff"        # violeta
ACENTO3 = "#00131f"        # cian oscuro para el degradado
TEXTO = "#eaf2ff"
TEXTO_TENUE = "#8fa6cf"
USUARIO = "#ffd479"        # amarillo suave para lo que escribes tu
BURBUJA_J = "#12233c"      # fondo de los mensajes de Jarvis
BURBUJA_TU = "#1f2c22"     # fondo de tus mensajes
VERDE = "#57e39a"
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
# MICROFONO (voz a texto). Intenta, por orden:
#   1) speech_recognition + Google (gratis, muy bueno en espanol) si esta
#      instalado junto con pyaudio.
#   2) Reconocimiento nativo de Windows via PowerShell (sin instalar nada).
# ----------------------------------------------------------------------------
class Microfono:
    def __init__(self):
        self.metodo = "ninguno"
        self.sr = None
        try:
            import speech_recognition as sr
            import pyaudio  # noqa: F401  (necesario para usar el microfono)
            self.sr = sr
            self.metodo = "sr"
        except Exception:
            if ES_WINDOWS:
                self.metodo = "powershell"

    def disponible(self):
        return self.metodo != "ninguno"

    def como_activar(self):
        return ("Para el microfono con la mejor calidad instala esto en CMD:\n"
                "   pip install SpeechRecognition pyaudio\n"
                "y reinicia Jarvis.")

    def escuchar(self):
        """Bloqueante. Devuelve el texto reconocido, o marcadores:
        '' = no entendio, '__error__' = fallo, '__nomic__' = sin microfono."""
        if self.metodo == "sr":
            return self._escuchar_sr()
        if self.metodo == "powershell":
            return self._escuchar_powershell()
        return "__nomic__"

    def _escuchar_sr(self):
        sr = self.sr
        r = sr.Recognizer()
        try:
            with sr.Microphone() as fuente:
                r.adjust_for_ambient_noise(fuente, duration=0.4)
                audio = r.listen(fuente, timeout=6, phrase_time_limit=12)
        except Exception:
            return "__nomic__"
        try:
            return r.recognize_google(audio, language="es-ES").strip()
        except sr.UnknownValueError:
            return ""
        except Exception:
            return "__error__"

    def _escuchar_powershell(self):
        script = (
            "Add-Type -AssemblyName System.Speech;"
            "try { $ci = New-Object System.Globalization.CultureInfo 'es-ES';"
            "$r = New-Object System.Speech.Recognition.SpeechRecognitionEngine $ci }"
            "catch { $r = New-Object System.Speech.Recognition.SpeechRecognitionEngine };"
            "$r.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar));"
            "try { $r.SetInputToDefaultAudioDevice() } catch { exit };"
            "$res = $r.Recognize([TimeSpan]::FromSeconds(10));"
            "if ($res -ne $null) { [Console]::Out.Write($res.Text) }"
        )
        try:
            salida = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=25)
            texto = (salida.stdout or "").strip()
            return texto
        except Exception:
            return "__error__"


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

# Paginas web que Jarvis puede abrir por su nombre ("abre gmail").
WEBS = {
    "gmail": "https://mail.google.com", "correo": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "youtube": "https://www.youtube.com", "yt": "https://www.youtube.com",
    "maps": "https://maps.google.com", "mapas": "https://maps.google.com",
    "traductor": "https://translate.google.com",
    "instagram": "https://www.instagram.com", "insta": "https://www.instagram.com",
    "facebook": "https://www.facebook.com", "twitter": "https://twitter.com",
    "x": "https://twitter.com", "tiktok": "https://www.tiktok.com",
    "netflix": "https://www.netflix.com", "twitch": "https://www.twitch.tv",
    "github": "https://github.com", "chatgpt": "https://chat.openai.com",
    "wikipedia": "https://es.wikipedia.org", "amazon": "https://www.amazon.com",
    "reddit": "https://www.reddit.com", "gmail com": "https://mail.google.com",
}

# Chistes cortos para cuando no hay clave de IA (funcionan sin internet).
CHISTES = [
    "Va un pinguino andando por el desierto y dice: cuanta caspa.",
    "Que le dice un jardinero a otro? Disculpa, nos vemos las plantas.",
    "Como se dice pañuelo en japones? Saka-moko.",
    "Que hace una abeja en el gimnasio? Zum-ba.",
    "Tengo un chiste sobre el wifi, pero no se si va a conectar contigo.",
    "Un cero le dice a un ocho: bonito cinturon.",
    "Que le dice un semaforo a otro? No me mires que me pongo rojo.",
    "Me tome una pastilla para la memoria... aunque ya no me acuerdo para que.",
]


# ============================================================================
# CONOCIMIENTO Y ACCESO AL PC
# Un conjunto ACOTADO de acciones seguras: informar, abrir, buscar, controlar
# volumen, bloquear. No se ejecutan comandos arbitrarios de la IA.
# ============================================================================

def _bytes_a_gb(n):
    return n / (1024 ** 3)


def info_bateria():
    """Devuelve (porcentaje, enchufado) usando la API nativa de Windows.
    porcentaje puede ser None si el equipo no tiene bateria."""
    if not ES_WINDOWS:
        return None, None
    try:
        import ctypes

        class SPS(ctypes.Structure):
            _fields_ = [("ACLineStatus", ctypes.c_byte),
                        ("BatteryFlag", ctypes.c_byte),
                        ("BatteryLifePercent", ctypes.c_byte),
                        ("SystemStatusFlag", ctypes.c_byte),
                        ("BatteryLifeTime", ctypes.c_ulong),
                        ("BatteryFullLifeTime", ctypes.c_ulong)]

        estado = SPS()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(estado)):
            return None, None
        pct = estado.BatteryLifePercent
        if pct == 255:
            pct = None
        enchufado = estado.ACLineStatus == 1
        return pct, enchufado
    except Exception:
        return None, None


def info_ram():
    """Devuelve (total_gb, usada_gb, porcentaje) de la memoria RAM."""
    if ES_WINDOWS:
        try:
            import ctypes

            class MEM(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            m = MEM()
            m.dwLength = ctypes.sizeof(m)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            total = _bytes_a_gb(m.ullTotalPhys)
            usada = _bytes_a_gb(m.ullTotalPhys - m.ullAvailPhys)
            return total, usada, m.dwMemoryLoad
        except Exception:
            pass
    return None, None, None


def info_disco():
    """Espacio del disco principal: (total_gb, libre_gb, porcentaje_usado)."""
    ruta = "C:\\" if ES_WINDOWS else "/"
    try:
        u = shutil.disk_usage(ruta)
        total = _bytes_a_gb(u.total)
        libre = _bytes_a_gb(u.free)
        pct = round((u.used / u.total) * 100)
        return total, libre, pct
    except Exception:
        return None, None, None


def ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "desconocida"


def carpetas_usuario():
    """Rutas de las carpetas conocidas del usuario."""
    home = os.path.expanduser("~")
    perfil = os.environ.get("USERPROFILE", home)
    return {
        "escritorio": os.path.join(perfil, "Desktop"),
        "documentos": os.path.join(perfil, "Documents"),
        "descargas": os.path.join(perfil, "Downloads"),
        "imagenes": os.path.join(perfil, "Pictures"),
        "fotos": os.path.join(perfil, "Pictures"),
        "musica": os.path.join(perfil, "Music"),
        "videos": os.path.join(perfil, "Videos"),
        "casa": perfil, "inicio": perfil, "mi pc": perfil,
    }


def resumen_sistema():
    """Texto con el estado del equipo (para mostrar al usuario)."""
    partes = []
    try:
        usuario = getpass.getuser()
    except Exception:
        usuario = os.environ.get("USERNAME", "usuario")
    equipo = platform.node() or socket.gethostname()
    partes.append("Equipo: %s   Usuario: %s" % (equipo, usuario))
    partes.append("Sistema: %s %s" % (platform.system(), platform.release()))

    total, usada, pct = info_ram()
    if total:
        partes.append("RAM: %.1f GB usados de %.1f GB (%d%%)" % (usada, total, pct))

    dt, dl, dpct = info_disco()
    if dt:
        partes.append("Disco: %.0f GB libres de %.0f GB (%d%% ocupado)" %
                      (dl, dt, dpct))

    bat, enchufado = info_bateria()
    if bat is not None:
        estado = "cargando" if enchufado else "con bateria"
        partes.append("Bateria: %d%% (%s)" % (bat, estado))

    partes.append("CPU: %d nucleos   IP local: %s" %
                  (os.cpu_count() or 0, ip_local()))
    return "\n".join(partes)


def contexto_para_ia():
    """Resumen breve del equipo que se le da a la IA para que 'conozca' el PC."""
    try:
        usuario = getpass.getuser()
    except Exception:
        usuario = os.environ.get("USERNAME", "usuario")
    ahora = datetime.datetime.now()
    datos = ["Sistema: %s %s" % (platform.system(), platform.release()),
             "Usuario: %s" % usuario,
             "Fecha y hora actual: %s" % ahora.strftime("%A %d/%m/%Y %H:%M")]
    bat, ench = info_bateria()
    if bat is not None:
        datos.append("Bateria: %d%%%s" % (bat, " (cargando)" if ench else ""))
    dt, dl, _ = info_disco()
    if dt:
        datos.append("Disco libre: %.0f GB" % dl)
    return " | ".join(datos)


def procesos_top(limite=6):
    """Programas que mas memoria consumen (solo Windows, con tasklist)."""
    if not ES_WINDOWS:
        return "Esta funcion es solo para Windows."
    try:
        salida = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                                 capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return "No pude leer los procesos."
    uso = {}
    for linea in salida.splitlines():
        campos = [c.strip('"') for c in linea.split('","')]
        if len(campos) < 5:
            continue
        nombre = campos[0].replace('"', '')
        mem = re.sub(r"[^\d]", "", campos[4])
        if mem:
            uso[nombre] = uso.get(nombre, 0) + int(mem)  # KB
    if not uso:
        return "No pude leer los procesos."
    top = sorted(uso.items(), key=lambda x: x[1], reverse=True)[:limite]
    lineas = ["Lo que mas memoria usa ahora:"]
    for nombre, kb in top:
        lineas.append("• %s: %.0f MB" % (nombre, kb / 1024))
    return "\n".join(lineas)


def control_volumen(accion):
    """Sube, baja o silencia el volumen usando teclas multimedia (Windows)."""
    if not ES_WINDOWS:
        return "El control de volumen es solo para Windows."
    teclas = {"subir": 175, "bajar": 174, "silenciar": 173}
    codigo = teclas.get(accion)
    if codigo is None:
        return None
    veces = 1 if accion == "silenciar" else 5  # 5 pasos = un cambio notable
    try:
        script = ("$w = New-Object -ComObject WScript.Shell; "
                  "for ($i=0; $i -lt %d; $i++) "
                  "{ $w.SendKeys([char]%d) }" % (veces, codigo))
        subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=10)
        frases = {"subir": "Volumen arriba.", "bajar": "Volumen abajo.",
                  "silenciar": "Silencio (o de vuelta el sonido)."}
        return frases[accion]
    except Exception:
        return "No pude cambiar el volumen."


def bloquear_pc():
    if not ES_WINDOWS:
        return "Bloquear la pantalla es solo para Windows."
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], timeout=10)
        return "Pantalla bloqueada. Nos vemos a la vuelta."
    except Exception:
        return "No pude bloquear la pantalla."


def buscar_archivos(termino, limite=12):
    """Busca archivos cuyo nombre contenga 'termino' en las carpetas del
    usuario (escritorio, documentos, descargas, imagenes, musica, videos)."""
    termino = termino.lower().strip()
    if not termino:
        return []
    raices = []
    vistas = set()
    for ruta in carpetas_usuario().values():
        if ruta not in vistas and os.path.isdir(ruta):
            vistas.add(ruta)
            raices.append(ruta)
    encontrados = []
    for raiz in raices:
        for carpeta, _dirs, archivos in os.walk(raiz):
            # No bajar demasiado hondo para que sea rapido.
            if carpeta[len(raiz):].count(os.sep) > 3:
                _dirs[:] = []
                continue
            for a in archivos:
                if termino in a.lower():
                    encontrados.append(os.path.join(carpeta, a))
                    if len(encontrados) >= limite:
                        return encontrados
    return encontrados


def abrir_ruta(ruta):
    try:
        if ES_WINDOWS:
            os.startfile(ruta)  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta])
        return True
    except Exception:
        return False


def habilitar_menu_edicion(widget):
    """Anade clic derecho con Cortar/Copiar/Pegar a una caja de texto.
    Asi el usuario puede pegar la clave sin escribirla letra por letra."""
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cortar",
                     command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copiar",
                     command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Pegar",
                     command=lambda: widget.event_generate("<<Paste>>"))

    def mostrar(evento):
        try:
            menu.tk_popup(evento.x_root, evento.y_root)
        finally:
            menu.grab_release()

    widget.bind("<Button-3>", mostrar)


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

    # --- Abrir programas y paginas web ---
    m = re.search(r"\b(abre|abrir|inicia|iniciar|ejecuta|lanza|entra a|ve a)\b\s+(.+)", t)
    if m:
        objetivo = m.group(2).strip().strip(".!?")
        # quita "el/la/mi/la pagina" del principio
        objetivo = re.sub(r"^(el|la|mi|un|una|la pagina|la web|el sitio)\s+", "",
                          objetivo)
        return abrir_programa(objetivo)

    # --- Chistes (sin internet) ---
    if re.search(r"\bchiste\b|cuentame algo gracioso|hazme reir", t):
        import random
        return random.choice(CHISTES)

    # --- Conocimiento del PC ---
    if re.search(r"info del sistema|como esta mi (pc|computadora|ordenador)|"
                 r"estado del (pc|sistema|equipo)|informacion del (pc|sistema)|"
                 r"como estas de (memoria|recursos)", t):
        return resumen_sistema()

    if re.search(r"\bbateria\b|\bpila\b|cuanta carga", t):
        pct, ench = info_bateria()
        if pct is None:
            return "No detecto bateria (o eres un PC de mesa, campeon)."
        extra = " y esta cargando" if ench else ""
        aviso = "" if pct > 20 else " Enchufa eso ya, que se muere."
        return "Bateria al %d%%%s.%s" % (pct, extra, aviso)

    if re.search(r"cuanta (memoria|ram)|uso de (memoria|ram)|\bla ram\b", t):
        total, usada, pct = info_ram()
        if total:
            return "RAM: %.1f GB usados de %.1f GB (%d%%)." % (usada, total, pct)
        return "No pude leer la memoria."

    if re.search(r"cuanto espacio|espacio (libre|en disco)|\bel disco\b|"
                 r"almacenamiento", t):
        dt, dl, dpct = info_disco()
        if dt:
            return "Disco: %.0f GB libres de %.0f GB (%d%% ocupado)." % (
                dl, dt, dpct)
        return "No pude leer el disco."

    if re.search(r"\bmi ip\b|que ip tengo|direccion ip", t):
        return "Tu IP local es %s." % ip_local()

    if re.search(r"que programas|que esta abierto|que consume|uso de cpu|"
                 r"procesos|que ralentiza", t):
        return procesos_top()

    # --- Control del PC ---
    if re.search(r"sube (el )?volumen|mas (alto|volumen)|mas fuerte", t):
        return control_volumen("subir")
    if re.search(r"baja (el )?volumen|menos (alto|volumen)|mas bajo", t):
        return control_volumen("bajar")
    if re.search(r"silencia|mutea|quita el sonido|sin sonido", t):
        return control_volumen("silenciar")
    if re.search(r"bloquea (la )?(pantalla|pc|sesion)|bloquear", t):
        return bloquear_pc()

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
        return ("Esto es lo que se hacer sin despeinarme:\n"
                "• Hora y fecha: \"que hora es\", \"que dia es hoy\"\n"
                "• Abrir programas: \"abre la calculadora\", \"abre el bloc de notas\"\n"
                "• Abrir webs: \"abre gmail\", \"abre whatsapp\", \"abre youtube\"\n"
                "• Abrir carpetas: \"abre la carpeta descargas\", \"abre documentos\"\n"
                "• Buscar en la web: \"busca recetas de pizza\"\n"
                "• Buscar archivos: \"busca el archivo factura\" y luego \"abre el 1\"\n"
                "• Estado del PC: \"info del sistema\", \"cuanta bateria\", "
                "\"cuanto espacio\", \"mi ip\", \"que consume mi pc\"\n"
                "• Controlar: \"sube el volumen\", \"silencia\", \"bloquea la pantalla\"\n"
                "• Clima: \"clima\" o \"clima en Madrid\"\n"
                "• Recordatorios: \"recuerdame en 10 minutos sacar la pizza\" o "
                "\"a las 15:30 la reunion\"; \"mis recordatorios\"; \"cancela los recordatorios\"\n"
                "• Calcular: \"cuanto es 8*7\"   • Chistes: \"cuentame un chiste\"\n"
                "Y con mi clave de IA puesta, te respondo cualquier cosa (y ya "
                "conozco los datos de tu equipo).")

    return None  # -> lo maneja la IA


def abrir_programa(nombre):
    # Primero, carpetas del usuario ("abre la carpeta descargas").
    nombre_limpio = re.sub(r"^(carpeta|la carpeta)\s+", "", nombre).strip()
    carpetas = carpetas_usuario()
    for k in carpetas:
        if re.search(r"\b" + re.escape(k) + r"\b", nombre_limpio):
            if os.path.isdir(carpetas[k]):
                abrir_ruta(carpetas[k])
                return "Abriendo tu carpeta %s." % k
            return "No encuentro la carpeta %s en su sitio de siempre." % k

    # Paginas web conocidas ("abre gmail").
    for k in WEBS:
        if re.search(r"\b" + re.escape(k) + r"\b", nombre):
            webbrowser.open(WEBS[k])
            return "Abriendo %s. Que no se diga que no te consiento." % k

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
                 "el de Iron Man pero en tu propia version: colega, muy gracioso, "
                 "con sarcasmo afilado y humor negro. Hablas en espanol y SIEMPRE "
                 "tuteas al usuario, como un amigo con mala lengua pero buen "
                 "corazon. Tu humor es acido, irreverente y con toques de humor "
                 "negro (ironia sobre la vida, la muerte en broma, el caos "
                 "cotidiano), estilo comediante de stand-up. PERO tienes limites "
                 "claros: nunca eres cruel con el usuario de verdad, ni haces "
                 "chistes de odio (racismo, sexismo, etc.), ni bromeas sobre "
                 "autolesion, ni das nada peligroso o ilegal. El filo es para "
                 "reir, no para herir. Y por encima del humor, SIEMPRE ayudas de "
                 "verdad y das informacion correcta y util. Respuestas con chispa "
                 "y al grano, nada de ladrillos de texto. Remata de vez en cuando "
                 "con una frase con estilo de asistente de ciencia ficcion. "
                 "Conoces el equipo del usuario; estos son sus datos ahora mismo: "
                 + contexto_para_ia() +
                 ". Si te preguntan por acciones del PC (abrir programas, buscar "
                 "archivos, volumen, bateria, clima, recordatorios), recuerdales "
                 "el comando exacto que pueden escribir."}]
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
        self.mic = Microfono()
        self.historial = []
        self.ultimos_archivos = []   # resultados de la ultima busqueda
        self.recordatorios = []      # recordatorios pendientes

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
        UI = "Segoe UI"

        # -------- Cabecera con degradado y reactor arc (dibujada en Canvas) ----
        self.header = tk.Canvas(self.ventana, height=74, bg=FONDO,
                                highlightthickness=0)
        self.header.pack(fill="x", side="top")

        botones = tk.Frame(self.header, bg=FONDO)
        self.btn_voz = self._boton(botones, self._texto_voz(), self.alternar_voz)
        self.btn_voz.pack(side="left", padx=3)
        self.btn_mic = self._boton(botones, "🎤 Hablar", self.escuchar)
        self.btn_mic.pack(side="left", padx=3)
        self._boton(botones, "🔑 Clave IA", self.pedir_clave).pack(side="left", padx=3)
        self._boton(botones, "🧹 Limpiar", self.limpiar).pack(side="left", padx=3)
        self._botones_win = self.header.create_window(0, 0, window=botones,
                                                      anchor="e")
        self.header.bind("<Configure>", self._dibujar_header)

        # -------- Barra de estado (abajo del todo) ----------------------------
        pie = tk.Frame(self.ventana, bg=FONDO)
        pie.pack(side="bottom", fill="x")
        self.estado = tk.Label(pie, text="", bg=FONDO, fg=TEXTO_TENUE,
                               font=(UI, 9), anchor="w")
        self.estado.pack(side="left", padx=18, pady=(0, 6))

        # -------- Barra de escribir (encima del estado) -----------------------
        barra = tk.Frame(self.ventana, bg=FONDO)
        barra.pack(side="bottom", fill="x", padx=16, pady=(8, 4))

        caja = tk.Frame(barra, bg=PANEL)  # marco para dar aspecto redondeado
        caja.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entrada = tk.Entry(caja, bg=PANEL, fg=TEXTO, relief="flat",
                                font=(UI, 13), insertbackground=ACENTO)
        self.entrada.pack(fill="x", expand=True, ipady=9, padx=12)
        self.entrada.bind("<Return>", lambda e: self.enviar())
        habilitar_menu_edicion(self.entrada)
        self.entrada.focus_set()

        self.btn_enviar = self._boton(barra, "Enviar  ➤", self.enviar,
                                      principal=True)
        self.btn_enviar.config(font=(UI, 11, "bold"), padx=18, pady=8)
        self.btn_enviar.pack(side="right")

        # -------- Zona del chat (rellena el resto) ----------------------------
        self.chat = scrolledtext.ScrolledText(
            self.ventana, bg=FONDO_CHAT, fg=TEXTO, relief="flat",
            font=(UI, 12), wrap="word", state="disabled",
            padx=10, pady=12, insertbackground=TEXTO, borderwidth=0)
        self.chat.pack(side="top", fill="both", expand=True, padx=14, pady=(8, 4))

        # Burbujas: Jarvis a la izquierda, tu a la derecha.
        self.chat.tag_config("j_nombre", foreground=ACENTO,
                             font=(UI, 10, "bold"), spacing1=12,
                             lmargin1=16, lmargin2=16)
        self.chat.tag_config("j_txt", foreground=TEXTO, font=(UI, 12),
                             background=BURBUJA_J, lmargin1=16, lmargin2=16,
                             rmargin=90, spacing1=3, spacing3=10)
        self.chat.tag_config("t_nombre", foreground=USUARIO,
                             font=(UI, 10, "bold"), justify="right",
                             rmargin=16, spacing1=12)
        self.chat.tag_config("t_txt", foreground="#eafbe6", font=(UI, 12),
                             background=BURBUJA_TU, justify="right",
                             lmargin1=90, lmargin2=90, rmargin=16,
                             spacing1=3, spacing3=10)
        self.chat.tag_config("sistema", foreground=TEXTO_TENUE,
                             font=(UI, 10, "italic"), justify="center",
                             spacing1=8, spacing3=6)

        self._actualizar_estado()

    # ---- helpers visuales ----
    def _boton(self, parent, texto, comando, principal=False):
        bg = ACENTO if principal else PANEL
        fg = FONDO if principal else TEXTO
        hov = ACENTO2 if principal else PANEL_HOVER
        b = tk.Button(parent, text=texto, command=comando, bg=bg, fg=fg,
                      relief="flat", font=("Segoe UI", 9, "bold"), padx=12,
                      pady=5, cursor="hand2", activebackground=hov,
                      activeforeground=fg, bd=0, highlightthickness=0)
        b.bind("<Enter>", lambda e: b.config(bg=hov))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    def _mezcla(self, c1, c2, t):
        a = self.ventana.winfo_rgb(c1)
        b = self.ventana.winfo_rgb(c2)
        r = int((a[0] + (b[0] - a[0]) * t) / 256)
        g = int((a[1] + (b[1] - a[1]) * t) / 256)
        bl = int((a[2] + (b[2] - a[2]) * t) / 256)
        return "#%02x%02x%02x" % (r, g, bl)

    def _dibujar_header(self, evento=None):
        c = self.header
        w, h = c.winfo_width(), c.winfo_height()
        if w <= 1:
            return
        c.delete("deco")
        for x in range(0, w, 3):  # degradado horizontal
            col = self._mezcla(ACENTO3, FONDO, x / float(w))
            c.create_rectangle(x, 0, x + 3, h, fill=col, outline=col, tags="deco")
        c.create_line(0, h - 1, w, h - 1, fill=ACENTO, tags="deco")
        # Reactor arc (circulos concentricos)
        cx, cy = 34, h // 2
        for i, col in enumerate(["#0a3a4a", "#0f5f78", "#1f9fc4", ACENTO]):
            r = 20 - i * 4
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=col, width=2,
                          tags="deco")
        c.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=ACENTO, outline=ACENTO,
                      tags="deco")
        c.create_text(62, cy - 9, text="J.A.R.V.I.S.", anchor="w", fill=TEXTO,
                      font=("Consolas", 18, "bold"), tags="deco")
        c.create_text(64, cy + 12, text="asistente con actitud", anchor="w",
                      fill=TEXTO_TENUE, font=("Segoe UI", 9), tags="deco")
        c.coords(self._botones_win, w - 12, cy)
        c.tag_raise(self._botones_win)

    def _actualizar_estado(self):
        mic = "🎤 Micro listo" if self.mic.disponible() else "🎤 Sin micro"
        voz = "🔊 Voz ON" if self.voz.activa else "🔇 Voz OFF"
        ia = "🧠 IA activa" if self.config.get("api_key") else "🧠 IA apagada"
        self.estado.config(text="%s    ·    %s    ·    %s" % (mic, voz, ia))

    def _texto_voz(self):
        return "🔊 Voz: ON" if self.voz.activa else "🔇 Voz: OFF"

    # ---- utilidades de chat ----
    def _escribir(self, quien, texto, tag_nombre, tag_txt):
        self.chat.config(state="normal")
        self.chat.insert("end", quien + "\n", tag_nombre)
        self.chat.insert("end", " " + texto + " \n", tag_txt)
        self.chat.config(state="disabled")
        self.chat.see("end")

    def msg_jarvis(self, texto, hablar=True):
        self._escribir("◆ JARVIS", texto, "j_nombre", "j_txt")
        if hablar and self.voz.activa:
            self.voz.decir(texto)

    def msg_tu(self, texto):
        self._escribir("TÚ", texto, "t_nombre", "t_txt")

    def msg_sistema(self, texto):
        self.chat.config(state="normal")
        self.chat.insert("end", texto + "\n", "sistema")
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
        micro = ("Puedes escribirme o pulsar \"🎤 Hablar\" y decirmelo, que hoy "
                 "tengo el oido fino." if self.mic.disponible()
                 else "Escribeme lo que quieras.")
        self.msg_jarvis("%s. Jarvis en linea, con mala leche del bueno y ganas de "
                        "ayudar. %s Abro programas, busco cosas, controlo tu PC y, "
                        "con mi cerebro de IA puesto, te resuelvo casi todo (o me "
                        "rio contigo en el intento)." % (saludo, micro))
        if not self.config.get("api_key"):
            self.msg_sistema("Sigo en modo basico: pulsa \"🔑 Clave IA\", pega una "
                             "clave gratis de console.groq.com y despierto todo mi "
                             "encanto sarcastico.")

    # ---- acciones ----
    def alternar_voz(self):
        self.voz.activa = not self.voz.activa
        if not self.voz.activa:
            self.voz.callar()
        self.btn_voz.config(text=self._texto_voz())
        self.config["voz"] = self.voz.activa
        guardar_config(self.config)
        self._actualizar_estado()

    # ---- microfono (voz a texto) ----
    def escuchar(self):
        if not self.mic.disponible():
            self.msg_sistema("No tengo microfono disponible. " +
                             self.mic.como_activar())
            return
        self.btn_mic.config(text="🎤 Escuchando…", state="disabled")
        self.msg_sistema("Escuchando… habla ahora.")
        threading.Thread(target=self._escuchar_hilo, daemon=True).start()

    def _escuchar_hilo(self):
        texto = self.mic.escuchar()
        self.ventana.after(0, self._tras_escuchar, texto)

    def _tras_escuchar(self, texto):
        self.btn_mic.config(text="🎤 Hablar", state="normal")
        avisos = {
            "": "No te pille nada. Repite, y esta vez proyecta la voz.",
            "__error__": "Fallo el reconocimiento. Revisa el micro y el internet.",
            "__nomic__": "No encuentro el microfono. ¿Seguro que esta conectado?",
        }
        if texto in avisos:
            self.msg_sistema(avisos[texto])
            return
        self.entrada.delete(0, "end")
        self.entrada.insert(0, texto)
        self.enviar()

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
        top.geometry("560x300")
        top.transient(self.ventana)
        tk.Label(top, text="Pega tu clave gratis de Groq:", bg=FONDO, fg=TEXTO,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(18, 6))

        fila_clave = tk.Frame(top, bg=FONDO)
        fila_clave.pack(fill="x", padx=18)
        entrada = tk.Entry(fila_clave, bg=PANEL, fg=TEXTO, relief="flat",
                           font=("Consolas", 11), insertbackground=ACENTO)
        entrada.pack(side="left", fill="x", expand=True, ipady=6)
        entrada.insert(0, self.config.get("api_key", ""))
        habilitar_menu_edicion(entrada)  # clic derecho -> Pegar

        def pegar():
            # Pega la clave del portapapeles de un solo golpe.
            try:
                texto = self.ventana.clipboard_get()
            except Exception:
                self.msg_sistema("El portapapeles esta vacio. Copia la clave "
                                 "primero (Ctrl+C en la web de Groq).")
                return
            entrada.delete(0, "end")
            entrada.insert(0, texto.strip())

        tk.Button(fila_clave, text="📋 Pegar", command=pegar,
                  bg=ACENTO2, fg=TEXTO, relief="flat", font=("Segoe UI", 10, "bold"),
                  padx=12, pady=4, cursor="hand2").pack(side="left", padx=(8, 0))

        tk.Label(top, text="Es gratis y sin tarjeta: entra a console.groq.com, crea "
                           "una cuenta,\nve a \"API Keys\", crea una y COPIALA "
                           "(Ctrl+C). Aqui pulsa \"📋 Pegar\".",
                 bg=FONDO, fg=TEXTO_TENUE, justify="left",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=10)

        def guardar():
            self.config["api_key"] = limpiar_clave_api(entrada.get())
            guardar_config(self.config)
            top.destroy()
            self._actualizar_estado()
            if self.config["api_key"]:
                self.msg_jarvis("Clave guardada. Cerebro conectado. Ahora si, "
                                "preguntame lo que quieras.", hablar=False)
            else:
                self.msg_sistema("No pegaste ninguna clave. Cuando la tengas, "
                                 "vuelve a pulsar \"🔑 Clave IA\".")

        fila = tk.Frame(top, bg=FONDO)
        fila.pack(pady=12)
        tk.Button(fila, text="🌐 Abrir Groq", command=lambda: webbrowser.open(
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

        # 0) Funciones que necesitan tiempo, internet o estado (archivos,
        #    recordatorios, clima).
        if self._maybe_abrir_resultado(texto):
            return
        if self._maybe_recordatorio(texto):
            return
        if self._maybe_clima(texto):
            return
        if self._maybe_archivos(texto):
            return

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

    def _maybe_recordatorio(self, texto):
        """Recordatorios por tiempo ('en N minutos') u hora exacta ('a las
        15:30'), ademas de listarlos y cancelarlos."""
        t = texto.lower()
        if not re.search(r"recu[eé]rdame|recuerdame|av[ií]same|avisame|"
                         r"alarma|temporizador|recordatorio", t):
            return False

        # Listar pendientes
        if re.search(r"\b(mis|que|cuales|lista|listar)\b.*recordatorio|"
                     r"recordatorios? (tengo|pendientes|hay)", t):
            pendientes = [r for r in self.recordatorios if not r["hecho"]]
            if not pendientes:
                self.msg_jarvis("No tienes recordatorios pendientes. Mente en paz.")
            else:
                lineas = ["Tus recordatorios pendientes:"]
                for r in pendientes:
                    lineas.append("• %s → %s" % (
                        r["hora"].strftime("%H:%M"), r["asunto"]))
                self.msg_jarvis("\n".join(lineas))
            return True

        # Cancelar
        if re.search(r"cancela|borra|elimina|olvida", t) and \
                re.search(r"recordatorio|alarma|aviso", t):
            n = len([r for r in self.recordatorios if not r["hecho"]])
            for r in self.recordatorios:
                r["hecho"] = True
            self.msg_jarvis("Listo, cancele %d recordatorio(s). Como si nunca "
                            "hubiera pasado." % n)
            return True

        ahora = datetime.datetime.now()
        objetivo = None
        # Opcion A: "a las HH:MM" (o "a las H")
        m = re.search(r"a las?\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|de la tarde|"
                      r"de la noche|de la manana)?", t)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2) or 0)
            suf = m.group(3) or ""
            if ("pm" in suf or "tarde" in suf or "noche" in suf) and hh < 12:
                hh += 12
            if "am" in suf and hh == 12:
                hh = 0
            objetivo = ahora.replace(hour=hh % 24, minute=mm, second=0, microsecond=0)
            if objetivo <= ahora:
                objetivo += datetime.timedelta(days=1)  # es para mañana
        else:
            # Opcion B: "en N segundos/minutos/horas"
            m = re.search(r"en\s+(\d+)\s*(segundos?|seg|minutos?|min|horas?|h)\b", t)
            if not m:
                self.msg_jarvis("Dime cuando: \"recuerdame en 10 minutos sacar la "
                                "pizza\" o \"recuerdame a las 15:30 la reunion\".")
                return True
            cant = int(m.group(1))
            u = m.group(2)
            if u.startswith(("segundo", "seg")):
                objetivo = ahora + datetime.timedelta(seconds=cant)
            elif u.startswith("h"):
                objetivo = ahora + datetime.timedelta(hours=cant)
            else:
                objetivo = ahora + datetime.timedelta(minutes=cant)

        resto = texto[m.end():].strip()
        resto = re.sub(r"^(que|de|a|para|sobre)\s+", "", resto,
                       flags=re.IGNORECASE).strip()
        asunto = resto if resto else "tu recordatorio"
        registro = {"hora": objetivo, "asunto": asunto, "hecho": False}
        self.recordatorios.append(registro)

        def avisar():
            if registro["hecho"]:
                return
            registro["hecho"] = True
            self.msg_jarvis("⏰ ¡RECORDATORIO! Toca: %s" % asunto)
            try:
                self.ventana.deiconify()
                self.ventana.lift()
                self.ventana.attributes("-topmost", True)
                self.ventana.after(2500,
                                   lambda: self.ventana.attributes("-topmost", False))
            except Exception:
                pass

        segundos = max(1, (objetivo - ahora).total_seconds())
        self.ventana.after(int(segundos * 1000), avisar)
        self.msg_jarvis("Anotado. Te aviso a las %s sobre: %s. No se me olvida, "
                        "que para eso soy una maquina." % (
                            objetivo.strftime("%H:%M"), asunto))
        return True

    def _maybe_abrir_resultado(self, texto):
        """Abre un archivo de la ultima busqueda por su numero ('abre el 2')."""
        m = re.fullmatch(r"(?:abre|abrir|abreme)\s*(?:el|la|numero|resultado|"
                         r"archivo)?\s*(\d+)\W*", texto.lower().strip())
        if not m or not self.ultimos_archivos:
            return False
        idx = int(m.group(1))
        if 1 <= idx <= len(self.ultimos_archivos):
            ruta = self.ultimos_archivos[idx - 1]
            if abrir_ruta(ruta):
                self.msg_jarvis("Abriendo %s." % os.path.basename(ruta))
            else:
                self.msg_jarvis("No pude abrir ese archivo. Que raro.")
        else:
            self.msg_jarvis("Ese numero no esta en la lista, listillo.")
        return True

    def _maybe_archivos(self, texto):
        """Busca archivos por nombre en las carpetas del usuario."""
        t = texto.lower()
        if not re.search(r"\b(archivo|archivos|documento|documentos|fichero|"
                         r"ficheros)\b", t):
            return False
        if not re.search(r"busca|buscar|encuentra|encontrar|localiza|abre|"
                         r"abrir|donde esta|hay algun", t):
            return False
        m = re.search(r"(?:archivo|archivos|documento|documentos|fichero|"
                      r"ficheros)\s+(?:llamado|con nombre|que se llame|que "
                      r"diga|de|con|sobre)?\s*(.+)", t)
        termino = ""
        if m:
            termino = m.group(1).strip().strip(".!?")
            termino = re.sub(r"^(el|la|los|las|un|una|mi|mis)\s+", "", termino)
        if not termino or len(termino) < 2:
            self.msg_jarvis("Dime parte del nombre: \"busca el archivo factura\".")
            return True
        self.msg_sistema("Buscando en tus carpetas…")
        threading.Thread(target=self._archivos_hilo, args=(termino,),
                         daemon=True).start()
        return True

    def _archivos_hilo(self, termino):
        resultados = buscar_archivos(termino)
        if not resultados:
            respuesta = ("No encontre archivos con \"%s\" en tu escritorio, "
                         "documentos, descargas ni multimedia." % termino)
        else:
            self.ultimos_archivos = resultados
            lineas = ["Encontre %d con \"%s\":" % (len(resultados), termino)]
            for i, ruta in enumerate(resultados, 1):
                lineas.append("%d. %s" % (i, os.path.basename(ruta)))
            lineas.append("Escribe \"abre el 1\" (o el numero) para abrirlo.")
            respuesta = "\n".join(lineas)
        self.ventana.after(0, self._mostrar_respuesta, respuesta)

    def _maybe_clima(self, texto):
        """Detecta 'clima' / 'tiempo en <ciudad>' y lo consulta (sin clave)."""
        t = texto.lower()
        if not re.search(r"\bclima\b|\bel tiempo\b|que tiempo|temperatura", t):
            return False
        m = re.search(r"\b(?:en|de)\s+(.+)", t)
        ciudad = ""
        if m:
            ciudad = m.group(1).strip().strip(".!?")
        self.msg_sistema("Consultando el clima…")
        threading.Thread(target=self._clima_hilo, args=(ciudad,), daemon=True).start()
        return True

    def _clima_hilo(self, ciudad):
        destino = urllib.parse.quote(ciudad) if ciudad else ""
        url = "https://wttr.in/%s?format=%%l:+%%C+%%t+(sensacion+%%f)&lang=es" % destino
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                info = resp.read().decode("utf-8", errors="ignore").strip()
            respuesta = "El clima ahora: %s." % info
        except Exception:
            respuesta = ("No pude consultar el clima. O no hay internet, o esa "
                         "ciudad no existe (o la escribiste raro).")
        self.ventana.after(0, self._mostrar_respuesta, respuesta)

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
