[app]

# Nombre que se vera en la tablet
title = Mi Cuaderno

# Nombre interno (sin espacios ni acentos)
package.name = misnotas
package.domain = org.misnotas

# Carpeta con el codigo (el punto = carpeta actual)
source.dir = .

# Tipos de archivo que se incluyen en la app
source.include_exts = py,png,jpg,kv,atlas,json

# Version de tu app
version = 1.0

# Icono de la app y pantalla de carga
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

# Librerias de Python que necesita la app
requirements = python3,kivy,plyer

# Permisos de Android (notificaciones + servicio en segundo plano)
android.permissions = POST_NOTIFICATIONS,FOREGROUND_SERVICE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED

# Servicio en segundo plano que avisa aunque la app este cerrada.
# Formato:  NombreDelServicio:archivo.py:tipo
services = Recordatorio:service.py:foreground

# La app se ve en vertical (como celular). Usa 'all' si quieres que rote.
orientation = portrait

# Pantalla completa: 0 = no (se ve la barra de arriba), 1 = si
fullscreen = 0

# Procesadores de Android a soportar (cubre practicamente todas las tablets)
android.archs = arm64-v8a, armeabi-v7a

# Acepta automaticamente las licencias del SDK de Android (evita que se cuelgue)
android.accept_sdk_license = True

[buildozer]

# Nivel de detalle de los mensajes (2 = muestra todo, util si algo falla)
log_level = 2

# Avisa si lo ejecutas como administrador (root)
warn_on_root = 1
