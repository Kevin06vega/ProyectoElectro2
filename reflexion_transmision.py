import sys as sistema
from pathlib import Path as Ruta

import numpy
import matplotlib.pyplot
import matplotlib.animation
import matplotlib.widgets

"Constantes a utilizar"
velocidad_luz = 299792458.0
permeabilidad_vacio = 4.0 * numpy.pi * 1e-7
frecuencia = 100e6
amplitud = 1.0
longitud_onda_vacio = velocidad_luz / frecuencia
periodo = 1.0 / frecuencia


def calcular_coeficientes(indice_uno, indice_dos):
    """Calcula qué parte de la onda se refleja y qué parte pasa al otro medio.
    r y t corresponden al campo eléctrico, mientras que R y T son de potencia.
    """
    if indice_uno <= 0 or indice_dos <= 0:
        raise ValueError("Los índices de refracción deben ser positivos.")
    # El signo de r indica si el campo reflejado invierte su fase.
    reflexion = (indice_uno - indice_dos) / (indice_uno + indice_dos)
    transmision = 2.0 * indice_uno / (indice_uno + indice_dos)
    reflectancia = reflexion ** 2
    transmitancia = (indice_dos / indice_uno) * transmision ** 2
    return {"reflexion": reflexion, "transmision": transmision,
            "reflectancia": reflectancia, "transmitancia": transmitancia}


def evaluar_campos(posicion, tiempo, indice_uno, indice_dos,
                   amplitud_campo=amplitud, frecuencia_onda=frecuencia):
    """Calcula los campos eléctrico y magnético en la posición y el tiempo dados.

    Devuelve los valores de las tres ondas para luego dibujarlas en cada medio.
    """
    coeficientes = calcular_coeficientes(indice_uno, indice_dos)
    frecuencia_angular = 2.0 * numpy.pi * frecuencia_onda
    numero_onda_uno = indice_uno * frecuencia_angular / velocidad_luz
    numero_onda_dos = indice_dos * frecuencia_angular / velocidad_luz
    incidente = amplitud_campo * numpy.cos(
        numero_onda_uno * posicion - frecuencia_angular * tiempo)
    reflejada = coeficientes["reflexion"] * amplitud_campo * numpy.cos(
        numero_onda_uno * posicion + frecuencia_angular * tiempo)
    transmitida = coeficientes["transmision"] * amplitud_campo * numpy.cos(
        numero_onda_dos * posicion - frecuencia_angular * tiempo)
    # E apunta en y. El signo de B_x cambia con el sentido de propagación.
    return {"incidente": incidente, "reflejada": reflejada,
            "transmitida": transmitida,
            "magnetico_incidente": -indice_uno * incidente / velocidad_luz,
            "magnetico_reflejada": indice_uno * reflejada / velocidad_luz,
            "magnetico_transmitida": -indice_dos * transmitida / velocidad_luz}


def calcular_balance(indice_uno, indice_dos, tiempo=0.0):
    """Calcula el flujo promedio de energía de cada onda.

    También revisa que R + T sea 1 y que los campos coincidan en la interfaz.
    """
    coeficientes = calcular_coeficientes(indice_uno, indice_dos)
    flujo_incidente = indice_uno * amplitud ** 2 / (
        2.0 * permeabilidad_vacio * velocidad_luz)
    # El flujo reflejado es negativo porque la energía regresa hacia el primer medio.
    flujo_reflejado = -coeficientes["reflectancia"] * flujo_incidente
    flujo_transmitido = coeficientes["transmitancia"] * flujo_incidente
    campos = evaluar_campos(0.0, tiempo, indice_uno, indice_dos)
    error_electrico = abs(campos["incidente"] + campos["reflejada"]
                          - campos["transmitida"]) / amplitud
    error_magnetico = velocidad_luz * abs(campos["magnetico_incidente"]
        + campos["magnetico_reflejada"] - campos["magnetico_transmitida"]) / amplitud
    return {"flujo_incidente": flujo_incidente, "flujo_reflejado": flujo_reflejado,
            "flujo_transmitido": flujo_transmitido,
            "error_energia": abs(coeficientes["reflectancia"]
                                + coeficientes["transmitancia"] - 1.0),
            "error_electrico": error_electrico, "error_magnetico": error_magnetico}


