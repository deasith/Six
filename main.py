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

import datetime
import json
import os
import re

from kivy.config import Config
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.clock import Clock
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

# ---- Paleta coquette (rosa pastel) ----
CABECERA    = (0.93, 0.60, 0.70, 1)
ACCENT      = (0.90, 0.52, 0.63, 1)
CARD        = (1.00, 0.97, 0.98, 1)
CARD_BORDE  = (0.94, 0.88, 0.91, 1)
BORRAR      = (0.90, 0.45, 0.52, 1)
VERDE       = (0.45, 0.78, 0.55, 1)
AMARILLO    = (0.98, 0.75, 0.35, 1)
TEXTO       = (0.38, 0.22, 0.28, 1)
TEXTO_TENUE = (0.62, 0.48, 0.54, 1)
ORO         = (0.95, 0.72, 0.35, 1)
BLANCO      = (1, 1, 1, 1)

FONDOS = [
    (0.99, 0.94, 0.95, 1), (0.96, 0.93, 0.98, 1), (0.93, 0.97, 0.95, 1),
    (0.99, 0.97, 0.91, 1), (0.99, 0.94, 0.91, 1), (0.92, 0.96, 0.99, 1),
]

COLORES = [
    None, (0.95, 0.45, 0.60, 1), (0.55, 0.70, 0.95, 1),
    (0.50, 0.80, 0.60, 1), (0.98, 0.80, 0.40, 1), (0.98, 0.60, 0.45, 1),
]

