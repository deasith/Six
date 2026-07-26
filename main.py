"""
Mi Cuaderno - app para tablet/celular Android hecha con Python y Kivy.
Estilo coquette (rosa pastel). Secciones: Notas, Tareas (lista/tablero),
Avisos (recordatorios inteligentes) y Dibujo.

Funciones:
- NOTAS: crear, editar, buscar, favoritos, color de etiqueta, fecha/hora
- TAREAS: lista con casillas + vista TABLERO estilo Kanban
  (Pendiente / En proceso / Terminado) moviendo tarjetas entre columnas
- AVISOS: escribe en lenguaje normal ("Llamar a Juan el lunes a las 5 pm")
  y la app detecta la fecha/hora y te notifica cuando llega
- DIBUJO: lienzo con colores, grosores, borrador, limpiar y guardar
- Color de fondo personalizable (se guarda)

Este es el archivo principal que Buildozer usa para crear el .apk.
Se llama 'main.py' obligatoriamente.

Como probarla en tu computador Linux:
    python3 main.py
"""

import calendar
import datetime
import json
import os
import re
import threading
import urllib.request
import urllib.error

from kivy.config import Config
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ---- Temas de colores (elegibles desde la app) ----
# Cada tema define los colores principales y un fondo que combina.
TEMAS = [
    {"nombre": "Coquette",
     "CABECERA": (0.93, 0.60, 0.70, 1), "ACCENT": (0.90, 0.52, 0.63, 1),
     "CARD": (1.00, 0.97, 0.98, 1), "CARD_BORDE": (0.94, 0.88, 0.91, 1),
     "BORRAR": (0.90, 0.45, 0.52, 1), "VERDE": (0.45, 0.78, 0.55, 1),
     "TEXTO": (0.38, 0.22, 0.28, 1), "TEXTO_TENUE": (0.62, 0.48, 0.54, 1),
     "FONDO": (0.99, 0.94, 0.95, 1)},
    {"nombre": "Lavanda",
     "CABECERA": (0.60, 0.53, 0.85, 1), "ACCENT": (0.55, 0.47, 0.82, 1),
     "CARD": (0.99, 0.98, 1.00, 1), "CARD_BORDE": (0.90, 0.88, 0.96, 1),
     "BORRAR": (0.85, 0.45, 0.60, 1), "VERDE": (0.45, 0.78, 0.60, 1),
     "TEXTO": (0.28, 0.24, 0.40, 1), "TEXTO_TENUE": (0.52, 0.48, 0.66, 1),
     "FONDO": (0.95, 0.94, 0.99, 1)},
    {"nombre": "Menta",
     "CABECERA": (0.35, 0.72, 0.62, 1), "ACCENT": (0.28, 0.66, 0.56, 1),
     "CARD": (0.98, 1.00, 0.99, 1), "CARD_BORDE": (0.87, 0.95, 0.91, 1),
     "BORRAR": (0.88, 0.45, 0.50, 1), "VERDE": (0.40, 0.75, 0.50, 1),
     "TEXTO": (0.20, 0.36, 0.32, 1), "TEXTO_TENUE": (0.44, 0.60, 0.55, 1),
     "FONDO": (0.93, 0.98, 0.96, 1)},
    {"nombre": "Oceano",
     "CABECERA": (0.35, 0.60, 0.88, 1), "ACCENT": (0.28, 0.53, 0.85, 1),
     "CARD": (0.98, 0.99, 1.00, 1), "CARD_BORDE": (0.87, 0.92, 0.98, 1),
     "BORRAR": (0.88, 0.45, 0.52, 1), "VERDE": (0.40, 0.75, 0.55, 1),
     "TEXTO": (0.20, 0.30, 0.45, 1), "TEXTO_TENUE": (0.45, 0.55, 0.70, 1),
     "FONDO": (0.93, 0.96, 0.99, 1)},
    {"nombre": "Durazno",
     "CABECERA": (0.96, 0.60, 0.45, 1), "ACCENT": (0.94, 0.54, 0.40, 1),
     "CARD": (1.00, 0.98, 0.96, 1), "CARD_BORDE": (0.97, 0.90, 0.85, 1),
     "BORRAR": (0.88, 0.42, 0.42, 1), "VERDE": (0.45, 0.75, 0.50, 1),
     "TEXTO": (0.42, 0.26, 0.20, 1), "TEXTO_TENUE": (0.66, 0.50, 0.44, 1),
     "FONDO": (1.00, 0.95, 0.90, 1)},
    {"nombre": "Noche",
     "CABECERA": (0.42, 0.35, 0.60, 1), "ACCENT": (0.58, 0.48, 0.85, 1),
     "CARD": (0.20, 0.19, 0.28, 1), "CARD_BORDE": (0.30, 0.28, 0.40, 1),
     "BORRAR": (0.82, 0.42, 0.50, 1), "VERDE": (0.40, 0.72, 0.52, 1),
     "TEXTO": (0.92, 0.90, 0.97, 1), "TEXTO_TENUE": (0.66, 0.62, 0.78, 1),
     "FONDO": (0.12, 0.11, 0.18, 1)},
]

# Fondos sueltos que se pueden elegir aparte del tema
FONDOS = [
    (0.99, 0.94, 0.95, 1), (0.96, 0.93, 0.98, 1), (0.93, 0.97, 0.95, 1),
    (0.99, 0.97, 0.91, 1), (0.99, 0.94, 0.91, 1), (0.92, 0.96, 0.99, 1),
    (0.15, 0.14, 0.20, 1),
]

# Colores fijos (no cambian con el tema)
AMARILLO = (0.98, 0.75, 0.35, 1)
ORO      = (0.95, 0.72, 0.35, 1)
BLANCO   = (1, 1, 1, 1)

# Colores del tema actual (se rellenan con aplicar_tema)
CABECERA = ACCENT = CARD = CARD_BORDE = BORRAR = VERDE = TEXTO = TEXTO_TENUE = (0, 0, 0, 1)


def aplicar_tema(idx):
    """Cambia los colores globales al tema elegido."""
    global CABECERA, ACCENT, CARD, CARD_BORDE, BORRAR, VERDE, TEXTO, TEXTO_TENUE
    t = TEMAS[idx % len(TEMAS)]
    CABECERA = t["CABECERA"]
    ACCENT = t["ACCENT"]
    CARD = t["CARD"]
    CARD_BORDE = t["CARD_BORDE"]
    BORRAR = t["BORRAR"]
    VERDE = t["VERDE"]
    TEXTO = t["TEXTO"]
    TEXTO_TENUE = t["TEXTO_TENUE"]


aplicar_tema(0)   # tema por defecto (Coquette)

COLORES = [
    None, (0.95, 0.45, 0.60, 1), (0.55, 0.70, 0.95, 1),
    (0.50, 0.80, 0.60, 1), (0.98, 0.80, 0.40, 1), (0.98, 0.60, 0.45, 1),
]

# Paleta de colores para dibujar (estilo coquette/aesthetic).
# Se muestra en una barra que se desliza para elegir cualquiera.
DIBUJO_COLORES = [
    (0.20, 0.20, 0.25, 1),   # negro suave
    (0.55, 0.55, 0.62, 1),   # gris
    (0.95, 0.50, 0.65, 1),   # rosa coquette
    (0.98, 0.68, 0.78, 1),   # rosa pastel
    (0.99, 0.80, 0.86, 1),   # rosa bebe
    (0.90, 0.30, 0.40, 1),   # rojo fresa
    (0.98, 0.55, 0.45, 1),   # coral
    (0.98, 0.75, 0.30, 1),   # amarillo miel
    (0.99, 0.87, 0.55, 1),   # mantequilla
    (0.55, 0.80, 0.55, 1),   # verde pastel
    (0.30, 0.75, 0.45, 1),   # verde
    (0.60, 0.85, 0.82, 1),   # menta
    (0.55, 0.78, 0.95, 1),   # celeste
    (0.30, 0.55, 0.95, 1),   # azul
    (0.72, 0.65, 0.92, 1),   # lavanda
    (0.80, 0.55, 0.88, 1),   # lila
    (0.85, 0.62, 0.52, 1),   # cafe con leche
    (0.60, 0.42, 0.35, 1),   # chocolate
]

# ---- Fuentes de escritura (estilo aesthetic/coquette) ----
# Los archivos .ttf estan en la carpeta 'fuentes'. Se incluyen en el .apk.
DIR_FUENTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes")

# (nombre que se ve en la app, nombre interno de la fuente, archivo .ttf)
# La primera (None) es la letra normal de siempre.
FUENTES = [
    ("Normal", None, None),
    ("Redondita", "Quicksand", "Quicksand.ttf"),
    ("Comfy", "Comfortaa", "Comfortaa.ttf"),
    ("Cursiva", "DancingScript", "DancingScript.ttf"),
    ("Playa", "Pacifico", "Pacifico.ttf"),
    ("Cuaderno", "GochiHand", "GochiHand.ttf"),
    ("Marcador", "PatrickHand", "PatrickHand.ttf"),
]

_ROBOTO_ORIGINAL = None   # ruta de la letra normal de Kivy (para volver atras)


def registrar_fuentes():
    """Deja listas todas las fuentes bonitas para poder usarlas."""
    global _ROBOTO_ORIGINAL
    try:
        import kivy
        _ROBOTO_ORIGINAL = os.path.join(os.path.dirname(kivy.__file__),
                                        "data", "fonts", "Roboto-Regular.ttf")
    except Exception:
        _ROBOTO_ORIGINAL = None
    for _, nombre, archivo in FUENTES:
        if nombre is None:
            continue
        ruta = os.path.join(DIR_FUENTES, archivo)
        if os.path.exists(ruta):
            try:
                LabelBase.register(name=nombre, fn_regular=ruta)
            except Exception:
                pass


