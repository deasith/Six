"""
App de Notas para tablet/celular Android - hecha con Python y Kivy.
Estilo coquette (rosa pastel) con color de fondo personalizable.

Funciones:
- Interfaz coquette y color de fondo a elegir
- Fecha/hora en cada nota y contador de notas
- Buscador de notas
- Editar notas y ponerles color de etiqueta
- Favoritos (suben arriba)
- Confirmacion antes de borrar

Este es el archivo principal que Buildozer usa para crear el .apk.
Se llama 'main.py' obligatoriamente.

Como probarla en tu computador Linux:
    python3 main.py
"""

import datetime
import json
import os

# Quita el circulo rojo del clic derecho (simulador de toque multiple de Kivy)
from kivy.config import Config
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ---- Paleta coquette (rosa pastel) ----  (R, G, B, transparencia) de 0 a 1
CABECERA    = (0.93, 0.60, 0.70, 1)      # rosa fuerte
ACCENT      = (0.90, 0.52, 0.63, 1)      # rosa (botones)
CARD        = (1.00, 0.97, 0.98, 1)      # tarjetas casi blancas
CARD_BORDE  = (0.94, 0.88, 0.91, 1)      # rosa muy claro
BORRAR      = (0.90, 0.45, 0.52, 1)      # rojo rosado
TEXTO       = (0.38, 0.22, 0.28, 1)      # texto oscuro (ciruela)
TEXTO_TENUE = (0.62, 0.48, 0.54, 1)      # texto secundario
ORO         = (0.95, 0.72, 0.35, 1)      # estrella de favorito
BLANCO      = (1, 1, 1, 1)

# Colores de fondo que se pueden elegir (pasteles)
FONDOS = [
    (0.99, 0.94, 0.95, 1),   # 0 - rosa crema
    (0.96, 0.93, 0.98, 1),   # 1 - lavanda
    (0.93, 0.97, 0.95, 1),   # 2 - menta
    (0.99, 0.97, 0.91, 1),   # 3 - vainilla
    (0.99, 0.94, 0.91, 1),   # 4 - durazno
    (0.92, 0.96, 0.99, 1),   # 5 - cielo
]

# Colores de etiqueta que se pueden poner a una nota (el 0 = sin color)
COLORES = [
    None,
    (0.95, 0.45, 0.60, 1),
    (0.55, 0.70, 0.95, 1),
    (0.50, 0.80, 0.60, 1),
    (0.98, 0.80, 0.40, 1),
    (0.98, 0.60, 0.45, 1),
]

MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_ahora():
    ahora = datetime.datetime.now()
    return f"{ahora.day} {MESES[ahora.month - 1]} {ahora.year}, {ahora.hour:02d}:{ahora.minute:02d}"