DIBUJO_COLORES = [
    (0.20, 0.20, 0.25, 1), (0.90, 0.30, 0.40, 1), (0.30, 0.55, 0.95, 1),
    (0.30, 0.75, 0.45, 1), (0.98, 0.75, 0.30, 1), (0.95, 0.50, 0.65, 1),
]

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
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._fondo = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._actualizar, size=self._actualizar)

    def _actualizar(self, *args):
        self._fondo.pos = self.pos
        self._fondo.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            with self.canvas:
                Color(*self.color_lapiz)
                touch.ud["linea"] = Line(points=[touch.x, touch.y],
                                         width=self.grosor, cap="round", joint="round")
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if "linea" in touch.ud and self.collide_point(*touch.pos):
            touch.ud["linea"].points += [touch.x, touch.y]
            return True
        return super().on_touch_move(touch)

    def limpiar(self):
        self.canvas.clear()


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
        self.notas = self.cargar_json(self.archivo, self.normalizar_nota)
        self.tareas = self.cargar_json(self.archivo_tareas, self.normalizar_tarea)
        self.recordatorios = self.cargar_json(self.archivo_recordatorios, self.normalizar_recordatorio)
        self.config_app = self.cargar_config()
        self.dir_dibujos = os.path.join(d, "dibujos")
        os.makedirs(self.dir_dibujos, exist_ok=True)
        self.filtro = ""
        self.lienzo = None
        self.seccion = "notas"
        self.vista_tareas = "lista"
        self.vista_dibujo = "lienzo"

        self.aplicar_fondo()

        raiz = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        cabecera = Tarjeta(color=CABECERA, radio=22, size_hint_y=None, height=dp(58),
                           padding=(dp(14), 0), spacing=dp(8))
        self.titulo = Label(markup=True, font_size="21sp", color=BLANCO,
                            halign="left", valign="middle")
        self.titulo.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        cabecera.add_widget(self.titulo)
        boton_fondo = BotonRedondo(text="Fondo", color=CARD, texto_color=CABECERA,
                                   radio=14, font_size="14sp", bold=True,
                                   size_hint_x=None, width=dp(70))
        boton_fondo.bind(on_press=lambda w: self.elegir_fondo())
        cabecera.add_widget(boton_fondo)
        raiz.add_widget(cabecera)

        barra_nav = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.nav = {}
        for clave, texto in [("notas", "Notas"), ("tareas", "Tareas"),
                             ("avisos", "Avisos"), ("dibujo", "Dibujo")]:
            boton = BotonRedondo(text=texto, color=CARD_BORDE, texto_color=TEXTO,
                                 radio=14, font_size="14sp", bold=True)
            boton.bind(on_press=lambda w, c=clave: self.mostrar_seccion(c))
            self.nav[clave] = boton
            barra_nav.add_widget(boton)
        raiz.add_widget(barra_nav)

        self.contenido = BoxLayout(orientation="vertical", spacing=dp(10))
        raiz.add_widget(self.contenido)

        # Revisa los recordatorios cada 20 segundos (con la app abierta)
        Clock.schedule_interval(self.revisar_recordatorios, 20)

        self.mostrar_seccion("notas")
        return raiz

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

    # ---------- Fondo ----------
    def aplicar_fondo(self):
        idx = self.config_app.get("fondo", 0) % len(FONDOS)
        Window.clearcolor = FONDOS[idx]

    def elegir_fondo(self):
        contenido = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14))
        contenido.add_widget(Label(text="Elige un color de fondo:", color=TEXTO,
                                   size_hint_y=None, height=dp(24), font_size="16sp"))
        fila = BoxLayout(spacing=dp(10))
        popup = Popup(title="Color de fondo", size_hint=(0.9, 0.4),
                      title_color=TEXTO, separator_color=ACCENT)
        for idx, col in enumerate(FONDOS):
            swatch = BotonRedondo(color=col, radio=16)
            swatch.bind(on_press=lambda w, i=idx: self._poner_fondo(i, popup))
            fila.add_widget(swatch)
        contenido.add_widget(fila)
        popup.content = contenido
        popup.open()

    def _poner_fondo(self, idx, popup):
        self.config_app["fondo"] = idx
        self.guardar_config()
        self.aplicar_fondo()
        popup.dismiss()

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

    def cargar_config(self):
        if os.path.exists(self.archivo_config):
            try:
                with open(self.archivo_config, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"fondo": 0}

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
        b_edit.bind(on_press=lambda w: self.editar_nota(indice))
        tarjeta.add_widget(b_edit)
        b_del = BotonRedondo(text="X", color=BORRAR, radio=20, font_size="18sp",
                             bold=True, size_hint_x=None, width=dp(40))
        b_del.bind(on_press=lambda w: self.confirmar_borrado(indice))
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
            Clock.schedule_once(lambda dt: self.refrescar_lista(), 0)

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
        Clock.schedule_once(lambda dt: self.mostrar_seccion("tareas"), 0)

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
        b_del = BotonRedondo(text="X", color=BORRAR, radio=12, font_size="16sp",
                             bold=True, size_hint_x=None, width=dp(46))
        b_del.bind(on_press=lambda w: self.borrar_tarea(indice))
        tarjeta.add_widget(b_del)
        return tarjeta

    def alternar_tarea(self, indice):
        if 0 <= indice < len(self.tareas):
            self.tareas[indice]["estado"] = 0 if self.tareas[indice].get("estado") == 2 else 2
            self.guardar_tareas()
            Clock.schedule_once(lambda dt: self.refrescar_tareas(), 0)

    def borrar_tarea(self, indice):
        if 0 <= indice < len(self.tareas):
            self.tareas.pop(indice)
            self.guardar_tareas()
            Clock.schedule_once(lambda dt: self.refrescar_tareas(), 0)

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
            Clock.schedule_once(lambda dt: self.refrescar_tablero(), 0)

    def borrar_tarea_tablero(self, indice):
        if 0 <= indice < len(self.tareas):
            self.tareas.pop(indice)
            self.guardar_tareas()
            Clock.schedule_once(lambda dt: self.refrescar_tablero(), 0)

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

        scroll = ScrollView()
        self.avisos_lista = BoxLayout(orientation="vertical", size_hint_y=None,
                                      spacing=dp(10), padding=(0, dp(4)))
        self.avisos_lista.bind(minimum_height=self.avisos_lista.setter("height"))
        scroll.add_widget(self.avisos_lista)
        self.contenido.add_widget(scroll)
        self.refrescar_avisos()

    def refrescar_avisos(self):
        if self.seccion != "avisos":
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
        b_del = BotonRedondo(text="X", color=BORRAR, radio=18, font_size="16sp",
                             bold=True, size_hint_x=None, width=dp(40))
        b_del.bind(on_press=lambda w: self.borrar_recordatorio(indice))
        tarjeta.add_widget(b_del)
        return tarjeta

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
        Clock.schedule_once(lambda dt: self.mostrar_seccion("dibujo"), 0)

    def construir_lienzo(self):
        barra1 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        for col in DIBUJO_COLORES:
            b = BotonRedondo(color=col, radio=12, size_hint_x=None, width=dp(40))
            b.bind(on_press=lambda w, c=col: self.set_color(c))
            barra1.add_widget(b)
        borrador = BotonRedondo(text="Borrador", color=CARD_BORDE, texto_color=TEXTO,
                                radio=12, font_size="12sp", bold=True)
        borrador.bind(on_press=lambda w: self.set_color((1, 1, 1, 1)))
        barra1.add_widget(borrador)
        self.contenido.add_widget(barra1)

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
        nombre = "dibujo_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        ruta = os.path.join(self.dir_dibujos, nombre)
        self.lienzo.export_to_png(ruta)
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
                       size_hint_y=None, height=dp(190), padding=dp(6), spacing=dp(4))
        img = Image(source=ruta, allow_stretch=True, keep_ratio=True)
        card.add_widget(img)
        fila = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(6))
        fecha = Label(text=self.etiqueta_dibujo(ruta), color=TEXTO_TENUE,
                      font_size="11sp", halign="left", valign="middle")
        fecha.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        fila.add_widget(fecha)
        b_ver = BotonRedondo(text="Ver", color=ACCENT, radio=8, font_size="12sp",
                             bold=True, size_hint_x=None, width=dp(48))
        b_ver.bind(on_press=lambda w: self.ver_dibujo(ruta))
        fila.add_widget(b_ver)
        b_del = BotonRedondo(text="X", color=BORRAR, radio=8, font_size="12sp",
                             bold=True, size_hint_x=None, width=dp(34))
        b_del.bind(on_press=lambda w: self.borrar_dibujo(ruta))
        fila.add_widget(b_del)
        card.add_widget(fila)
        return card

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
            Clock.schedule_once(lambda dt: self.mostrar_seccion("dibujo"), 0)
        b_si.bind(on_press=borrar)
        popup.open()


if __name__ == "__main__":
    AppNotas().run()
