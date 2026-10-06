# ====== Celda 1 ======
# Instalación de PuLP para Google Colab
# Ejecutar en una celda de Colab:
# !pip install "pulp==3.3.2"


# ====== Celda 2 ======
import pandas as pd
import pulp
from pulp import LpMaximize, LpProblem, LpStatus, LpVariable, lpSum, LpBinary


# ====== Celda 3 ======
# Datos del problema
canales_iniciales = pd.DataFrame({
    "Canal": ["TV", "Radio", "Redes sociales", "Prensa"],
    "Costo": [8, 3, 4, 2],
    "Impacto": [14, 5, 7, 3]
})

presupuesto_inicial = 9

canales_iniciales


# ====== Celda 4 ======
def resolver(canales, presupuesto):
    """Resuelve el problema binario de selección de medios."""
    if presupuesto < 0:
        raise ValueError("El presupuesto no puede ser negativo.")

    if canales.empty:
        raise ValueError("Debe existir al menos un canal publicitario.")

    nombres = canales["Canal"].astype(str).str.strip().tolist()
    if any(nombre == "" for nombre in nombres):
        raise ValueError("Todos los canales deben tener un nombre.")

    if len(set(nombres)) != len(nombres):
        raise ValueError("Los nombres de los canales deben ser únicos.")

    problema = LpProblem("Plan_de_medios", LpMaximize)

    # x[i] = 1 si se usa el canal i; x[i] = 0 en caso contrario.
    x = {
        i: LpVariable(f"x_{i}", cat=LpBinary)
        for i in canales.index
    }

    # Función objetivo: maximizar el impacto total.
    problema += lpSum(
        canales.loc[i, "Impacto"] * x[i]
        for i in canales.index
    ), "Impacto_total"

    # Restricción de presupuesto.
    problema += lpSum(
        canales.loc[i, "Costo"] * x[i]
        for i in canales.index
    ) <= presupuesto, "Presupuesto"

    problema.solve(pulp.PULP_CBC_CMD(msg=False))
    estado = LpStatus[problema.status]

    if estado != "Optimal":
        return {
            "estado": estado,
            "costo_total": None,
            "impacto_total": None,
            "presupuesto_restante": None,
            "resultado": pd.DataFrame()
        }

    seleccion = []
    for i in canales.index:
        valor = int(round(pulp.value(x[i])))
        seleccion.append({
            "Canal": canales.loc[i, "Canal"],
            "Costo": canales.loc[i, "Costo"],
            "Impacto": canales.loc[i, "Impacto"],
            "Variable": f"x_{i}",
            "Seleccionado": valor,
            "Costo usado": canales.loc[i, "Costo"] * valor,
            "Impacto obtenido": canales.loc[i, "Impacto"] * valor
        })

    resultado = pd.DataFrame(seleccion)
    costo_total = resultado["Costo usado"].sum()
    impacto_total = resultado["Impacto obtenido"].sum()

    return {
        "estado": estado,
        "costo_total": costo_total,
        "impacto_total": impacto_total,
        "presupuesto_restante": presupuesto - costo_total,
        "resultado": resultado
    }


# ====== Celda 5 ======
resultado_inicial = resolver(canales_iniciales, presupuesto_inicial)

print("Estado:", resultado_inicial["estado"])
print("Costo total:", resultado_inicial["costo_total"])
print("Impacto total:", resultado_inicial["impacto_total"])
print("Presupuesto restante:", resultado_inicial["presupuesto_restante"])


# ====== Celda 6 ======
resultado_inicial["resultado"]


# ====== Celda 7 ======
# Solo mostramos los canales seleccionados.
seleccionados = resultado_inicial["resultado"][
    resultado_inicial["resultado"]["Seleccionado"] == 1
]
seleccionados[["Canal", "Costo", "Impacto"]]
