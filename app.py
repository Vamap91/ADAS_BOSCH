import streamlit as st
import pandas as pd

st.title("🔧 Sistema ADAS - Teste Básico")
st.write("**Versão de teste funcionando!**")

# Dados simples para teste
data = {
    'FIPE': [92983, 95432, 87621],
    'Marca': ['BMW', 'VW', 'Mercedes'],
    'Modelo': ['118i', 'Polo', 'A200'],
    'ADAS': ['Sim', 'Sim', 'Sim']
}

df = pd.DataFrame(data)
st.dataframe(df)

st.success("✅ Se você vê isso, o app está funcionando!")