class Tarjeta(BoxLayout):
    """Un contenedor con fondo de color y esquinas redondeadas."""

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
    """Una barrita de color a la izquierda de la nota (la etiqueta)."""

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
    """Boton con color de fondo, esquinas redondeadas y color de texto propio."""

    def __init__(self, color=ACCENT, radio=16, texto_color=BLANCO, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = texto_color        # color del texto
        self._base = color
        with self.canvas.before:
            self._color = Color(*color)
            self._rect = RoundedRectangle(radius=[radio])
        self.bind(pos=self._actualizar, size=self._actualizar, state=self._al_pulsar)

    def _actualizar(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _al_pulsar(self, *args):
        factor = 0.85 if self.state == "down" else 1.0
        self._color.rgba = (self._base[0] * factor, self._base[1] * factor,
                            self._base[2] * factor, 1)


class AppNotas(App):
    def build(self):
        self.title = "Mis Notas"
        self.archivo = os.path.join(self.user_data_dir, "notas.json")
        self.archivo_config = os.path.join(self.user_data_dir, "config.json")
        self.notas = self.cargar_notas()
        self.config_app = self.cargar_config()
        self.filtro = ""

        self.aplicar_fondo()

        raiz = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        # ---- Cabecera: titulo + boton de fondo ----
        cabecera = Tarjeta(color=CABECERA, radio=22, size_hint_y=None, height=dp(64),
                           padding=(dp(14), 0), spacing=dp(8))
        self.titulo = Label(
            markup=True, font_size="23sp", color=BLANCO,
            halign="left", valign="middle",
        )
        self.titulo.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        cabecera.add_widget(self.titulo)
        boton_fondo = BotonRedondo(
            text="Fondo", color=CARD, texto_color=CABECERA, radio=14,
            font_size="14sp", bold=True, size_hint_x=None, width=dp(72),
        )
        boton_fondo.bind(on_release=lambda w: self.elegir_fondo())
        cabecera.add_widget(boton_fondo)
        raiz.add_widget(cabecera)

        # ---- Fila para escribir una nota nueva ----
        fila = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10))
        caja_entrada = Tarjeta(color=CARD, radio=16, padding=(dp(14), 0))
        self.entrada = TextInput(
            hint_text="Escribe una nota...", multiline=False,
            font_size="17sp", background_normal="", background_active="",
            background_color=(0, 0, 0, 0), foreground_color=TEXTO,
            cursor_color=ACCENT, hint_text_color=TEXTO_TENUE,
            padding=(0, dp(14)),
        )
        self.entrada.bind(on_text_validate=lambda w: self.agregar_nota())
        caja_entrada.add_widget(self.entrada)
        fila.add_widget(caja_entrada)
        boton_add = BotonRedondo(
            text="+", color=ACCENT, radio=16, font_size="28sp", bold=True,
            size_hint_x=None, width=dp(60),
        )
        boton_add.bind(on_release=lambda w: self.agregar_nota())
        fila.add_widget(boton_add)
        raiz.add_widget(fila)

        # ---- Buscador ----
        caja_buscar = Tarjeta(color=CARD, radio=16, padding=(dp(14), 0),
                              size_hint_y=None, height=dp(46))
        self.buscador = TextInput(
            hint_text="Buscar nota...", multiline=False,
            font_size="15sp", background_normal="", background_active="",
            background_color=(0, 0, 0, 0), foreground_color=TEXTO,
            cursor_color=ACCENT, hint_text_color=TEXTO_TENUE,
            padding=(0, dp(11)),
        )
        self.buscador.bind(text=lambda w, valor: self.actualizar_filtro(valor))
        caja_buscar.add_widget(self.buscador)
        raiz.add_widget(caja_buscar)

        # ---- Lista de notas ----
        scroll = ScrollView()
        self.lista = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(10),
            padding=(0, dp(4)),
        )
        self.lista.bind(minimum_height=self.lista.setter("height"))
        scroll.add_widget(self.lista)
        raiz.add_widget(scroll)

        self.refrescar_lista()
        return raiz

    # ---------- Fondo ----------
    def aplicar_fondo(self):
        idx = self.config_app.get("fondo", 0) % len(FONDOS)
        Window.clearcolor = FONDOS[idx]

    def elegir_fondo(self):
        contenido = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14))
        contenido.add_widget(Label(text="Elige un color de fondo:", color=TEXTO,
                                   size_hint_y=None, height=dp(24), font_size="16sp"))
        fila_colores = BoxLayout(spacing=dp(10))
        popup = Popup(title="Color de fondo", size_hint=(0.9, 0.4),
                      title_color=TEXTO, separator_color=ACCENT)
        for idx, col in enumerate(FONDOS):
            swatch = BotonRedondo(color=col, radio=16)
            swatch.bind(on_release=lambda w, i=idx: self._poner_fondo(i, popup))
            fila_colores.add_widget(swatch)
        contenido.add_widget(fila_colores)
        popup.content = contenido
        popup.open()

    def _poner_fondo(self, idx, popup):
        self.config_app["fondo"] = idx
        self.guardar_config()
        self.aplicar_fondo()
        popup.dismiss()

    # ---------- Datos ----------
    def cargar_config(self):
        if os.path.exists(self.archivo_config):
            try:
                with open(self.archivo_config, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"fondo": 0}

    def guardar_config(self):
        with open(self.archivo_config, "w", encoding="utf-8") as f:
            json.dump(self.config_app, f, ensure_ascii=False, indent=2)

    def cargar_notas(self):
        if not os.path.exists(self.archivo):
            return []
        try:
            with open(self.archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
        notas = []
        for nota in datos:
            if isinstance(nota, str):
                nota = {"texto": nota, "fecha": ""}
            nota.setdefault("texto", "")
            nota.setdefault("fecha", "")
            nota.setdefault("fav", False)
            nota.setdefault("color", 0)
            notas.append(nota)
        return notas

    def guardar_notas(self):
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(self.notas, f, ensure_ascii=False, indent=2)

    # ---------- Buscador ----------
    def actualizar_filtro(self, texto):
        self.filtro = texto.strip().lower()
        self.refrescar_lista()

    # ---------- Dibujar la lista ----------
    def refrescar_lista(self):
        cantidad = len(self.notas)
        etiqueta = "nota" if cantidad == 1 else "notas"
        self.titulo.text = (
            f"[b]Mis Notas[/b]  "
            f"[size=14sp][color=fff0f5]({cantidad} {etiqueta})[/color][/size]"
        )
        self.lista.clear_widgets()
        visibles = [
            (i, n) for i, n in enumerate(self.notas)
            if self.filtro in n.get("texto", "").lower()
        ]
        visibles.sort(key=lambda t: not t[1].get("fav", False))
        if not self.notas:
            self._mensaje("Aun no tienes notas.\nEscribe una arriba y pulsa  +")
            return
        if not visibles:
            self._mensaje("No se encontraron notas\ncon esa busqueda.")
            return
        for indice, nota in visibles:
            self.lista.add_widget(self.crear_tarjeta(indice, nota))

    def _mensaje(self, texto):
        self.lista.add_widget(Label(
            text=texto, halign="center", valign="middle", size_hint_y=None,
            height=dp(90), color=TEXTO_TENUE, font_size="16sp",
        ))

    def crear_tarjeta(self, indice, nota):
        tarjeta = Tarjeta(color=CARD, radio=16, size_hint_y=None, height=dp(78),
                          padding=(dp(10), dp(8)), spacing=dp(6))
        color_tag = COLORES[nota.get("color", 0) % len(COLORES)]
        tarjeta.add_widget(BarraColor(color_tag, size_hint_x=None, width=dp(6)))

        columna = BoxLayout(orientation="vertical", spacing=dp(2), padding=(dp(6), 0))
        etiqueta = Label(
            text=nota.get("texto", ""), halign="left", valign="middle",
            font_size="17sp", color=TEXTO,
        )
        etiqueta.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        columna.add_widget(etiqueta)
        etiqueta_fecha = Label(
            text=nota.get("fecha", ""), halign="left", valign="middle",
            font_size="12sp", color=TEXTO_TENUE, size_hint_y=None, height=dp(18),
        )
        etiqueta_fecha.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        columna.add_widget(etiqueta_fecha)
        tarjeta.add_widget(columna)

        es_fav = nota.get("fav", False)
        boton_fav = BotonRedondo(
            text="*", color=(ORO if es_fav else CARD_BORDE),
            texto_color=(BLANCO if es_fav else TEXTO_TENUE),
            radio=20, font_size="22sp", bold=True, size_hint_x=None, width=dp(40),
        )
        boton_fav.bind(on_release=lambda w: self.alternar_favorito(indice))
        tarjeta.add_widget(boton_fav)

        boton_editar = BotonRedondo(
            text="E", color=ACCENT, radio=20, font_size="16sp", bold=True,
            size_hint_x=None, width=dp(40),
        )
        boton_editar.bind(on_release=lambda w: self.editar_nota(indice))
        tarjeta.add_widget(boton_editar)

        boton_borrar = BotonRedondo(
            text="X", color=BORRAR, radio=20, font_size="18sp", bold=True,
            size_hint_x=None, width=dp(40),
        )
        boton_borrar.bind(on_release=lambda w: self.confirmar_borrado(indice))
        tarjeta.add_widget(boton_borrar)
        return tarjeta

    # ---------- Acciones ----------
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
        contenido.add_widget(Label(
            text="¿Seguro que quieres borrar esta nota?",
            color=TEXTO, font_size="16sp", halign="center", valign="middle",
        ))
        botones = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        boton_no = BotonRedondo(text="No", color=CARD_BORDE, texto_color=TEXTO, radio=14)
        boton_si = BotonRedondo(text="Si, borrar", color=BORRAR, radio=14, bold=True)
        botones.add_widget(boton_no)
        botones.add_widget(boton_si)
        contenido.add_widget(botones)
        popup = Popup(title="Borrar nota", content=contenido, size_hint=(0.85, 0.4),
                      title_color=TEXTO, separator_color=BORRAR)
        boton_no.bind(on_release=lambda w: popup.dismiss())

        def borrar(_):
            self.notas.pop(indice)
            self.guardar_notas()
            self.refrescar_lista()
            popup.dismiss()

        boton_si.bind(on_release=borrar)
        popup.open()

    def editar_nota(self, indice):
        if not (0 <= indice < len(self.notas)):
            return
        seleccion = {"color": self.notas[indice].get("color", 0)}
        contenido = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        entrada = TextInput(
            text=self.notas[indice].get("texto", ""), multiline=True,
            font_size="17sp",
        )
        contenido.add_widget(entrada)
        contenido.add_widget(Label(text="Color de etiqueta:", color=TEXTO,
                                   size_hint_y=None, height=dp(24), font_size="14sp"))
        fila_colores = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        for idx, col in enumerate(COLORES):
            texto_boton = "-" if col is None else ""
            boton_color = BotonRedondo(
                text=texto_boton, color=(col if col else CARD_BORDE),
                texto_color=TEXTO, radio=14, bold=True,
            )
            boton_color.bind(on_release=lambda w, i=idx: seleccion.update(color=i))
            fila_colores.add_widget(boton_color)
        contenido.add_widget(fila_colores)
        botones = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        boton_cancelar = BotonRedondo(text="Cancelar", color=CARD_BORDE,
                                      texto_color=TEXTO, radio=14)
        boton_guardar = BotonRedondo(text="Guardar", color=ACCENT, radio=14, bold=True)
        botones.add_widget(boton_cancelar)
        botones.add_widget(boton_guardar)
        contenido.add_widget(botones)
        popup = Popup(title="Editar nota", content=contenido, size_hint=(0.9, 0.65),
                      title_color=TEXTO, separator_color=ACCENT)
        boton_cancelar.bind(on_release=lambda w: popup.dismiss())

        def guardar(_):
            nuevo = entrada.text.strip()
            if nuevo:
                self.notas[indice]["texto"] = nuevo
                self.notas[indice]["color"] = seleccion["color"]
                self.guardar_notas()
                self.refrescar_lista()
            popup.dismiss()

        boton_guardar.bind(on_release=guardar)
        popup.open()


if __name__ == "__main__":
    AppNotas().run()