def crear_visualizacion(indice_uno=1.0, indice_dos=1.5, ciclos=0.0,
                       interactiva=True):
    """Prepara las gráficas de los campos y las barras de potencia.

    Devuelve la figura, los valores actuales y la función que actualiza todo.
    Si es interactiva, también agrega los deslizadores y botones.
    """
    posiciones = numpy.linspace(-2.5, 2.5, 1201)
    # Cada onda se dibuja solo en el medio que le corresponde; z = 0 es la interfaz.
    izquierda = posiciones <= 0.0
    derecha = posiciones >= 0.0
    estado = {"indice_uno": indice_uno, "indice_dos": indice_dos,
              "ciclos": ciclos, "pausado": False}
    figura = matplotlib.pyplot.figure(figsize=(11.5, 8.8))
    figura.suptitle("Reflexión y transmisión en una interfaz", fontsize=16)
    figura.subplots_adjust(bottom=0.21 if interactiva else 0.08,
                           top=0.90, left=0.09, right=0.97)
    rejilla = figura.add_gridspec(3, 2, height_ratios=[2.0, 2.0, 1.6],
                                hspace=0.58, wspace=0.40)
    eje_electrico = figura.add_subplot(rejilla[0, :])
    eje_magnetico = figura.add_subplot(rejilla[1, :])
    eje_potencia = figura.add_subplot(rejilla[2, 0])
    eje_datos = figura.add_subplot(rejilla[2, 1])
    colores = ["#168383", "#d27b24", "#7254a3", "#555555"]
    etiquetas = ["Incidente (+z)", "Reflejada (−z)", "Transmitida (+z)",
                 "Total en medio 1"]
    lineas_electricas, lineas_magneticas = [], []
    for eje, lineas in [(eje_electrico, lineas_electricas),
                        (eje_magnetico, lineas_magneticas)]:
        eje.axvspan(-2.5, 0, color="#e8f3f3", alpha=0.45)
        eje.axvspan(0, 2.5, color="#eee8f5", alpha=0.45)
        eje.axvline(0, color="black", linewidth=1.0)
        eje.set_xlim(-2.5, 2.5)
        eje.set_xlabel("Posición z / λ₀")
        eje.grid(alpha=0.2)
        for numero, (color, etiqueta) in enumerate(zip(colores, etiquetas)):
            linea, = eje.plot([], [], color=color, label=etiqueta,
                              linewidth=1.0 if numero == 3 else 1.8,
                              linestyle="--" if numero == 3 else "-")
            lineas.append(linea)
    eje_electrico.set_ylabel("Eᵧ / E₀")
    eje_electrico.set_ylim(-2.1, 2.1)
    eje_electrico.legend(loc="upper right", ncol=4, fontsize=8)
    eje_magnetico.set_ylabel("c Bₓ / E₀")
    eje_magnetico.set_title("Campo magnético (escala c Bₓ / E₀)", fontsize=10)
    barras = eje_potencia.bar(["R", "T"], [0, 0], color=colores[1:3], width=0.5)
    eje_potencia.set_ylim(0, 1.15)
    eje_potencia.set_ylabel("Fracción de potencia")
    eje_potencia.grid(axis="y", alpha=0.2)
    valores_barras = [eje_potencia.text(numero, 0, "", ha="center", fontsize=10)
                      for numero in range(2)]
    eje_datos.axis("off")
    texto_datos = eje_datos.text(0, 1, "", va="top", fontsize=9.4,
                                linespacing=1.4)

    def actualizar():
        """Recalcula los campos y actualiza las gráficas con los valores actuales."""
        indice_actual_uno = estado["indice_uno"]
        indice_actual_dos = estado["indice_dos"]
        tiempo = estado["ciclos"] * periodo
        coeficientes = calcular_coeficientes(indice_actual_uno, indice_actual_dos)
        campos = evaluar_campos(posiciones * longitud_onda_vacio, tiempo,
                                indice_actual_uno, indice_actual_dos)
        electricos = [campos["incidente"], campos["reflejada"],
                      campos["transmitida"], campos["incidente"] + campos["reflejada"]]
        magneticos = [campos["magnetico_incidente"], campos["magnetico_reflejada"],
                      campos["magnetico_transmitida"],
                      campos["magnetico_incidente"] + campos["magnetico_reflejada"]]
        for numero in range(4):
            dominio = derecha if numero == 2 else izquierda
            lineas_electricas[numero].set_data(posiciones[dominio],
                                              electricos[numero][dominio] / amplitud)
            lineas_magneticas[numero].set_data(posiciones[dominio],
                velocidad_luz * magneticos[numero][dominio] / amplitud)
        limite_magnetico = max(1.5, 1.15 * indice_actual_uno
                              * (1.0 + abs(coeficientes["reflexion"])))
        eje_magnetico.set_ylim(-limite_magnetico, limite_magnetico)
        eje_electrico.set_title(
            f"Campo eléctrico: n₁ = {indice_actual_uno:.2f}, "
            f"n₂ = {indice_actual_dos:.2f}  |  t / período = {estado['ciclos']:.3f}",
            fontsize=10)
        for barra, texto, valor in zip(barras, valores_barras,
                [coeficientes["reflectancia"], coeficientes["transmitancia"]]):
            barra.set_height(valor)
            texto.set_position((barra.get_x() + barra.get_width() / 2, valor + 0.04))
            texto.set_text(f"{valor:.4f}")
        balance = calcular_balance(indice_actual_uno, indice_actual_dos, tiempo)
        suma = coeficientes["reflectancia"] + coeficientes["transmitancia"]
        eje_potencia.set_title(f"R + T = {suma:.12f}", fontsize=10)
        texto_datos.set_text(
            f"r = {coeficientes['reflexion']:.4f}    t = {coeficientes['transmision']:.4f}\n"
            f"⟨Sᵢ⟩ = {balance['flujo_incidente']:.4e} W/m²  (+z)\n"
            f"⟨Sᵣ⟩ = {balance['flujo_reflejado']:.4e} W/m²  (−z)\n"
            f"⟨Sₜ⟩ = {balance['flujo_transmitido']:.4e} W/m²  (+z)\n"
            f"|R + T − 1| = {balance['error_energia']:.2e}\n"
            f"Interfaz: |ΔE|/E₀ = {balance['error_electrico']:.2e}\n"
            f"               c|ΔB|/E₀ = {balance['error_magnetico']:.2e}")
        figura.canvas.draw_idle()

    if interactiva:
        eje_indice_uno = figura.add_axes([0.17, 0.115, 0.53, 0.025])
        eje_indice_dos = figura.add_axes([0.17, 0.065, 0.53, 0.025])
        deslizador_uno = matplotlib.widgets.Slider(eje_indice_uno, "Índice n₁", 1.0, 3.0,
                                    valinit=indice_uno, valstep=0.01)
        deslizador_dos = matplotlib.widgets.Slider(eje_indice_dos, "Índice n₂", 1.0, 3.0,
                                    valinit=indice_dos, valstep=0.01)
        boton_pausa = matplotlib.widgets.Button(figura.add_axes([0.77, 0.105, 0.16, 0.04]), "Pausar")
        boton_inicio = matplotlib.widgets.Button(figura.add_axes([0.77, 0.05, 0.16, 0.04]), "Reiniciar tiempo")

        def cambiar_indices(valor):
            """Lee los índices de los deslizadores y vuelve a dibujar las ondas."""
            estado["indice_uno"] = deslizador_uno.val
            estado["indice_dos"] = deslizador_dos.val
            actualizar()

        def cambiar_pausa(evento):
            """Pausa o reanuda la animación y cambia el texto del botón."""
            estado["pausado"] = not estado["pausado"]
            boton_pausa.label.set_text("Reanudar" if estado["pausado"] else "Pausar")
            figura.canvas.draw_idle()

        def reiniciar_tiempo(evento):
            """Pone el tiempo en cero y muestra otra vez el estado inicial de las ondas."""
            estado["ciclos"] = 0.0
            actualizar()

        deslizador_uno.on_changed(cambiar_indices)
        deslizador_dos.on_changed(cambiar_indices)
        boton_pausa.on_clicked(cambiar_pausa)
        boton_inicio.on_clicked(reiniciar_tiempo)
        # Guardamos los controles para que sigan respondiendo al usar la ventana.
        figura.controles = [deslizador_uno, deslizador_dos, boton_pausa, boton_inicio]
    figura.text(0.09, 0.015, "f = 100 MHz   |   E₀ = 1 V/m   |   μ₁ = μ₂ = μ₀   |   Interfaz en z = 0",
                fontsize=9)
    actualizar()
    return figura, estado, actualizar


