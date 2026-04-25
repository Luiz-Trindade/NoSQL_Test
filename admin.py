import streamlit as st
import requests

# Configuração da Página
st.set_page_config(page_title="NPJ Admin Central", layout="wide")

# Endpoint da sua API FastAPI
API_URL = "http://localhost:8000"

st.sidebar.title("NPJ - Gestão")
st.sidebar.info("The Boring Stack Engine")

# 1. Busca os schemas disponíveis via API
# (Lembra daquela rota /inspect/schemas que sugeri? Ela é vital aqui)
try:
    response = requests.get(f"{API_URL}/inspect/schemas")
    if response.status_code == 200:
        schemas = response.json()
    else:
        st.error(f"Erro na API: {response.status_code}")
        st.stop()
except Exception as e:
    st.error(f"Não foi possível conectar: {e}")
    st.stop()

# Filtra para não pegar o campo 'detail' caso a API envie um erro
if "detail" in schemas and len(schemas) == 1:
    st.error("A API retornou um erro em vez dos schemas.")
    st.stop()

escolha = st.sidebar.radio("Selecione uma Coleção:", list(schemas.keys()))


if escolha:
    st.header(f"Gerenciando: {escolha}")

    # 3. Botões de Ação em colunas
    col1, col2 = st.columns([1, 4])

    # 4. Busca os dados da coleção selecionada
    res = requests.get(f"{API_URL}/{escolha}").json()

    if res:
        # Mostra a tabela (Streamlit lida com o JSON lindamente)
        st.table(res)  # Ou st.dataframe para ser interativo
    else:
        st.warning("Nenhum registro encontrado.")

    # 5. Formulário Dinâmico de Criação
    with st.expander(f"➕ Adicionar Novo em {escolha}"):
        novo_dado = {}
        fields = schemas[escolha]

        for campo, tipo in fields.items():
            if tipo in schemas:  # É uma relação
                novo_dado[campo] = st.text_input(
                    f"{campo} (UUIDs separados por vírgula)"
                )
                # Dica: Aqui você poderia buscar a lista da relação e fazer um st.multiselect
            elif tipo == "int":
                novo_dado[campo] = st.number_input(f"{campo}", step=1)
            else:
                novo_dado[campo] = st.text_input(f"{campo}")

        if st.button(f"Salvar em {escolha}"):
            post_res = requests.post(f"{API_URL}/{escolha}", json=novo_dado)
            if post_res.status_code == 200:
                st.success("Criado com sucesso!")
                st.rerun()