def aplicar_fuente(idx):
    """Cambia la letra de TODA la app volviendo a registrar 'Roboto'
    (la letra por defecto que usan todas las etiquetas)."""
    idx = idx % len(FUENTES)
    nombre, archivo = FUENTES[idx][1], FUENTES[idx][2]
    try:
        if nombre is None:
            if _ROBOTO_ORIGINAL and os.path.exists(_ROBOTO_ORIGINAL):
                LabelBase.register(name="Roboto", fn_regular=_ROBOTO_ORIGINAL)
        else:
            ruta = os.path.join(DIR_FUENTES, archivo)
            if os.path.exists(ruta):
                LabelBase.register(name="Roboto", fn_regular=ruta)
    except Exception:
        pass


MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]
DIAS_CORTO = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]

DIAS_SEMANA = {
    "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2, "jueves": 3,
    "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6,
}
MESES_NUM = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def fecha_ahora():
    ahora = datetime.datetime.now()
    return f"{ahora.day} {MESES[ahora.month - 1]} {ahora.year}, {ahora.hour:02d}:{ahora.minute:02d}"


def formatear_cuando(dt):
    return f"{DIAS_CORTO[dt.weekday()]} {dt.day} {MESES[dt.month - 1]}, {dt.hour:02d}:{dt.minute:02d}"


def escapar_markup(t):
    """Evita que corchetes del texto rompan el formato con markup."""
    return t.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def limpiar_clave_api(txt):
    """Limpia la clave API por si al copiarla se pegaron espacios, saltos
    de linea, comillas o un 'Bearer ' de mas. Una clave de Groq no tiene
    espacios, asi que quitarlos es seguro."""
    txt = txt.strip().strip('"').strip("'").strip()
    if txt.lower().startswith("bearer "):
        txt = txt[7:]
    return "".join(txt.split())   # quita cualquier espacio o salto interno


def parsear_fecha_hora(texto):
    """Detecta una fecha y hora dentro de un texto en espanol.
    Devuelve un datetime, o None si no encuentra nada."""
    t = " " + texto.lower() + " "
    ahora = datetime.datetime.now()
    fecha = None

    # Fechas relativas
    if "pasado manana" in t or "pasado mañana" in t:
        fecha = ahora.date() + datetime.timedelta(days=2)
    elif "manana" in t or "mañana" in t:
        fecha = ahora.date() + datetime.timedelta(days=1)
    elif "hoy" in t:
        fecha = ahora.date()

    # Dia de la semana ("el lunes")
    if fecha is None:
        for nombre, wd in DIAS_SEMANA.items():
            if nombre in t:
                delta = (wd - ahora.weekday()) % 7
                if delta == 0:
                    delta = 7   # el proximo, no hoy
                fecha = ahora.date() + datetime.timedelta(days=delta)
                break

    # Fecha con numero ("el 25 de julio", "el 25")
    m = re.search(r"\bel\s+(\d{1,2})(?:\s+de\s+([a-záéíóú]+))?", t)
    if m:
        dia = int(m.group(1))
        mes = MESES_NUM.get(m.group(2), ahora.month) if m.group(2) else ahora.month
        try:
            cand = datetime.date(ahora.year, mes, dia)
            if cand < ahora.date():
                cand = datetime.date(ahora.year + 1, mes, dia)
            fecha = cand
        except ValueError:
            pass

    # Hora
    hora = None
    minuto = 0
    m = re.search(
        r"a\s+la[s]?\s+(\d{1,2})(?::(\d{2}))?\s*"
        r"(a\.?\s*m\.?|p\.?\s*m\.?|de\s+la\s+tarde|de\s+la\s+noche|de\s+la\s+manana|de\s+la\s+mañana)?",
        t,
    )
    if not m:
        m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(a\.?\s*m\.?|p\.?\s*m\.?)", t)
    if m:
        hora = int(m.group(1))
        if m.group(2):
            minuto = int(m.group(2))
        seg = m.group(0)
        if "p" in seg or "tarde" in seg or "noche" in seg:
            if hora < 12:
                hora += 12
        elif "a" in seg and ("m" in seg or "manana" in seg or "mañana" in seg):
            if hora == 12:
                hora = 0
        if hora > 23 or minuto > 59:
            hora = None

    if fecha is None and hora is None:
        return None
    if fecha is None:
        fecha = ahora.date()
    if hora is None:
        hora, minuto = 9, 0
    cuando = datetime.datetime.combine(fecha, datetime.time(hora, minuto))
    if cuando < ahora:
        cuando += datetime.timedelta(days=1)
    return cuando


