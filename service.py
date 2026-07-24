"""
Servicio en segundo plano para Mi Cuaderno (solo Android).

Corre aunque la app este cerrada y hace dos cosas:
  A) Avisa con una notificacion cuando un recordatorio llega a su hora.
  B) Mantiene una notificacion fija (tipo widget) con el proximo
     recordatorio o cuantas tareas pendientes tienes.

Buildozer lo empaqueta como servicio segun la linea 'services' del
buildozer.spec. En el computador este archivo no se usa.
"""

import json
import os
import time
from datetime import datetime

INTERVALO = 30  # cada cuantos segundos revisa


def cargar(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def guardar(ruta, datos):
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def notificar(titulo, texto, ongoing=False, notif_id=1):
    """Muestra una notificacion en Android usando la API nativa."""
    try:
        from jnius import autoclass, cast
        PythonService = autoclass("org.kivy.android.PythonService")
        service = PythonService.mService
        Context = autoclass("android.content.Context")
        NotificationBuilder = autoclass("android.app.Notification$Builder")
        NotificationManager = autoclass("android.app.NotificationManager")
        VERSION = autoclass("android.os.Build$VERSION")

        nm = cast(NotificationManager,
                  service.getSystemService(Context.NOTIFICATION_SERVICE))
        canal = "recordatorios"
        if VERSION.SDK_INT >= 26:
            NotificationChannel = autoclass("android.app.NotificationChannel")
            channel = NotificationChannel(canal, "Recordatorios",
                                          NotificationManager.IMPORTANCE_HIGH)
            nm.createNotificationChannel(channel)
            builder = NotificationBuilder(service, canal)
        else:
            builder = NotificationBuilder(service)

        builder.setContentTitle(titulo)
        builder.setContentText(texto)
        builder.setSmallIcon(service.getApplicationInfo().icon)
        builder.setOngoing(ongoing)
        nm.notify(notif_id, builder.build())
    except Exception:
        pass


def texto_fijo(recordatorios, tareas):
    """Arma el texto de la notificacion fija (tipo widget)."""
    proximos = []
    for r in recordatorios:
        if r.get("cuando") and not r.get("avisado"):
            try:
                proximos.append((datetime.fromisoformat(r["cuando"]),
                                 r.get("texto", "")))
            except Exception:
                pass
    proximos.sort()
    pendientes = sum(1 for t in tareas if t.get("estado") != 2)
    if proximos:
        dt, txt = proximos[0]
        return f"Proximo: {txt} ({dt.day}/{dt.month} {dt.hour:02d}:{dt.minute:02d})"
    if pendientes:
        return f"Tienes {pendientes} tareas pendientes"
    return "Todo al dia. Sin recordatorios pendientes"


def main():
    datadir = (os.environ.get("PYTHON_SERVICE_ARGUMENT", "")
               or os.environ.get("ANDROID_APP_PATH", ""))
    ruta_r = os.path.join(datadir, "recordatorios.json")
    ruta_t = os.path.join(datadir, "tareas.json")
    siguiente_id = 2

    while True:
        recordatorios = cargar(ruta_r)
        tareas = cargar(ruta_t)

        # B) Notificacion fija tipo widget (id 1, siempre presente)
        notificar("Mi Cuaderno", texto_fijo(recordatorios, tareas),
                  ongoing=True, notif_id=1)

        # A) Avisos de recordatorios que ya llegaron a su hora
        ahora = datetime.now()
        cambio = False
        for r in recordatorios:
            if r.get("cuando") and not r.get("avisado"):
                try:
                    cuando = datetime.fromisoformat(r["cuando"])
                except Exception:
                    continue
                if cuando <= ahora:
                    notificar("Recordatorio", r.get("texto", "Recordatorio"),
                              ongoing=False, notif_id=siguiente_id)
                    siguiente_id += 1
                    r["avisado"] = True
                    cambio = True
        if cambio:
            guardar(ruta_r, recordatorios)

        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
