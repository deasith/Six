# 📝 Mis Notas

Una app sencilla para anotar cosas, hecha con **Python**.

## ¿Qué hace?

- Crear notas nuevas
- Editar y borrar notas
- Guarda todo automáticamente (las notas no se pierden al cerrar)

## Cómo ejecutarla

1. Necesitas tener **Python 3** instalado. Para comprobarlo, abre una terminal
   (o CMD en Windows) y escribe:

   ```
   python3 --version
   ```

   Si no lo tienes, descárgalo gratis en https://www.python.org/downloads/
   (en Windows, marca la casilla **"Add Python to PATH"** al instalar).

2. Abre una terminal en la carpeta donde está el archivo y ejecuta:

   ```
   python3 notas.py
   ```

   En Windows también puedes hacer **doble clic** en `notas.py`.

## Cómo usarla

- **Nueva**: crea una nota.
- **Editar**: cambia la nota seleccionada (o haz doble clic sobre ella).
- **Borrar**: elimina la nota seleccionada.

Las notas se guardan en el archivo `notas.json`, que se crea solo la primera
vez que añades una nota.

## Nota técnica

Usa **Tkinter**, que viene incluido con Python, así que no hay que instalar
nada más. 🎉
