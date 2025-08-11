import streamlit as st

st.write("# 🔧 Teste de Funcionamento")
st.write("Se você vê isso, o Streamlit está funcionando!")

if st.button("Teste"):
    st.success("✅ Botão funcionando!")

st.write("**Versão do Streamlit:**", st.__version__)
