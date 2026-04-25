import streamlit as st
import requests
import json
from typing import Dict, Any, List, Optional

# Configuração da Página
st.set_page_config(page_title="NPJ Admin Central", layout="wide")

# Endpoint da sua API FastAPI
API_URL = "http://localhost:8000"

# === Utilidades ===


def validate_uuid(uuid_str: str) -> bool:
    """Valida se uma string é um UUID válido."""
    if not uuid_str:
        return False
    try:
        parts = uuid_str.split("-")
        if len(parts) != 5:
            return False
        return all(len(p) in (8, 4, 4, 4, 12) for p in parts)
    except Exception:
        return False


def parse_uuid_list(uuid_str: str) -> List[str]:
    """Parse string de UUIDs (separados por vírgula) para lista."""
    if not uuid_str:
        return []
    return [uid.strip() for uid in uuid_str.split(",") if uid.strip()]


def fetch_schemas() -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{API_URL}/inspect/schemas", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Não foi possível conectar à API. Verifique se o servidor está rodando."
        )
        return None
    except requests.exceptions.Timeout:
        st.error("_TIMEOUT_ ao conectar à API.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Erro HTTP {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")
        return None


def fetch_collection(collection: str) -> Dict[str, Any]:
    try:
        response = requests.get(f"{API_URL}/{collection}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao buscar {collection}: {e}")
        return {}