class Tarjeta(BoxLayout):
    def __init__(self, color=CARD, radio=18, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*color)
            self._rect = RoundedRectangle(radius=[radio])
        self.bind(pos=self._actualizar, size=self._actualizar)

    def _actualizar(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class BarraColor(Widget):
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._color = Color(*(color if color else (0, 0, 0, 0)))
            self._rect = RoundedRectangle(radius=[3])
        self.bind(pos=self._actualizar, size=self._actualizar)

    def _actualizar(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class BotonRedondo(Button):
    def __init__(self, color=ACCENT, radio=16, texto_color=BLANCO, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = texto_color
        self._base = color
        with self.canvas.before:
            self._color = Color(*color)
            self._rect = RoundedRectangle(radius=[radio])
        self.bind(pos=self._actualizar, size=self._actualizar, state=self._al_pulsar)

    def poner_color(self, color, texto_color=None):
        self._base = color
        self._color.rgba = color
        if texto_color is not None:
            self.color = texto_color

    def _actualizar(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _al_pulsar(self, *args):
        factor = 0.85 if self.state == "down" else 1.0
        self._color.rgba = (self._base[0] * factor, self._base[1] * factor,
                            self._base[2] * factor, 1)


class Lienzo(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color_lapiz = (0.20, 0.20, 0.25, 1)
        self.grosor = 3
        self._img_rect = None
        self._img_tex = None       # textura del dibujo que se esta editando
        self.trazos = []           # cada trazo: {"color":..., "width":..., "pts":[...]}
        self._trazo_actual = None
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._fondo = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._actualizar, size=self._actualizar)

    def _actualizar(self, *args):
        self._fondo.pos = self.pos
        self._fondo.size = self.size
        if self._img_rect is not None:
            self._img_rect.pos = self.pos
            self._img_rect.size = self.size

    def cargar_imagen(self, ruta):
        """Carga un dibujo guardado para seguir editandolo."""
        from kivy.core.image import Image as CoreImage
        self.limpiar()
        try:
            tex = CoreImage(ruta).texture
        except Exception:
            return
        self._img_tex = tex
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._img_rect = Rectangle(texture=tex, pos=self.pos, size=self.size)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Guardamos el trazo como datos (en coordenadas locales) para poder
            # dibujarlo despues en la imagen guardada sin que salga en blanco.
            self._trazo_actual = {"color": tuple(self.color_lapiz),
                                  "width": self.grosor,
                                  "pts": [touch.x - self.x, touch.y - self.y]}
            self.trazos.append(self._trazo_actual)
            with self.canvas:
                Color(*self.color_lapiz)
                touch.ud["linea"] = Line(points=[touch.x, touch.y],
                                         width=self.grosor, cap="round", joint="round")
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if "linea" in touch.ud and self.collide_point(*touch.pos):
            touch.ud["linea"].points += [touch.x, touch.y]
            if self._trazo_actual is not None:
                self._trazo_actual["pts"] += [touch.x - self.x, touch.y - self.y]
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if "linea" in touch.ud:
            self._trazo_actual = None
        return super().on_touch_up(touch)

    def limpiar(self):
        self.canvas.clear()
        if self._img_rect is not None:
            try:
                self.canvas.before.remove(self._img_rect)
            except Exception:
                pass
            self._img_rect = None
        self._img_tex = None
        self.trazos = []
        self._trazo_actual = None

    def guardar_png(self, ruta):
        """Dibuja el fondo blanco, la imagen editada (si hay) y todos los
        trazos en una imagen fuera de pantalla (FBO) y la guarda. Asi el
        dibujo nunca sale en blanco, aunque el widget este desplazado."""
        from kivy.graphics import (Fbo, ClearColor, ClearBuffers,
                                    Color as GColor, Line as GLine,
                                    Rectangle as GRect)
        w = max(1, int(self.width))
        h = max(1, int(self.height))
        fbo = Fbo(size=(w, h))
        with fbo:
            ClearColor(1, 1, 1, 1)
            ClearBuffers()
            if self._img_tex is not None:
                GColor(1, 1, 1, 1)
                GRect(texture=self._img_tex, pos=(0, 0), size=(w, h))
            for t in self.trazos:
                if len(t["pts"]) >= 2:
                    GColor(*t["color"])
                    GLine(points=t["pts"], width=t["width"],
                          cap="round", joint="round")
        fbo.draw()
        fbo.texture.save(ruta, flipped=True)
        return True


class AppNotas(App):
    def build(self):
        self.title = "Mi Cuaderno"
        # El teclado empuja la vista en vez de tapar el campo de texto
        Window.softinput_mode = "below_target"
        # En el computador, ventana con forma de celular para probar comodo
        from kivy.utils import platform
        if platform != "android":
            Window.size = (400, 720)
        d = self.user_data_dir
        self.archivo = os.path.join(d, "notas.json")
        self.archivo_tareas = os.path.join(d, "tareas.json")
        self.archivo_recordatorios = os.path.join(d, "recordatorios.json")
        self.archivo_config = os.path.join(d, "config.json")
        self.archivo_chat = os.path.join(d, "chat.json")
        self.notas = self.cargar_json(self.archivo, self.normalizar_nota)
        self.tareas = self.cargar_json(self.archivo_tareas, self.normalizar_tarea)
        self.recordatorios = self.cargar_json(self.archivo_recordatorios, self.normalizar_recordatorio)
        self.chat = self.cargar_json(self.archivo_chat, self.normalizar_chat)
        self.config_app = self.cargar_config()
        self.dir_dibujos = os.path.join(d, "dibujos")
        os.makedirs(self.dir_dibujos, exist_ok=True)
        aplicar_tema(self.config_app.get("tema", 0))
        registrar_fuentes()
        aplicar_fuente(self.config_app.get("fuente", 0))
        self.filtro = ""
        self.lienzo = None
        self.seccion = "notas"
        self.vista_tareas = "lista"
        self.vista_dibujo = "lienzo"
        self.vista_avisos = "lista"
        self.ia_ocupada = False
        self.chat_scroll = None
        hoy = datetime.datetime.now()
        self.cal_mes = hoy.month
        self.cal_anio = hoy.year

        self.aplicar_fondo()
        self.raiz = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        self.montar_interfaz()

        # Revisa los recordatorios cada 20 segundos (con la app abierta)
        Clock.schedule_interval(self.revisar_recordatorios, 20)
        return self.raiz

    def montar_interfaz(self):
        self.raiz.clear_widgets()
        cabecera = Tarjeta(color=CABECERA, radio=22, size_hint_y=None, height=dp(58),
                           padding=(dp(14), 0), spacing=dp(8))
        self.titulo = Label(markup=True, font_size="21sp", color=BLANCO,
                            halign="left", valign="middle")
        self.titulo.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        cabecera.add_widget(self.titulo)
        boton_colores = BotonRedondo(text="Colores", color=CARD, texto_color=CABECERA,
                                     radio=14, font_size="13sp", bold=True,
                                     size_hint_x=None, width=dp(86))
        boton_colores.bind(on_release=lambda w: self.elegir_colores())
        cabecera.add_widget(boton_colores)
        self.raiz.add_widget(cabecera)

        barra_nav = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        self.nav = {}
        for clave, texto in [("notas", "Notas"), ("tareas", "Tareas"),
                             ("avisos", "Avisos"), ("dibujo", "Dibujo"),
                             ("ia", "IA")]:
            boton = BotonRedondo(text=texto, color=CARD_BORDE, texto_color=TEXTO,
                                 radio=14, font_size="12sp", bold=True)
            boton.bind(on_press=lambda w, c=clave: self.mostrar_seccion(c))
            self.nav[clave] = boton
            barra_nav.add_widget(boton)
        self.raiz.add_widget(barra_nav)

        self.contenido = BoxLayout(orientation="vertical", spacing=dp(10))
        self.raiz.add_widget(self.contenido)
        self.mostrar_seccion(self.seccion)

    def reconstruir(self):
        # Rehace toda la interfaz (tras cambiar de tema)
        self.aplicar_fondo()
        self.montar_interfaz()

    def on_start(self):
        # Arranca el servicio en segundo plano (solo funciona en Android)
        self.iniciar_servicio()

    def iniciar_servicio(self):
        try:
            from jnius import autoclass
            servicio = autoclass("org.misnotas.misnotas.ServiceRecordatorio")
            actividad = autoclass("org.kivy.android.PythonActivity").mActivity
            servicio.start(actividad, self.user_data_dir)
        except Exception as e:
            # En el computador no hay Android: se ignora sin problema
            print("Servicio en segundo plano no disponible aqui:", e)

    # ---------- Cambio de seccion ----------
    def mostrar_seccion(self, nombre):
        self.seccion = nombre
        for clave, boton in self.nav.items():
            if clave == nombre:
                boton.poner_color(ACCENT, BLANCO)
            else:
                boton.poner_color(CARD_BORDE, TEXTO)
        self.contenido.clear_widgets()
        if nombre == "notas":
            self.construir_notas()
        elif nombre == "tareas":
            self.construir_tareas()
        elif nombre == "avisos":
            self.construir_avisos()
        elif nombre == "dibujo":
            self.construir_dibujo()
        elif nombre == "ia":
            self.construir_ia()

    # ---------- Colores (tema + fondo) ----------
    def aplicar_fondo(self):
        idx = self.config_app.get("fondo", -1)
        if idx is None or idx < 0:
            Window.clearcolor = TEMAS[self.config_app.get("tema", 0) % len(TEMAS)]["FONDO"]
        else:
            Window.clearcolor = FONDOS[idx % len(FONDOS)]

    def elegir_colores(self):
        cont = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8),
                         size_hint_y=None)
        cont.bind(minimum_height=cont.setter("height"))
        popup = Popup(title="Colores y letra", size_hint=(0.92, 0.82),
                      title_color=TEXTO, separator_color=ACCENT)

        cont.add_widget(Label(text="Tema", color=TEXTO, size_hint_y=None,
                              height=dp(22), font_size="15sp", bold=True))
        grid_t = GridLayout(cols=3, size_hint_y=None, height=dp(100), spacing=dp(8))
        for i, t in enumerate(TEMAS):
            b = BotonRedondo(text=t["nombre"], color=t["ACCENT"], radio=12,
                             font_size="12sp", bold=True)
            b.bind(on_press=lambda w, idx=i: self._poner_tema(idx, popup))
            grid_t.add_widget(b)
        cont.add_widget(grid_t)

        cont.add_widget(Label(text="Fondo", color=TEXTO, size_hint_y=None,
                              height=dp(22), font_size="15sp", bold=True))
        fila_f = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        for i, col in enumerate(FONDOS):
            s = BotonRedondo(color=col, radio=14)
            s.bind(on_press=lambda w, idx=i: self._poner_fondo(idx, popup))
            fila_f.add_widget(s)
        cont.add_widget(fila_f)

        cont.add_widget(Label(text="Letra", color=TEXTO, size_hint_y=None,
                              height=dp(22), font_size="15sp", bold=True))
        grid_l = GridLayout(cols=2, size_hint_y=None, spacing=dp(8))
        grid_l.bind(minimum_height=grid_l.setter("height"))
        actual_f = self.config_app.get("fuente", 0)
        for i, (nombre_f, nombre_int, _arch) in enumerate(FUENTES):
            col_b = ACCENT if i == actual_f else CARD_BORDE
            col_t = BLANCO if i == actual_f else TEXTO
            b = BotonRedondo(text=nombre_f, color=col_b, texto_color=col_t,
                             radio=12, font_size="16sp",
                             size_hint_y=None, height=dp(44))
            # muestra el nombre en esa misma letra (solo si el archivo existe)
            if nombre_int is not None and _arch is not None and \
                    os.path.exists(os.path.join(DIR_FUENTES, _arch)):
                b.font_name = nombre_int
            b.bind(on_press=lambda w, idx=i: self._poner_fuente(idx, popup))
            grid_l.add_widget(b)
        cont.add_widget(grid_l)

        b_cerrar = BotonRedondo(text="Cerrar", color=ACCENT, radio=14,
                                size_hint_y=None, height=dp(44))
        b_cerrar.bind(on_press=lambda w: popup.dismiss())
        cont.add_widget(b_cerrar)

        scroll = ScrollView()
        scroll.add_widget(cont)
        popup.content = scroll
        popup.open()

    def _poner_tema(self, idx, popup):
        self.config_app["tema"] = idx
        self.config_app["fondo"] = -1   # usar el fondo que combina con el tema
        aplicar_tema(idx)
        self.guardar_config()
        popup.dismiss()
        self.reconstruir()

    def _poner_fondo(self, idx, popup):
        self.config_app["fondo"] = idx
        self.guardar_config()
        self.aplicar_fondo()
        popup.dismiss()

    def _poner_fuente(self, idx, popup):
        self.config_app["fuente"] = idx
        aplicar_fuente(idx)
        self.guardar_config()
        popup.dismiss()
        self.reconstruir()

    # ---------- Guardar/cargar ----------
    def normalizar_nota(self, nota):
        if isinstance(nota, str):
            nota = {"texto": nota, "fecha": ""}
        nota.setdefault("texto", "")
        nota.setdefault("fecha", "")
        nota.setdefault("fav", False)
        nota.setdefault("color", 0)
        return nota

    def normalizar_tarea(self, tarea):
        if isinstance(tarea, str):
            tarea = {"texto": tarea}
        tarea.setdefault("texto", "")
        if "estado" not in tarea:
            tarea["estado"] = 2 if tarea.get("hecha") else 0
        tarea.pop("hecha", None)
        return tarea

    def normalizar_recordatorio(self, r):
        if isinstance(r, str):
            r = {"texto": r}
        r.setdefault("texto", "")
        r.setdefault("cuando", "")
        r.setdefault("avisado", False)
        return r

    def normalizar_chat(self, m):
        if not isinstance(m, dict):
            m = {}
        m.setdefault("role", "user")
        m.setdefault("content", "")
        return m

    def cargar_json(self, ruta, normalizar):
        if not os.path.exists(ruta):
            return []
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
        return [normalizar(d) for d in datos]

    def _guardar(self, ruta, datos):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

    def guardar_notas(self):
        self._guardar(self.archivo, self.notas)

    def guardar_tareas(self):
        self._guardar(self.archivo_tareas, self.tareas)

    def guardar_recordatorios(self):
        self._guardar(self.archivo_recordatorios, self.recordatorios)

    def guardar_chat(self):
        self._guardar(self.archivo_chat, self.chat)

    def cargar_config(self):
        if os.path.exists(self.archivo_config):
            try:
                with open(self.archivo_config, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"tema": 0, "fondo": -1, "fuente": 0}

    def guardar_config(self):
        self._guardar(self.archivo_config, self.config_app)

    def _mensaje(self, contenedor, texto):
        contenedor.add_widget(Label(text=texto, halign="center", valign="middle",
                                    size_hint_y=None, height=dp(90), color=TEXTO_TENUE,
                                    font_size="16sp"))

    # ================= SECCION NOTAS =================
    def construir_notas(self):
        fila = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        caja = Tarjeta(color=CARD, radio=16, padding=(dp(14), 0))
        self.entrada = TextInput(
            hint_text="Escribe una nota...", multiline=False, font_size="17sp",
            background_normal="", background_active="", background_color=(0, 0, 0, 0),
            foreground_color=TEXTO, cursor_color=ACCENT, hint_text_color=TEXTO_TENUE,
            padding=(0, dp(13)))
        self.entrada.bind(on_text_validate=lambda w: self.agregar_nota())
        caja.add_widget(self.entrada)
        fila.add_widget(caja)
        boton = BotonRedondo(text="+", color=ACCENT, radio=16, font_size="28sp",
                             bold=True, size_hint_x=None, width=dp(56))
        boton.bind(on_press=lambda w: self.agregar_nota())
        fila.add_widget(boton)
        self.contenido.add_widget(fila)

        caja_buscar = Tarjeta(color=CARD, radio=16, padding=(dp(14), 0),
                              size_hint_y=None, height=dp(44))
        self.buscador = TextInput(
            hint_text="Buscar nota...", multiline=False, font_size="15sp",
            background_normal="", background_active="", background_color=(0, 0, 0, 0),
            foreground_color=TEXTO, cursor_color=ACCENT, hint_text_color=TEXTO_TENUE,
            padding=(0, dp(10)))
        self.buscador.bind(text=lambda w, v: self.actualizar_filtro(v))
        caja_buscar.add_widget(self.buscador)
        self.contenido.add_widget(caja_buscar)

        scroll = ScrollView()
        self.lista = BoxLayout(orientation="vertical", size_hint_y=None,
                               spacing=dp(10), padding=(0, dp(4)))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        scroll.add_widget(self.lista)
        self.contenido.add_widget(scroll)
        self.refrescar_lista()

    def actualizar_filtro(self, texto):
        self.filtro = texto.strip().lower()
        self.refrescar_lista()

    def refrescar_lista(self):
        cantidad = len(self.notas)
        etiqueta = "nota" if cantidad == 1 else "notas"
        self.titulo.text = (f"[b]Notas[/b]  "
                            f"[size=13sp][color=fff0f5]({cantidad} {etiqueta})[/color][/size]")
        self.lista.clear_widgets()
        visibles = [(i, n) for i, n in enumerate(self.notas)
                    if self.filtro in n.get("texto", "").lower()]
        visibles.sort(key=lambda t: not t[1].get("fav", False))
        if not self.notas:
            self._mensaje(self.lista, "Aun no tienes notas.\nEscribe una arriba y pulsa  +")
            return
        if not visibles:
            self._mensaje(self.lista, "No se encontraron notas\ncon esa busqueda.")
            return
        for indice, nota in visibles:
            self.lista.add_widget(self.crear_tarjeta(indice, nota))

    def crear_tarjeta(self, indice, nota):
        tarjeta = Tarjeta(color=CARD, radio=16, size_hint_y=None, height=dp(78),
                          padding=(dp(10), dp(8)), spacing=dp(6))
        tarjeta.add_widget(BarraColor(COLORES[nota.get("color", 0) % len(COLORES)],
                                      size_hint_x=None, width=dp(6)))
        columna = BoxLayout(orientation="vertical", spacing=dp(2), padding=(dp(6), 0))
        etiqueta = Label(text=nota.get("texto", ""), halign="left", valign="middle",
                         font_size="17sp", color=TEXTO)
        etiqueta.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        columna.add_widget(etiqueta)
        fecha = Label(text=nota.get("fecha", ""), halign="left", valign="middle",
                      font_size="12sp", color=TEXTO_TENUE, size_hint_y=None, height=dp(18))
        fecha.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        columna.add_widget(fecha)
        tarjeta.add_widget(columna)

        es_fav = nota.get("fav", False)
        b_fav = BotonRedondo(text="*", color=(ORO if es_fav else CARD_BORDE),
                             texto_color=(BLANCO if es_fav else TEXTO_TENUE),
                             radio=20, font_size="22sp", bold=True,
                             size_hint_x=None, width=dp(40))
        b_fav.bind(on_press=lambda w: self.alternar_favorito(indice))
        tarjeta.add_widget(b_fav)
        b_edit = BotonRedondo(text="E", color=ACCENT, radio=20, font_size="16sp",
                              bold=True, size_hint_x=None, width=dp(40))
        b_edit.bind(on_release=lambda w: self.editar_nota(indice))
        tarjeta.add_widget(b_edit)
        b_del = BotonRedondo(text="X", color=BORRAR, radio=20, font_size="18sp",
                             bold=True, size_hint_x=None, width=dp(40))
        b_del.bind(on_release=lambda w: self.confirmar_borrado(indice))
        tarjeta.add_widget(b_del)
        return tarjeta

    def agregar_nota(self):
        texto = self.entrada.text.strip()
        if texto:
            self.notas.append({"texto": texto, "fecha": fecha_ahora(),
                               "fav": False, "color": 0})
            self.guardar_notas()
            self.entrada.text = ""
            self.refrescar_lista()

    def alternar_favorito(self, indice):
        if 0 <= indice < len(self.notas):
            self.notas[indice]["fav"] = not self.notas[indice].get("fav", False)
            self.guardar_notas()
            self.refrescar_lista()

    def confirmar_borrado(self, indice):
        if not (0 <= indice < len(self.notas)):
            return
        contenido = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14))
        contenido.add_widget(Label(text="¿Seguro que quieres borrar esta nota?",
                                   color=TEXTO, font_size="16sp",
                                   halign="center", valign="middle"))
        botones = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        b_no = BotonRedondo(text="No", color=CARD_BORDE, texto_color=TEXTO, radio=14)
        b_si = BotonRedondo(text="Si, borrar", color=BORRAR, radio=14, bold=True)
        botones.add_widget(b_no)
        botones.add_widget(b_si)
        contenido.add_widget(botones)
        popup = Popup(title="Borrar nota", content=contenido, size_hint=(0.85, 0.4),
                      title_color=TEXTO, separator_color=BORRAR)
        b_no.bind(on_press=lambda w: popup.dismiss())

        def borrar(_):
            self.notas.pop(indice)
            self.guardar_notas()
            self.refrescar_lista()
            popup.dismiss()
        b_si.bind(on_press=borrar)
        popup.open()

    def editar_nota(self, indice):
        if not (0 <= indice < len(self.notas)):
            return
        seleccion = {"color": self.notas[indice].get("color", 0)}
        contenido = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        entrada = TextInput(text=self.notas[indice].get("texto", ""),
                            multiline=True, font_size="17sp")
        contenido.add_widget(entrada)
        contenido.add_widget(Label(text="Color de etiqueta:", color=TEXTO,
                                   size_hint_y=None, height=dp(24), font_size="14sp"))
        fila = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        for idx, col in enumerate(COLORES):
            b = BotonRedondo(text=("-" if col is None else ""),
                             color=(col if col else CARD_BORDE),
                             texto_color=TEXTO, radio=14, bold=True)
            b.bind(on_press=lambda w, i=idx: seleccion.update(color=i))
            fila.add_widget(b)
        contenido.add_widget(fila)
        botones = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        b_cancel = BotonRedondo(text="Cancelar", color=CARD_BORDE, texto_color=TEXTO, radio=14)
        b_guardar = BotonRedondo(text="Guardar", color=ACCENT, radio=14, bold=True)
        botones.add_widget(b_cancel)
        botones.add_widget(b_guardar)
        contenido.add_widget(botones)
        popup = Popup(title="Editar nota", content=contenido, size_hint=(0.9, 0.65),
                      title_color=TEXTO, separator_color=ACCENT)
        b_cancel.bind(on_press=lambda w: popup.dismiss())

        def guardar(_):
            nuevo = entrada.text.strip()
            if nuevo:
                self.notas[indice]["texto"] = nuevo
                self.notas[indice]["color"] = seleccion["color"]
                self.guardar_notas()
                self.refrescar_lista()
            popup.dismiss()
        b_guardar.bind(on_press=guardar)
        popup.open()

    # ================= SECCION TAREAS (lista + tablero) =================
    def construir_tareas(self):
        fila = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        caja = Tarjeta(color=CARD, radio=16, padding=(dp(14), 0))
        self.tarea_entrada = TextInput(
            hint_text="Nueva tarea...", multiline=False, font_size="17sp",
            background_normal="", background_active="", background_color=(0, 0, 0, 0),
            foreground_color=TEXTO, cursor_color=ACCENT, hint_text_color=TEXTO_TENUE,
            padding=(0, dp(13)))
        self.tarea_entrada.bind(on_text_validate=lambda w: self.agregar_tarea())
        caja.add_widget(self.tarea_entrada)
        fila.add_widget(caja)
        boton = BotonRedondo(text="+", color=ACCENT, radio=16, font_size="28sp",
                             bold=True, size_hint_x=None, width=dp(56))
        boton.bind(on_press=lambda w: self.agregar_tarea())
        fila.add_widget(boton)
        self.contenido.add_widget(fila)

        # Boton para cambiar de vista (Lista <-> Tablero) - ancho completo
        fila_vista = BoxLayout(size_hint_y=None, height=dp(46))
        texto_vista = "Ver como Tablero" if self.vista_tareas == "lista" else "Ver como Lista"
        b_vista = BotonRedondo(text=texto_vista, color=CABECERA, radio=14,
                               font_size="15sp", bold=True)
        b_vista.bind(on_press=lambda w: self.alternar_vista_tareas())
        fila_vista.add_widget(b_vista)
        self.contenido.add_widget(fila_vista)

        if self.vista_tareas == "lista":
            scroll = ScrollView()
            self.tareas_lista = BoxLayout(orientation="vertical", size_hint_y=None,
                                          spacing=dp(10), padding=(0, dp(4)))
            self.tareas_lista.bind(minimum_height=self.tareas_lista.setter("height"))
            scroll.add_widget(self.tareas_lista)
            self.contenido.add_widget(scroll)
            self.refrescar_tareas()
        else:
            self.construir_tablero()

    def alternar_vista_tareas(self):
        self.vista_tareas = "tablero" if self.vista_tareas == "lista" else "lista"
        self.mostrar_seccion("tareas")

    def _titulo_tareas(self):
        hechas = sum(1 for t in self.tareas if t.get("estado") == 2)
        total = len(self.tareas)
        self.titulo.text = (f"[b]Tareas[/b]  "
                            f"[size=13sp][color=fff0f5]({hechas}/{total} hechas)[/color][/size]")

    # ---- Vista Lista ----
    def refrescar_tareas(self):
        self._titulo_tareas()
        self.tareas_lista.clear_widgets()
        if not self.tareas:
            self._mensaje(self.tareas_lista, "Aun no tienes tareas.\nEscribe una arriba y pulsa  +")
            return
        for indice, tarea in enumerate(self.tareas):
            self.tareas_lista.add_widget(self.crear_tarjeta_tarea(indice, tarea))

    def crear_tarjeta_tarea(self, indice, tarea):
        hecha = tarea.get("estado") == 2
        tarjeta = Tarjeta(color=CARD, radio=16, size_hint_y=None, height=dp(60),
                          padding=(dp(8), dp(6)), spacing=dp(8))
        # Casilla grande para marcar/desmarcar
        casilla = BotonRedondo(text=("v" if hecha else ""),
                               color=(VERDE if hecha else CARD_BORDE),
                               texto_color=BLANCO, radio=12, font_size="20sp",
                               bold=True, size_hint_x=None, width=dp(52))
        casilla.bind(on_press=lambda w: self.alternar_tarea(indice))
        tarjeta.add_widget(casilla)
        # El texto tambien es un boton grande: tocarlo marca/desmarca la tarea
        texto = tarea.get("texto", "")
        b_txt = BotonRedondo(color=CARD, texto_color=(TEXTO_TENUE if hecha else TEXTO),
                             radio=12, font_size="17sp")
        b_txt.markup = True
        b_txt.halign = "left"
        b_txt.valign = "middle"
        b_txt.text = ("[s]" + escapar_markup(texto) + "[/s]") if hecha else escapar_markup(texto)
        b_txt.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(14), w.height)))
        b_txt.bind(on_press=lambda w: self.alternar_tarea(indice))
        tarjeta.add_widget(b_txt)
        b_edit = BotonRedondo(text="E", color=ACCENT, radio=12, font_size="15sp",
                              bold=True, size_hint_x=None, width=dp(42))
        b_edit.bind(on_release=lambda w: self.editar_tarea(indice))
        tarjeta.add_widget(b_edit)
        b_del = BotonRedondo(text="X", color=BORRAR, radio=12, font_size="16sp",
                             bold=True, size_hint_x=None, width=dp(42))
        b_del.bind(on_press=lambda w: self.borrar_tarea(indice))
        tarjeta.add_widget(b_del)
        return tarjeta

    def editar_tarea(self, indice):
        if not (0 <= indice < len(self.tareas)):
            return
        cont = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        entrada = TextInput(text=self.tareas[indice].get("texto", ""),
                            multiline=True, font_size="17sp")
        cont.add_widget(entrada)
        botones = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        b_cancel = BotonRedondo(text="Cancelar", color=CARD_BORDE, texto_color=TEXTO, radio=14)
        b_guardar = BotonRedondo(text="Guardar", color=ACCENT, radio=14, bold=True)
        botones.add_widget(b_cancel)
        botones.add_widget(b_guardar)
        cont.add_widget(botones)
        popup = Popup(title="Editar tarea", content=cont, size_hint=(0.9, 0.5),
                      title_color=TEXTO, separator_color=ACCENT)
        b_cancel.bind(on_press=lambda w: popup.dismiss())

        def guardar(_):
            nuevo = entrada.text.strip()
            if nuevo:
                self.tareas[indice]["texto"] = nuevo
                self.guardar_tareas()
                if self.vista_tareas == "lista":
                    self.refrescar_tareas()
                else:
                    self.refrescar_tablero()
            popup.dismiss()
        b_guardar.bind(on_press=guardar)
        popup.open()

    def alternar_tarea(self, indice):
        if 0 <= indice < len(self.tareas):
            self.tareas[indice]["estado"] = 0 if self.tareas[indice].get("estado") == 2 else 2
            self.guardar_tareas()
            self.refrescar_tareas()

    def borrar_tarea(self, indice):
        if 0 <= indice < len(self.tareas):
            self.tareas.pop(indice)
            self.guardar_tareas()
            self.refrescar_tareas()

    # ---- Vista Tablero (Kanban) ----
    def construir_tablero(self):
        board = BoxLayout(spacing=dp(8))
        self.columnas = {}
        defs = [(0, "Pendiente", CABECERA), (1, "En proceso", AMARILLO),
                (2, "Terminado", VERDE)]
        for estado, titulo, col in defs:
            columna = Tarjeta(color=CARD, radio=14, orientation="vertical",
                              padding=dp(6), spacing=dp(6))
            enc = Tarjeta(color=col, radio=10, size_hint_y=None, height=dp(34))
            enc.add_widget(Label(text=titulo, color=BLANCO, bold=True, font_size="13sp"))
            columna.add_widget(enc)
            scroll = ScrollView()
            inner = BoxLayout(orientation="vertical", size_hint_y=None,
                              spacing=dp(6), padding=(0, dp(2)))
            inner.bind(minimum_height=inner.setter("height"))
            scroll.add_widget(inner)
            columna.add_widget(scroll)
            self.columnas[estado] = inner
            board.add_widget(columna)
        self.contenido.add_widget(board)
        self.refrescar_tablero()

    def refrescar_tablero(self):
        self._titulo_tareas()
        for inner in self.columnas.values():
            inner.clear_widgets()
        for indice, tarea in enumerate(self.tareas):
            estado = tarea.get("estado", 0)
            if estado not in self.columnas:
                estado = 0
            self.columnas[estado].add_widget(self.crear_tarjeta_kanban(indice, tarea))

    def crear_tarjeta_kanban(self, indice, tarea):
        estado = tarea.get("estado", 0)
        card = Tarjeta(color=CARD_BORDE, radio=12, orientation="vertical",
                       size_hint_y=None, height=dp(96), padding=dp(6), spacing=dp(4))
        lbl = Label(text=tarea.get("texto", ""), color=TEXTO, font_size="13sp",
                    halign="left", valign="top")
        lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        card.add_widget(lbl)
        botones = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(4))
        b_izq = BotonRedondo(text="<", color=(ACCENT if estado > 0 else CARD),
                             texto_color=(BLANCO if estado > 0 else TEXTO_TENUE),
                             radio=8, font_size="15sp", bold=True)
        b_izq.bind(on_press=lambda w: self.mover_tarea(indice, -1))
        b_der = BotonRedondo(text=">", color=(ACCENT if estado < 2 else CARD),
                             texto_color=(BLANCO if estado < 2 else TEXTO_TENUE),
                             radio=8, font_size="15sp", bold=True)
        b_der.bind(on_press=lambda w: self.mover_tarea(indice, 1))
        b_del = BotonRedondo(text="X", color=BORRAR, radio=8, font_size="12sp",
                             bold=True, size_hint_x=None, width=dp(32))
        b_del.bind(on_press=lambda w: self.borrar_tarea_tablero(indice))
        botones.add_widget(b_izq)
        botones.add_widget(b_der)
        botones.add_widget(b_del)
        card.add_widget(botones)
        return card

    def mover_tarea(self, indice, delta):
        if 0 <= indice < len(self.tareas):
            nuevo = self.tareas[indice].get("estado", 0) + delta
            self.tareas[indice]["estado"] = max(0, min(2, nuevo))
            self.guardar_tareas()
            self.refrescar_tablero()

    def borrar_tarea_tablero(self, indice):
        if 0 <= indice < len(self.tareas):
            self.tareas.pop(indice)
            self.guardar_tareas()
            self.refrescar_tablero()

    def agregar_tarea(self):
        texto = self.tarea_entrada.text.strip()
        if texto:
            self.tareas.append({"texto": texto, "estado": 0})
            self.guardar_tareas()
            self.tarea_entrada.text = ""
            if self.vista_tareas == "lista":
                self.refrescar_tareas()
            else:
                self.refrescar_tablero()

    # ================= SECCION AVISOS (recordatorios) =================
    def construir_avisos(self):
        self.titulo.text = "[b]Recordatorios[/b]"
        fila = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        caja = Tarjeta(color=CARD, radio=16, padding=(dp(14), 0))
        self.aviso_entrada = TextInput(
            hint_text="Ej: Llamar a Juan el lunes a las 5 pm", multiline=False,
            font_size="15sp", background_normal="", background_active="",
            background_color=(0, 0, 0, 0), foreground_color=TEXTO, cursor_color=ACCENT,
            hint_text_color=TEXTO_TENUE, padding=(0, dp(13)))
        self.aviso_entrada.bind(on_text_validate=lambda w: self.agregar_recordatorio())
        caja.add_widget(self.aviso_entrada)
        fila.add_widget(caja)
        boton = BotonRedondo(text="+", color=ACCENT, radio=16, font_size="28sp",
                             bold=True, size_hint_x=None, width=dp(56))
        boton.bind(on_press=lambda w: self.agregar_recordatorio())
        fila.add_widget(boton)
        self.contenido.add_widget(fila)

        info = Label(text="Escribe con dia y hora y yo detecto cuando avisarte.",
                     color=TEXTO_TENUE, font_size="12sp", size_hint_y=None, height=dp(22))
        self.contenido.add_widget(info)

        # Boton para cambiar de vista (Lista <-> Calendario)
        fila_vista = BoxLayout(size_hint_y=None, height=dp(44))
        texto_vista = "Ver calendario" if self.vista_avisos == "lista" else "Ver lista"
        b_vista = BotonRedondo(text=texto_vista, color=CABECERA, radio=14,
                               font_size="15sp", bold=True)
        b_vista.bind(on_press=lambda w: self.alternar_vista_avisos())
        fila_vista.add_widget(b_vista)
        self.contenido.add_widget(fila_vista)

        if self.vista_avisos == "lista":
            scroll = ScrollView()
            self.avisos_lista = BoxLayout(orientation="vertical", size_hint_y=None,
                                          spacing=dp(10), padding=(0, dp(4)))
            self.avisos_lista.bind(minimum_height=self.avisos_lista.setter("height"))
            scroll.add_widget(self.avisos_lista)
            self.contenido.add_widget(scroll)
            self.refrescar_avisos()
        else:
            self.construir_calendario()

    def alternar_vista_avisos(self):
        self.vista_avisos = "calendario" if self.vista_avisos == "lista" else "lista"
        self.mostrar_seccion("avisos")

    def refrescar_avisos(self):
        if self.seccion != "avisos" or self.vista_avisos != "lista":
            return
        self.avisos_lista.clear_widgets()
        if not self.recordatorios:
            self._mensaje(self.avisos_lista, "Aun no tienes recordatorios.")
            return
        for indice, r in enumerate(self.recordatorios):
            self.avisos_lista.add_widget(self.crear_tarjeta_aviso(indice, r))

    def crear_tarjeta_aviso(self, indice, r):
        tarjeta = Tarjeta(color=CARD, radio=16, size_hint_y=None, height=dp(74),
                          padding=(dp(12), dp(8)), spacing=dp(8))
        columna = BoxLayout(orientation="vertical", spacing=dp(2))
        etiqueta = Label(text=r.get("texto", ""), halign="left", valign="middle",
                         font_size="16sp", color=TEXTO)
        etiqueta.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        columna.add_widget(etiqueta)
        if r.get("cuando"):
            try:
                dt = datetime.datetime.fromisoformat(r["cuando"])
                info = "Avisare: " + formatear_cuando(dt)
                if r.get("avisado"):
                    info = "Ya avisado - " + formatear_cuando(dt)
            except ValueError:
                info = ""
        else:
            info = "No detecte fecha/hora"
        sub = Label(text=info, halign="left", valign="middle", font_size="12sp",
                    color=TEXTO_TENUE, size_hint_y=None, height=dp(18))
        sub.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        columna.add_widget(sub)
        tarjeta.add_widget(columna)
        b_edit = BotonRedondo(text="E", color=ACCENT, radio=18, font_size="15sp",
                              bold=True, size_hint_x=None, width=dp(40))
        b_edit.bind(on_release=lambda w: self.editar_recordatorio(indice))
        tarjeta.add_widget(b_edit)
        b_del = BotonRedondo(text="X", color=BORRAR, radio=18, font_size="16sp",
                             bold=True, size_hint_x=None, width=dp(40))
        b_del.bind(on_press=lambda w: self.borrar_recordatorio(indice))
        tarjeta.add_widget(b_del)
        return tarjeta

    def editar_recordatorio(self, indice):
        if not (0 <= indice < len(self.recordatorios)):
            return
        cont = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        cont.add_widget(Label(text="Edita el recordatorio (con dia y hora):",
                              color=TEXTO, size_hint_y=None, height=dp(24), font_size="14sp"))
        entrada = TextInput(text=self.recordatorios[indice].get("texto", ""),
                            multiline=True, font_size="16sp")
        cont.add_widget(entrada)
        botones = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        b_cancel = BotonRedondo(text="Cancelar", color=CARD_BORDE, texto_color=TEXTO, radio=14)
        b_guardar = BotonRedondo(text="Guardar", color=ACCENT, radio=14, bold=True)
        botones.add_widget(b_cancel)
        botones.add_widget(b_guardar)
        cont.add_widget(botones)
        popup = Popup(title="Editar recordatorio", content=cont, size_hint=(0.9, 0.55),
                      title_color=TEXTO, separator_color=ACCENT)
        b_cancel.bind(on_press=lambda w: popup.dismiss())

        def guardar(_):
            nuevo = entrada.text.strip()
            if nuevo:
                dt = parsear_fecha_hora(nuevo)
                self.recordatorios[indice]["texto"] = nuevo
                self.recordatorios[indice]["cuando"] = dt.isoformat() if dt else ""
                self.recordatorios[indice]["avisado"] = False
                self.guardar_recordatorios()
                self.refrescar_avisos()
            popup.dismiss()
        b_guardar.bind(on_press=guardar)
        popup.open()

    # ---------- Vista Calendario ----------
    def construir_calendario(self):
        NOMBRES_MES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                       "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        # Barra de navegacion del mes
        barra = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        b_prev = BotonRedondo(text="<", color=ACCENT, radio=12, bold=True,
                              size_hint_x=None, width=dp(50))
        b_prev.bind(on_press=lambda w: self.cambiar_mes(-1))
        titulo_mes = BotonRedondo(text=f"{NOMBRES_MES[self.cal_mes]} {self.cal_anio}",
                                  color=CABECERA, radio=12, bold=True, font_size="15sp")
        b_next = BotonRedondo(text=">", color=ACCENT, radio=12, bold=True,
                              size_hint_x=None, width=dp(50))
        b_next.bind(on_press=lambda w: self.cambiar_mes(1))
        barra.add_widget(b_prev)
        barra.add_widget(titulo_mes)
        barra.add_widget(b_next)
        self.contenido.add_widget(barra)

        # Encabezado de dias
        cab = GridLayout(cols=7, size_hint_y=None, height=dp(22))
        for d in ["L", "M", "X", "J", "V", "S", "D"]:
            cab.add_widget(Label(text=d, color=TEXTO_TENUE, font_size="12sp", bold=True))
        self.contenido.add_widget(cab)

        # Dias con recordatorio (de este mes)
        dias_con_aviso = {}
        for r in self.recordatorios:
            if r.get("cuando"):
                try:
                    dt = datetime.datetime.fromisoformat(r["cuando"])
                    if dt.year == self.cal_anio and dt.month == self.cal_mes:
                        dias_con_aviso.setdefault(dt.day, 0)
                        dias_con_aviso[dt.day] += 1
                except ValueError:
                    pass

        hoy = datetime.datetime.now()
        grid = GridLayout(cols=7, spacing=dp(4))
        for semana in calendar.Calendar().monthdayscalendar(self.cal_anio, self.cal_mes):
            for dia in semana:
                if dia == 0:
                    grid.add_widget(Label(text=""))
                    continue
                tiene = dia in dias_con_aviso
                es_hoy = (dia == hoy.day and self.cal_mes == hoy.month
                          and self.cal_anio == hoy.year)
                if tiene:
                    color = ACCENT
                elif es_hoy:
                    color = CABECERA
                else:
                    color = CARD
                celda = BotonRedondo(
                    text=str(dia), color=color, radio=10,
                    texto_color=(BLANCO if (tiene or es_hoy) else TEXTO),
                    font_size="14sp", bold=tiene)
                celda.bind(on_release=lambda w, d=dia: self.ver_dia(d))
                grid.add_widget(celda)
        self.contenido.add_widget(grid)

    def cambiar_mes(self, delta):
        mes = self.cal_mes + delta
        anio = self.cal_anio
        if mes < 1:
            mes = 12
            anio -= 1
        elif mes > 12:
            mes = 1
            anio += 1
        self.cal_mes = mes
        self.cal_anio = anio
        self.mostrar_seccion("avisos")

    def ver_dia(self, dia):
        fecha = datetime.date(self.cal_anio, self.cal_mes, dia)
        deldia = []
        for r in self.recordatorios:
            if r.get("cuando"):
                try:
                    dt = datetime.datetime.fromisoformat(r["cuando"])
                    if dt.date() == fecha:
                        deldia.append((dt, r.get("texto", "")))
                except ValueError:
                    pass
        deldia.sort()
        cont = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        titulo = f"{dia}/{self.cal_mes}/{self.cal_anio}"
        if not deldia:
            cont.add_widget(Label(text="No hay recordatorios este dia.",
                                  color=TEXTO, font_size="15sp"))
        else:
            for dt, txt in deldia:
                cont.add_widget(Label(text=f"{dt.hour:02d}:{dt.minute:02d}  {txt}",
                                      color=TEXTO, font_size="15sp", halign="left",
                                      valign="middle", text_size=(dp(240), None),
                                      size_hint_y=None, height=dp(30)))
        b_ok = BotonRedondo(text="Cerrar", color=ACCENT, radio=14,
                            size_hint_y=None, height=dp(44))
        cont.add_widget(b_ok)
        popup = Popup(title=titulo, content=cont, size_hint=(0.85, 0.5),
                      title_color=TEXTO, separator_color=ACCENT)
        b_ok.bind(on_press=lambda w: popup.dismiss())
        popup.open()

    def agregar_recordatorio(self):
        texto = self.aviso_entrada.text.strip()
        if not texto:
            return
        dt = parsear_fecha_hora(texto)
        self.recordatorios.append({
            "texto": texto,
            "cuando": dt.isoformat() if dt else "",
            "avisado": False,
        })
        self.guardar_recordatorios()
        self.aviso_entrada.text = ""
        if self.vista_avisos == "calendario":
            self.mostrar_seccion("avisos")
        else:
            self.refrescar_avisos()

    def borrar_recordatorio(self, indice):
        if 0 <= indice < len(self.recordatorios):
            self.recordatorios.pop(indice)
            self.guardar_recordatorios()
            self.refrescar_avisos()

    def revisar_recordatorios(self, *args):
        ahora = datetime.datetime.now()
        cambio = False
        for r in self.recordatorios:
            if r.get("cuando") and not r.get("avisado"):
                try:
                    cuando = datetime.datetime.fromisoformat(r["cuando"])
                except ValueError:
                    continue
                if cuando <= ahora:
                    self.notificar(r.get("texto", "Recordatorio"))
                    r["avisado"] = True
                    cambio = True
        if cambio:
            self.guardar_recordatorios()
            self.refrescar_avisos()

    def notificar(self, texto):
        try:
            from plyer import notification
            notification.notify(title="Recordatorio", message=texto, timeout=10)
        except Exception:
            contenido = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
            contenido.add_widget(Label(text=texto, color=TEXTO, font_size="16sp",
                                       halign="center", valign="middle"))
            b_ok = BotonRedondo(text="OK", color=ACCENT, radio=14,
                                size_hint_y=None, height=dp(46))
            contenido.add_widget(b_ok)
            popup = Popup(title="Recordatorio", content=contenido, size_hint=(0.85, 0.4),
                          title_color=TEXTO, separator_color=ACCENT)
            b_ok.bind(on_press=lambda w: popup.dismiss())
            popup.open()

    # ================= SECCION DIBUJO =================
    def construir_dibujo(self):
        self.titulo.text = "[b]Dibujo y bocetos[/b]"
        fila_vista = BoxLayout(size_hint_y=None, height=dp(46))
        texto_vista = "Ver galeria" if self.vista_dibujo == "lienzo" else "Volver al lienzo"
        b_vista = BotonRedondo(text=texto_vista, color=CABECERA, radio=14,
                               font_size="15sp", bold=True)
        b_vista.bind(on_press=lambda w: self.alternar_vista_dibujo())
        fila_vista.add_widget(b_vista)
        self.contenido.add_widget(fila_vista)

        if self.vista_dibujo == "lienzo":
            self.construir_lienzo()
        else:
            self.construir_galeria()

    def alternar_vista_dibujo(self):
        self.vista_dibujo = "galeria" if self.vista_dibujo == "lienzo" else "lienzo"
        self.mostrar_seccion("dibujo")

    def construir_lienzo(self):
        # Paleta de colores en una barra que se desliza de lado
        scroll_col = ScrollView(size_hint_y=None, height=dp(48),
                                do_scroll_x=True, do_scroll_y=False,
                                bar_width=dp(3))
        barra1 = BoxLayout(size_hint_x=None, height=dp(46), spacing=dp(6),
                           padding=(dp(2), dp(2)))
        barra1.bind(minimum_width=barra1.setter("width"))
        borrador = BotonRedondo(text="Borrador", color=CARD_BORDE, texto_color=TEXTO,
                                radio=12, font_size="12sp", bold=True,
                                size_hint_x=None, width=dp(84))
        borrador.bind(on_press=lambda w: self.set_color((1, 1, 1, 1)))
        barra1.add_widget(borrador)
        for col in DIBUJO_COLORES:
            b = BotonRedondo(color=col, radio=20, size_hint_x=None, width=dp(42))
            b.bind(on_press=lambda w, c=col: self.set_color(c))
            barra1.add_widget(b)
        scroll_col.add_widget(barra1)
        self.contenido.add_widget(scroll_col)

        barra2 = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        for nombre, g in [("Fino", 2), ("Medio", 5), ("Grueso", 10)]:
            b = BotonRedondo(text=nombre, color=ACCENT, radio=12, font_size="13sp", bold=True)
            b.bind(on_press=lambda w, gg=g: self.set_grosor(gg))
            barra2.add_widget(b)
        limpiar = BotonRedondo(text="Limpiar", color=BORRAR, radio=12, font_size="13sp", bold=True)
        limpiar.bind(on_press=lambda w: self.lienzo.limpiar())
        barra2.add_widget(limpiar)
        guardar = BotonRedondo(text="Guardar", color=VERDE, radio=12, font_size="13sp", bold=True)
        guardar.bind(on_press=lambda w: self.guardar_dibujo())
        barra2.add_widget(guardar)
        self.contenido.add_widget(barra2)

        if self.lienzo is None:
            self.lienzo = Lienzo()
        elif self.lienzo.parent is not None:
            # lo soltamos del sitio anterior antes de volver a colocarlo
            self.lienzo.parent.remove_widget(self.lienzo)
        marco = Tarjeta(color=CARD, radio=16, padding=dp(4))
        marco.add_widget(self.lienzo)
        self.contenido.add_widget(marco)

    def set_color(self, color):
        if self.lienzo:
            self.lienzo.color_lapiz = color

    def set_grosor(self, grosor):
        if self.lienzo:
            self.lienzo.grosor = grosor

    def guardar_dibujo(self):
        if not self.lienzo:
            return
        if not self.lienzo.trazos and self.lienzo._img_tex is None:
            return   # nada que guardar (lienzo vacio)
        nombre = "dibujo_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        ruta = os.path.join(self.dir_dibujos, nombre)
        try:
            self.lienzo.guardar_png(ruta)
        except Exception:
            self.lienzo.export_to_png(ruta)   # respaldo por si falla el FBO
        self.lienzo.limpiar()   # empieza un lienzo nuevo en blanco
        contenido = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        contenido.add_widget(Label(text="Dibujo guardado en la galeria.\nEl lienzo esta listo para uno nuevo.",
                                   color=TEXTO, font_size="15sp", halign="center", valign="middle"))
        b_ok = BotonRedondo(text="OK", color=ACCENT, radio=14, size_hint_y=None, height=dp(46))
        contenido.add_widget(b_ok)
        popup = Popup(title="Guardado", content=contenido, size_hint=(0.85, 0.4),
                      title_color=TEXTO, separator_color=VERDE)
        b_ok.bind(on_press=lambda w: popup.dismiss())
        popup.open()

    # ---- Galeria de dibujos ----
    def listar_dibujos(self):
        try:
            archivos = [f for f in os.listdir(self.dir_dibujos) if f.endswith(".png")]
        except OSError:
            return []
        archivos.sort(reverse=True)   # mas nuevos primero
        return [os.path.join(self.dir_dibujos, f) for f in archivos]

    def etiqueta_dibujo(self, ruta):
        m = re.search(r"(\d{8})_(\d{6})", os.path.basename(ruta))
        if m:
            try:
                dt = datetime.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
                return formatear_cuando(dt)
            except ValueError:
                pass
        return os.path.basename(ruta)

    def construir_galeria(self):
        archivos = self.listar_dibujos()
        if not archivos:
            caja = BoxLayout()
            self._mensaje(caja, "Aun no has guardado dibujos.\nDibuja y pulsa Guardar.")
            self.contenido.add_widget(caja)
            return
        scroll = ScrollView()
        grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(10), padding=(0, dp(4)))
        grid.bind(minimum_height=grid.setter("height"))
        for ruta in archivos:
            grid.add_widget(self.crear_miniatura(ruta))
        scroll.add_widget(grid)
        self.contenido.add_widget(scroll)

    def crear_miniatura(self, ruta):
        card = Tarjeta(color=CARD, radio=14, orientation="vertical",
                       size_hint_y=None, height=dp(212), padding=dp(6), spacing=dp(4))
        img = Image(source=ruta, allow_stretch=True, keep_ratio=True)
        card.add_widget(img)
        fecha = Label(text=self.etiqueta_dibujo(ruta), color=TEXTO_TENUE,
                      font_size="11sp", size_hint_y=None, height=dp(16))
        card.add_widget(fecha)
        fila = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(5))
        b_edit = BotonRedondo(text="Editar", color=VERDE, radio=8, font_size="12sp", bold=True)
        b_edit.bind(on_release=lambda w: self.editar_dibujo(ruta))
        fila.add_widget(b_edit)
        b_ver = BotonRedondo(text="Ver", color=ACCENT, radio=8, font_size="12sp", bold=True)
        b_ver.bind(on_release=lambda w: self.ver_dibujo(ruta))
        fila.add_widget(b_ver)
        b_del = BotonRedondo(text="X", color=BORRAR, radio=8, font_size="12sp",
                             bold=True, size_hint_x=None, width=dp(34))
        b_del.bind(on_release=lambda w: self.borrar_dibujo(ruta))
        fila.add_widget(b_del)
        card.add_widget(fila)
        return card

    def editar_dibujo(self, ruta):
        if self.lienzo is None:
            self.lienzo = Lienzo()
        self.lienzo.cargar_imagen(ruta)
        self.vista_dibujo = "lienzo"
        self.mostrar_seccion("dibujo")

    def ver_dibujo(self, ruta):
        contenido = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        contenido.add_widget(Image(source=ruta, allow_stretch=True, keep_ratio=True))
        b_ok = BotonRedondo(text="Cerrar", color=ACCENT, radio=14,
                            size_hint_y=None, height=dp(46))
        contenido.add_widget(b_ok)
        popup = Popup(title=self.etiqueta_dibujo(ruta), content=contenido,
                      size_hint=(0.95, 0.9), title_color=TEXTO, separator_color=ACCENT)
        b_ok.bind(on_press=lambda w: popup.dismiss())
        popup.open()

    def borrar_dibujo(self, ruta):
        contenido = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14))
        contenido.add_widget(Label(text="¿Borrar este dibujo?", color=TEXTO,
                                   font_size="16sp", halign="center", valign="middle"))
        botones = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        b_no = BotonRedondo(text="No", color=CARD_BORDE, texto_color=TEXTO, radio=14)
        b_si = BotonRedondo(text="Si, borrar", color=BORRAR, radio=14, bold=True)
        botones.add_widget(b_no)
        botones.add_widget(b_si)
        contenido.add_widget(botones)
        popup = Popup(title="Borrar dibujo", content=contenido, size_hint=(0.85, 0.4),
                      title_color=TEXTO, separator_color=BORRAR)
        b_no.bind(on_press=lambda w: popup.dismiss())

        def borrar(_):
            try:
                os.remove(ruta)
            except OSError:
                pass
            popup.dismiss()
            self.mostrar_seccion("dibujo")
        b_si.bind(on_press=borrar)
        popup.open()

    # ================= SECCION IA (asistente) =================
    def construir_ia(self):
        self.titulo.text = "[b]Asistente IA[/b]"

        # Barra superior: estado de la clave + boton para configurarla
        fila_top = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        estado = "Clave lista" if self.config_app.get("api_key") else "Falta la clave API"
        et = Label(text=estado, color=TEXTO_TENUE, font_size="12sp",
                   halign="left", valign="middle")
        et.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        fila_top.add_widget(et)
        b_borrar = BotonRedondo(text="Limpiar", color=CARD_BORDE, texto_color=TEXTO,
                                radio=12, font_size="12sp", bold=True,
                                size_hint_x=None, width=dp(80))
        b_borrar.bind(on_press=lambda w: self.limpiar_chat())
        fila_top.add_widget(b_borrar)
        b_clave = BotonRedondo(text="Clave API", color=CARD_BORDE, texto_color=TEXTO,
                               radio=12, font_size="12sp", bold=True,
                               size_hint_x=None, width=dp(100))
        b_clave.bind(on_release=lambda w: self.config_clave())
        fila_top.add_widget(b_clave)
        self.contenido.add_widget(fila_top)

        # Chat
        self.chat_scroll = ScrollView()
        self.chat_lista = BoxLayout(orientation="vertical", size_hint_y=None,
                                    spacing=dp(8), padding=(0, dp(4)))
        self.chat_lista.bind(minimum_height=self.chat_lista.setter("height"))
        self.chat_scroll.add_widget(self.chat_lista)
        self.contenido.add_widget(self.chat_scroll)

        # Entrada + enviar
        fila = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        caja = Tarjeta(color=CARD, radio=16, padding=(dp(14), 0))
        self.ia_entrada = TextInput(
            hint_text="Escribe tu pregunta...", multiline=False, font_size="16sp",
            background_normal="", background_active="", background_color=(0, 0, 0, 0),
            foreground_color=TEXTO, cursor_color=ACCENT, hint_text_color=TEXTO_TENUE,
            padding=(0, dp(13)))
        self.ia_entrada.bind(on_text_validate=lambda w: self.enviar_ia())
        caja.add_widget(self.ia_entrada)
        fila.add_widget(caja)
        boton = BotonRedondo(text=">", color=ACCENT, radio=16, font_size="24sp",
                             bold=True, size_hint_x=None, width=dp(56))
        boton.bind(on_press=lambda w: self.enviar_ia())
        fila.add_widget(boton)
        self.contenido.add_widget(fila)

        self.refrescar_chat()

    def crear_burbuja(self, m):
        es_usuario = m.get("role") == "user"
        tarjeta = Tarjeta(color=(ACCENT if es_usuario else CARD), radio=14,
                          orientation="vertical", size_hint_y=None, padding=dp(12))
        tarjeta.bind(minimum_height=tarjeta.setter("height"))
        lbl = Label(text=m.get("content", ""), color=(BLANCO if es_usuario else TEXTO),
                    font_size="15sp", halign="left", valign="top", size_hint_y=None)
        lbl.bind(width=lambda w, *a: setattr(w, "text_size", (w.width, None)),
                 texture_size=lambda w, *a: setattr(w, "height", w.texture_size[1]))
        tarjeta.add_widget(lbl)
        return tarjeta

    def refrescar_chat(self):
        if self.seccion != "ia":
            return
        self.chat_lista.clear_widgets()
        if not self.chat and not self.ia_ocupada:
            self._mensaje(self.chat_lista, "Salúdame o pregúntame lo que quieras :)")
        for m in self.chat:
            if m.get("role") in ("user", "assistant"):
                self.chat_lista.add_widget(self.crear_burbuja(m))
        if self.ia_ocupada:
            self.chat_lista.add_widget(self.crear_burbuja(
                {"role": "assistant", "content": "Escribiendo..."}))
        if self.chat_scroll is not None:
            Clock.schedule_once(lambda dt: setattr(self.chat_scroll, "scroll_y", 0), 0)

    def limpiar_chat(self):
        self.chat = []
        self.guardar_chat()
        self.refrescar_chat()

    def config_clave(self):
        cont = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        cont.add_widget(Label(text="Pega tu clave de API de Groq:", color=TEXTO,
                              size_hint_y=None, height=dp(30), font_size="14sp"))
        entrada = TextInput(text=self.config_app.get("api_key", ""), multiline=False,
                            font_size="13sp", size_hint_y=None, height=dp(46))
        cont.add_widget(entrada)
        nota = Label(text="Es gratis y sin tarjeta: entra a console.groq.com, crea una "
                          "API key (empieza con gsk_) y pegala aqui. Se guarda solo en "
                          "tu dispositivo.",
                     color=TEXTO_TENUE, font_size="11sp",
                     size_hint_y=None, height=dp(60))
        nota.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        cont.add_widget(nota)
        botones = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        b_cancel = BotonRedondo(text="Cancelar", color=CARD_BORDE, texto_color=TEXTO, radio=14)
        b_guardar = BotonRedondo(text="Guardar", color=ACCENT, radio=14, bold=True)
        botones.add_widget(b_cancel)
        botones.add_widget(b_guardar)
        cont.add_widget(botones)
        popup = Popup(title="Clave API", content=cont, size_hint=(0.92, 0.55),
                      title_color=TEXTO, separator_color=ACCENT)
        b_cancel.bind(on_press=lambda w: popup.dismiss())

        def guardar(_):
            self.config_app["api_key"] = limpiar_clave_api(entrada.text)
            self.guardar_config()
            popup.dismiss()
            self.mostrar_seccion("ia")
        b_guardar.bind(on_press=guardar)
        popup.open()

    def enviar_ia(self):
        texto = self.ia_entrada.text.strip()
        if not texto or self.ia_ocupada:
            return
        if not self.config_app.get("api_key"):
            self.config_clave()
            return
        self.chat.append({"role": "user", "content": texto})
        self.ia_entrada.text = ""
        self.ia_ocupada = True
        self.guardar_chat()
        self.refrescar_chat()
        threading.Thread(target=self._llamar_ia, daemon=True).start()

    def _llamar_ia(self):
        try:
            respuesta = self._peticion_ia(self.chat)
        except urllib.error.HTTPError as e:
            try:
                detalle = json.loads(e.read().decode("utf-8"))["error"]["message"]
            except Exception:
                detalle = str(e)
            if e.code in (401, 403):
                respuesta = ("Tu clave API no fue aceptada. Revisa que la copiaste "
                             "completa (empieza con gsk_) en el boton 'Clave API'.\n" + detalle)
            elif e.code == 429:
                respuesta = ("La IA esta ocupada o llegaste al limite gratis por ahora. "
                             "Espera un momento y vuelve a intentar.\n" + detalle)
            else:
                respuesta = "Ups, la IA respondio con un error:\n" + detalle
        except Exception as e:
            respuesta = "No pude conectar con la IA. Revisa tu internet.\n" + str(e)

        def terminar(dt):
            self.ia_ocupada = False
            self.chat.append({"role": "assistant", "content": respuesta})
            self.guardar_chat()
            self.refrescar_chat()
        Clock.schedule_once(terminar, 0)

    def _peticion_ia(self, historial):
        # Usa Groq (gratis, sin tarjeta). Solo los ultimos 20 turnos.
        turnos = [m for m in historial if m.get("role") in ("user", "assistant")][-20:]
        mensajes = [{"role": "system", "content":
                     "Eres un asistente amable y util dentro de una app de notas "
                     "llamada Mi Cuaderno. Responde en espanol, claro y breve."}]
        for m in turnos:
            mensajes.append({"role": m["role"], "content": m["content"]})
        cuerpo = {
            "model": "llama-3.3-70b-versatile",
            "messages": mensajes,
            "max_tokens": 1024,
        }
        clave = limpiar_clave_api(self.config_app.get("api_key", ""))
        datos = json.dumps(cuerpo).encode("utf-8")
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions", data=datos, method="POST",
            headers={"Authorization": "Bearer " + clave,
                     "content-type": "application/json",
                     "User-Agent": "MiCuaderno/1.0 (Android)"})
        try:
            import ssl
            import certifi
            contexto = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            contexto = None
        with urllib.request.urlopen(req, timeout=60, context=contexto) as resp:
            r = json.loads(resp.read().decode("utf-8"))
        opciones = r.get("choices", [])
        if not opciones:
            return "(La IA no devolvio respuesta. Intenta de nuevo.)"
        return opciones[0].get("message", {}).get("content", "").strip() or "(sin texto)"


if __name__ == "__main__":
    AppNotas().run()
