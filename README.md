# Reflexión y transmisión de ondas electromagnéticas

Este proyecto simula cómo una onda electromagnética se refleja y se transmite al pasar de un medio a otro. Las gráficas permiten observar qué ocurre al cambiar los índices de refracción.

## Cómo ejecutar el proyecto

Se necesita tener instalado Python 3.9 o superior.

Abre una terminal en la carpeta del proyecto e instala las librerías necesarias:

```bash
python -m pip install -r requirements.txt
```

Luego ejecuta el programa:

```bash
python reflexion_transmision.py
```

Se abrirá una ventana con la simulación. Puedes cambiar los índices de refracción con los deslizadores, pausar la animación y reiniciar el tiempo.

## Guardar las gráficas

Para guardar las gráficas como imágenes, ejecuta:

```bash
python reflexion_transmision.py --guardar-figuras
```

Las imágenes se guardan en la carpeta `resultados`, que se crea automáticamente.
