import streamlit as st
import pandas as pd

st.title("🔧 Sistema ADAS - Teste")
st.write("Se você está vendo isso, o app está funcionando!")

# Dados de teste
data = {
    'Marca': ['BMW', 'VW', 'Mercedes'],
    'Modelo': ['118i', 'Polo', 'A200'],
    'ADAS': ['Sim', 'Sim', 'Sim']
}

df = pd.DataFrame(data)
st.dataframe(df)
