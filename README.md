# NoSQL_Test

![Python](https://img.shields.io/badge/python-3.13+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136.1-orange?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)

API REST para gestao de dados NoSQL com suporte a relacoes entre entidades e armazenamento em disco. Ideal para prototipagem e projetos educacionais.

---

## Caracteristicas

| Caracteristica | Descricao |
|----------------|-----------|
| **Armazenamento** | Persistencia em disco via `diskcache` |
| **Relacionamentos** | Resolucao recursiva de entidades relacionadas |
| **Validacao** | Validador de esquemas com tipos (str, int, relacoes) |
| **UUID** | Identificadores unicos version 4 |
| **API REST** | Full CRUD via FastAPI |
| **Filtragem** | Query por campo e valor |

---

## instalacao

```bash
# Clone o repositorio
git clone <repo-url>
cd NoSQL_Test

# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Instale as dependencias
pip install -r requirements.txt
# ou via uv:
uv sync
```

---

## usage

```bash
# Inicie o servidor
python main.py
# ou
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

A API estara disponivel em `http://localhost:8000`

### Documentacao Interativa

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Endpoints

### Colecoes Disponiveis

| Colecao | Descricao |
|--------|-----------|
| `Alunos` | Registro de alunos (nome: str, idade: int) |
| `Professores` | Registro de professores (nome: str, idade: int) |
| `Turmas` | Turmas com relacao a professores e alunos |

### Operacoes CRUD

| Metodo | Endpoint | Descricao |
|-------|----------|-----------|
| `GET` | `/{collection}` | Lista todos os registros |
| `GET` | `/{collection}/{uid}` | Obtem registro especifico |
| `GET` | `/{collection}/filter?campo=X&valor=Y` | Filtra registros |
| `POST` | `/{collection}` | Cria novo registro |
| `PATCH` | `/{collection}/{uid}` | Atualiza registro |
| `PUT` | `/{collection}/{uid}` | Substitui registro |
| `DELETE` | `/{collection}/{uid}` | Remove registro |

### Exemplos de Uso

#### Criar Aluno

```bash
curl -X POST "http://localhost:8000/Alunos" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Joao Silva", "idade": 15}'
```

Resposta:
```json
{"status": "sucesso", "id": "550e8400-e29b-41d4-a716-446655440000"}
```

#### Listar Alunos

```bash
curl "http://localhost:8000/Alunos"
```

#### Filtrar por Campo

```bash
curl "http://localhost:8000/Alunos/filter?campo=nome&valor=Joao"
```

#### Criar Turma com Relacionamentos

```bash
curl -X POST "http://localhost:8000/Turmas" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "3 Serie A",
    "Professores": ["<uuid-professor>"],
    "Alunos": ["<uuid-aluno1>", "<uuid-aluno2>"]
  }'
```

---

## Estrutura do Projeto

```
NoSQL_Test/
├── main.py          # FastAPI app & endpoints
├── conn.py        # Collection & Query classes
├── schemas.py      # Definicao de schemas
├── admin.py       # Interface admin (futuro)
├── templates/
│   └── admin_generico.html
├── pyproject.toml
└── README.md
```

---

## Schema

O sistema utiliza um esquema definindo campos e seus tipos:

```python
schemas = {
    "Alunos": {"nome": "str", "idade": "int"},
    "Professores": {"nome": "str", "idade": "int"},
    "Turmas": {"nome": "str", "Professores": "Professores", "Alunos": "Alunos"},
}
```

### Tipos Suportados

| Tipo | Descricao |
|------|-----------|
| `str` | Texto |
| `int` | Inteiro |
| `{Collection}` | Referencia para outra colecao |

---

## Health Check

```bash
curl "http://localhost:8000/health"
```

---

## License

MIT License - sinta-se livre para usar e modificar.