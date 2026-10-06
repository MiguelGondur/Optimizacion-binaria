import pandas as pd
import streamlit as st
import pulp
from pulp import LpMaximize, LpProblem, LpStatus, LpVariable, lpSum, LpBinary


st.set_page_config(
    page_title="Plan de medios - PuLP",
    page_icon="📣",
    layout="wide"
)


DATOS_INICIALES = pd.DataFrame({
    "Canal": ["TV", "Radio", "Redes sociales", "Prensa"],
    "Costo": [8, 3, 4, 2],
    "Impacto": [14, 5, 7, 3]
})
PRESUPUESTO_INICIAL = 9


def resolver(canales: pd.DataFrame, presupuesto: float):
    """Resuelve el problema binario de selección de medios."""
    if presupuesto < 0:
        raise ValueError("El presupuesto no puede ser negativo.")

    if canales.empty:
        raise ValueError("Debe existir al menos un canal publicitario.")

    datos = canales.copy()
    datos["Canal"] = datos["Canal"].astype(str).str.strip()

    if datos["Canal"].eq("").any():
        raise ValueError("Todos los canales deben tener un nombre.")

    if datos["Canal"].duplicated().any():
        raise ValueError("Los nombres de los canales deben ser únicos.")

    for columna in ["Costo", "Impacto"]:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")
        if datos[columna].isna().any():
            raise ValueError(f"La columna '{columna}' solo debe contener números.")
        if (datos[columna] < 0).any():
            raise ValueError(f"La columna '{columna}' no puede contener valores negativos.")

    problema = LpProblem("Plan_de_medios", LpMaximize)

    x = {
        i: LpVariable(f"x_{pos}", cat=LpBinary)
        for pos, i in enumerate(datos.index)
    }

    problema += lpSum(
        datos.loc[i, "Impacto"] * x[i]
        for i in datos.index
    ), "Impacto_total"

    problema += lpSum(
        datos.loc[i, "Costo"] * x[i]
        for i in datos.index
    ) <= presupuesto, "Presupuesto"

    problema.solve(pulp.PULP_CBC_CMD(msg=False))
    estado = LpStatus[problema.status]

    resultado = datos.copy()
    resultado["Variable"] = [f"x_{pos}" for pos, _ in enumerate(datos.index)]

    if estado != "Optimal":
        return estado, None, None, None, resultado

    resultado["Seleccionado"] = [
        int(round(pulp.value(x[i]))) for i in datos.index
    ]
    resultado["Costo usado"] = resultado["Costo"] * resultado["Seleccionado"]
    resultado["Impacto obtenido"] = resultado["Impacto"] * resultado["Seleccionado"]

    costo_total = float(resultado["Costo usado"].sum())
    impacto_total = float(resultado["Impacto obtenido"].sum())
    presupuesto_restante = float(presupuesto - costo_total)

    return estado, costo_total, impacto_total, presupuesto_restante, resultado


st.title("📣 Plan de medios con presupuesto")
st.write(
    "Selecciona los canales publicitarios que se usarán este mes "
    "para maximizar el impacto sin superar el presupuesto disponible."
)

with st.expander("📐 Formulación matemática", expanded=True):
    st.markdown(
        "**Variable de decisión:**  "
        "xᵢ = 1 si se utiliza el canal i, xᵢ = 0 en caso contrario."
    )
    st.latex(
        r"\max Z = 14x_{TV}+5x_{Radio}+7x_{Redes}+3x_{Prensa}"
    )
    st.latex(
        r"8x_{TV}+3x_{Radio}+4x_{Redes}+2x_{Prensa}\leq 9"
    )
    st.latex(
        r"x_{TV},x_{Radio},x_{Redes},x_{Prensa}\in\{0,1\}"
    )

st.subheader("Datos del problema")

col1, col2 = st.columns([3, 1])
with col1:
    datos = st.data_editor(
        DATOS_INICIALES,
        hide_index=True,
        use_container_width=True,
        disabled=["Canal"],
        column_config={
            "Costo": st.column_config.NumberColumn(
                "Costo", min_value=0, step=1, format="%g"
            ),
            "Impacto": st.column_config.NumberColumn(
                "Impacto", min_value=0, step=1, format="%g"
            )
        },
        key="datos_medios"
    )

with col2:
    presupuesto = st.number_input(
        "Presupuesto disponible",
        min_value=0.0,
        value=float(PRESUPUESTO_INICIAL),
        step=1.0
    )

    st.caption("Las variables de decisión son binarias: 0 = no usar, 1 = usar.")

    optimizar = st.button(
        "🚀 Optimizar distribución",
        type="primary",
        use_container_width=True
    )

if optimizar:
    try:
        estado, costo_total, impacto_total, presupuesto_restante, resultado = resolver(
            datos, presupuesto
        )

        st.divider()
        st.subheader("Resultado de la optimización")

        if estado == "Optimal":
            uso = (costo_total / presupuesto * 100) if presupuesto > 0 else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Estado", estado)
            m2.metric("Impacto máximo", f"{impacto_total:g}")
            m3.metric("Costo usado", f"{costo_total:g}")
            m4.metric("Presupuesto restante", f"{presupuesto_restante:g}")

            st.progress(min(uso / 100, 1.0), text=f"Uso del presupuesto: {uso:.1f}%")

            seleccionados = resultado[resultado["Seleccionado"] == 1]

            st.subheader("Canales seleccionados")
            if seleccionados.empty:
                st.info("No se seleccionó ningún canal con el presupuesto indicado.")
            else:
                st.dataframe(
                    seleccionados[
                        ["Canal", "Costo", "Impacto", "Variable", "Seleccionado"]
                    ],
                    hide_index=True,
                    use_container_width=True
                )

            st.subheader("Detalle de todas las alternativas")
            st.dataframe(
                resultado[
                    [
                        "Canal", "Costo", "Impacto", "Variable",
                        "Seleccionado", "Costo usado", "Impacto obtenido"
                    ]
                ],
                hide_index=True,
                use_container_width=True
            )

            st.success(
                f"La solución óptima utiliza {len(seleccionados)} canal(es), "
                f"gasta {costo_total:g} del presupuesto y obtiene un impacto total de {impacto_total:g}."
            )
        else:
            st.error(f"El modelo terminó con el estado: {estado}")

    except ValueError as error:
        st.error(str(error))
    except Exception as error:
        st.exception(error)

st.divider()
st.caption("Modelo de programación lineal entera binaria resuelto con PuLP.")