def imprimir_ejemplos():
    """Muestra dos ejemplos en la terminal para comparar los cambios de medio."""
    for indice_uno, indice_dos in [(1.0, 1.5), (1.5, 1.0)]:
        coeficientes = calcular_coeficientes(indice_uno, indice_dos)
        balance = calcular_balance(indice_uno, indice_dos)
        print(f"\nn1 = {indice_uno}, n2 = {indice_dos}")
        print(f"r = {coeficientes['reflexion']:.6f}, t = {coeficientes['transmision']:.6f}")
        print(f"R = {coeficientes['reflectancia']:.6f}, T = {coeficientes['transmitancia']:.6f}")
        print("Poynting promedio (W/m2):", balance["flujo_incidente"],
              balance["flujo_reflejado"], balance["flujo_transmitido"])
        print(f"Error R+T: {balance['error_energia']:.3e}")
        print("Diferencias en frontera |E1-E2|/E0 y c|B1-B2|/E0:",
              balance["error_electrico"], balance["error_magnetico"])


def ejecutar():
    """Inicia la animación o guarda las figuras si se usa --guardar-figuras."""
    imprimir_ejemplos()
    if "--guardar-figuras" in sistema.argv:
        carpeta = Ruta(__file__).resolve().parent / "resultados"
        carpeta.mkdir(exist_ok=True)
        for indice_uno, indice_dos, nombre in [(1.0, 1.5, "indice_mayor"),
                                              (1.5, 1.0, "indice_menor")]:
            figura, estado, actualizar = crear_visualizacion(
                indice_uno, indice_dos, ciclos=0.125, interactiva=False)
            archivo = carpeta / f"{nombre}.png"
            figura.savefig(archivo, dpi=180)
            matplotlib.pyplot.close(figura)
            print(f"Figura guardada: {archivo}")
        return
    figura, estado, actualizar = crear_visualizacion()

    def avanzar(cuadro):
        """Hace avanzar el tiempo en cada cuadro mientras la animación esté activa."""
        if not estado["pausado"]:
            estado["ciclos"] += 0.025
            actualizar()

    animacion = matplotlib.animation.FuncAnimation(figura, avanzar, interval=35,
                                                   cache_frame_data=False)
    matplotlib.pyplot.show()
    return animacion


if __name__ == "__main__":
    ejecutar()