def create_record(collection: str, data: Dict[str, Any]) -> bool:
    try:
        response = requests.post(f"{API_URL}/{collection}", json=data, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        st.error(f"Erro ao criar registro: {e}")
        return False


def update_record(collection: str, uid: str, data: Dict[str, Any]) -> bool:
    try:
        response = requests.patch(
            f"{API_URL}/{collection}/{uid}", json=data, timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False


def delete_record(collection: str, uid: str) -> bool:
    try:
        response = requests.delete(f"{API_URL}/{collection}/{uid}", timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar: {e}")
        return False


st.sidebar.title("NPJ - Gestão")
st.sidebar.info("the Boring Stack Engine")

schemas = fetch_schemas()
if schemas is None:
    st.stop()

if "detail" in schemas and len(schemas) == 1:
    st.error("⚠️ A API retornou um erro em vez dos schemas.")
    st.stop()

collections = list(schemas.keys())
if not collections:
    st.error("⚠️ Nenhuma coleção definida no schema.")
    st.stop()

escolha = st.sidebar.radio("Selecione uma Coleção:", collections)

if not escolha:
    st.stop()

st.header(f"📂 Gerenciando: {escolha}")

col_search, col_refresh = st.columns([3, 1])
with col_search:
    search_query = st.text_input("🔍 Buscar registros:", key=f"search_{escolha}")
with col_refresh:
    if st.button("🔄 Atualizar"):
        st.rerun()

st.subheader("📜 Registros")
records = fetch_collection(escolha)

if search_query:
    filtered = {}
    search_lower = search_query.lower()
    for uid, record in records.items():
        for value in record.values():
            if isinstance(value, str) and search_lower in value.lower():
                filtered[uid] = record
                break
            # Busca em listas
            if isinstance(value, list):
                if any(search_lower in str(v).lower() for v in value):
                    filtered[uid] = record
                    break
    records = filtered

if records:
    table_data = []
    for uid, record in records.items():
        row = {"id": uid}
        for campo, valor in record.items():
            if isinstance(valor, dict):
                row[campo] = ", ".join(str(v) for v in valor.keys())
            elif isinstance(valor, list):
                row[campo] = ", ".join(str(v) for v in valor)
            else:
                row[campo] = valor
        table_data.append(row)

    if table_data:
        st.dataframe(table_data, use_container_width=True, hide_index=True)
        st.caption(f"💡 {len(table_data)} registro(s) encontrado(s)")
    else:
        st.warning("ℹ️ Nenhum registro encontrado.")
else:
    st.warning("ℹ️ Nenhum registro encontrado.")

st.divider()
st.subheader("➕ Adicionar Novo")

with st.expander(f"📝 Preencha os dados para {escolha}", expanded=True):
    form_data = {}
    fields = schemas[escolha]

    all_valid = True

    for campo, tipo in fields.items():
        is_required = True
        required_marker = " *" if is_required else ""
        label = f"{campo}{required_marker}"
        help_text = f"Tipo: {tipo}"

        if tipo in schemas:
            uuid_input = st.text_input(
                label,
                key=f"input_{escolha}_{campo}",
                help=help_text,
                placeholder="UUIDs separados por vírgula (ex: uuid1, uuid2)",
            )
            parsed_uuids = parse_uuid_list(uuid_input)
            if is_required and not parsed_uuids:
                all_valid = False
                st.error(f"Campo obrigatório: {campo}")
            form_data[campo] = parsed_uuids
            if parsed_uuids and not all(validate_uuid(u) for u in parsed_uuids):
                st.warning(f"⚠️ Alguns UUIDs em {campo} são inválidos")
        elif tipo == "int":
            value = st.number_input(
                label, step=1, key=f"input_{escolha}_{campo}", help=help_text
            )
            if is_required and value == 0:
                all_valid = False
                st.error(f"Campo obrigatório: {campo}")
            form_data[campo] = int(value)
        elif tipo == "str":
            value = st.text_input(label, key=f"input_{escolha}_{campo}", help=help_text)
            if is_required and not value.strip():
                all_valid = False
                st.error(f"Campo obrigatório: {campo}")
            form_data[campo] = value.strip()
        else:
            value = st.text_input(label, key=f"input_{escolha}_{campo}", help=help_text)
            form_data[campo] = value

    st.caption("* Campos obrigatórios")

    if st.button(f"💾 Salvar em {escolha}", disabled=not all_valid):
        if not all_valid:
            st.error("⚠️ Preencha todos os campos obrigatórios.")
        else:
            with st.spinner("Criando registro..."):
                if create_record(escolha, form_data):
                    st.success("✅ Registro criado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Falha ao criar registro.")

st.divider()
st.subheader("✏️ Editar Registro Existente")

if records:
    uid_list = list(records.keys())
    selected_uid = st.selectbox(
        "Selecione o registro para editar:", uid_list, key=f"edit_select_{escolha}"
    )

    if selected_uid:
        current_data = records.get(selected_uid, {})
        st.write("📝 Dados atuais:")
        st.json(current_data)

        st.write("✏️ Novos dados (mescla com dados atuais):")
        update_data = {}
        for campo in current_data.keys():
            valor = current_data[campo]
            if isinstance(valor, dict):
                uid_str = ", ".join(str(v) for v in valor.keys())
                new_val = st.text_input(
                    f"{campo} (relação)",
                    value=uid_str,
                    key=f"update_{escolha}_{campo}",
                )
                update_data[campo] = parse_uuid_list(new_val)
            elif isinstance(valor, list):
                val_str = ", ".join(str(v) for v in valor)
                new_val = st.text_input(
                    f"{campo} (lista)",
                    value=val_str,
                    key=f"update_{escolha}_{campo}",
                )
                update_data[campo] = (
                    [type(valor[0])(v.strip()) for v in new_val.split(",") if v.strip()]
                    if valor
                    else []
                )
            elif isinstance(valor, int):
                update_data[campo] = st.number_input(
                    f"{campo}",
                    value=valor,
                    step=1,
                    key=f"update_{escolha}_{campo}",
                )
            else:
                update_data[campo] = st.text_input(
                    f"{campo}", value=str(valor), key=f"update_{escolha}_{campo}"
                )

        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("💾 Atualizar", key=f"update_btn_{escolha}"):
                with st.spinner("Atualizando..."):
                    if update_record(escolha, selected_uid, update_data):
                        st.success("✅ Registro atualizado!")
                        st.rerun()
        with c2:
            if st.button("❌ Deletar", key=f"delete_btn_{escolha}"):
                with st.spinner("Deletando..."):
                    if delete_record(escolha, selected_uid):
                        st.success("✅ Registro deletado!")
                        st.rerun()
    else:
        st.info("Nenhum registro disponível para editar.")

st.divider()
st.caption(
    f"**Admin Central** | API: {API_URL} | Coleções: {', '.join(collections)} | {len(records)} registros exibidos"
)
