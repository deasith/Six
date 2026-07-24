# 📱 Guía: app de notas en tu tablet Samsung (con Python)

Vas a hacer tu app con **Python + Kivy** y la vas a instalar en tu tablet
Samsung (Android). Sigue los pasos en orden. Copia y pega cada comando en la
**terminal** de tu Linux.

> Estos comandos son para **Ubuntu / Linux Mint / Debian**. Si usas otra
> distribución, avísame y te doy los tuyos.

---

## PARTE 1 — Probar la app en tu computador (fácil y rápido)

Así ves la app funcionando antes de meterla en la tablet.

### Paso 1. Instalar Kivy

```
pip install kivy
```

Si te da error de "pip no encontrado", instala pip primero:

```
sudo apt update
sudo apt install python3-pip -y
```

### Paso 2. Ejecutar la app

Ve a la carpeta del proyecto (donde está `main.py`) y escribe:

```
python3 main.py
```

Se abrirá una ventana con tu app de notas. 🎉
Escribe una nota, pulsa **Agregar**, y ciérrala. Al volver a abrirla,
tus notas siguen ahí.

---

## PARTE 2 — Convertirla en app de Android (.apk)

Esto crea el archivo que instalas en la tablet. La **primera vez tarda**
(descarga muchas cosas), ten paciencia.

### Paso 1. Instalar las herramientas del sistema

```
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake \
    libffi-dev libssl-dev build-essential
```

### Paso 2. Instalar Buildozer

```
pip install --user buildozer cython
```

### Paso 3. Crear el archivo de configuración

Dentro de la carpeta del proyecto:

```
buildozer init
```

Esto crea un archivo llamado `buildozer.spec`. (Ya te dejé uno preparado en
el proyecto, así que si ya existe, puedes saltarte este paso.)

### Paso 4. Construir el .apk

```
buildozer -v android debug
```

⏳ La primera vez puede tardar **30-60 minutos** y descargar varios GB.
Cuando termine, el archivo `.apk` aparece en la carpeta `bin/`.

---

## PARTE 3 — Instalar la app en la tablet Samsung

1. Conecta la tablet al computador con el cable USB.
2. En la tablet, activa el **modo desarrollador**:
   - Ajustes → *Información del teléfono* → *Información de software*
   - Toca **7 veces** sobre "Número de compilación".
   - Vuelve a Ajustes → *Opciones de desarrollador* → activa **Depuración USB**.
3. En el computador, con la tablet conectada, escribe:

   ```
   buildozer android deploy run
   ```

   ¡La app se instala y se abre sola en tu tablet! 🎉

> **Alternativa fácil:** copia el archivo `.apk` de la carpeta `bin/` a la
> tablet (por USB o WhatsApp), tócalo desde la tablet para instalarlo, y
> acepta "instalar de fuentes desconocidas" si te lo pide.

---

## ¿Algo no funcionó?

Cuéntame en qué paso te quedaste y qué mensaje te salió (una foto o el texto
del error), y te ayudo a resolverlo. 💪
