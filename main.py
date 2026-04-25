from fastapi import FastAPI, HTTPException, Request
from conn import Collection
from schemas import schemas
import uvicorn

# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates

app = FastAPI(title="SISTEMA DE GESTÃO NO-SQL (Escola)")

# Instância global do banco
db = Collection("meu_banco_cache", schemas)

# templates = Jinja2Templates(directory="templates")

# @app.get("/admin/{collection}", response_class=HTMLResponse)
# async def admin_panel(request: Request, collection: str):
#     if collection not in schemas:
#         raise HTTPException(status_code=404, detail="Coleção não encontrada")

#     # Pega os dados e o schema
#     fields = schemas[collection]
#     res = db.get(collection)
#     data = res.all() if res else {}

#     # FORMA CORRETA:
#     return templates.TemplateResponse(
#         request=request,  # Passe o request como argumento nomeado
#         name="admin_generico.html",  # Evite acentos no nome do arquivo (boa prática)
#         context={
#             "collection": collection,
#             "fields": fields,
#             "data": data
#         }
#     )


@app.get("/")
async def root():
    return {"status": "online", "banco": "diskcache", "colecoes": list(schemas.keys())}


@app.get("/inspect/schemas")
async def inspect_schemas():
    return schemas


@app.get("/{collection}")
async def list_all(collection: str):
    """Retorna todos os registros com resolução recursiva."""
    res = db.get(collection)
    if not res:
        raise HTTPException(status_code=404, detail="Coleção não encontrada")
    return res.all()


@app.get("/{collection}/filter")
async def filter_records(collection: str, campo: str, valor: str):
    """Filtra registros: /{colecao}/filter?campo=nome&valor=Luiz"""
    res = db.get(collection)
    if not res:
        raise HTTPException(status_code=404, detail="Coleção não encontrada")
    return res.where(campo).is_val(valor)


@app.post("/{collection}")
async def create_record(collection: str, request: Request):
    """Cria um registro validando contra o schema."""
    if collection not in schemas:
        raise HTTPException(status_code=404, detail="Coleção não cadastrada no schema")

    data = await request.json()

    # Validação básica de tipos (conforme seu dicionário schemas)
    for campo, tipo in schemas[collection].items():
        if campo not in data:
            raise HTTPException(
                status_code=400, detail=f"Campo obrigatório ausente: {campo}"
            )

        # Se for uma relação, esperamos uma lista
        if tipo in schemas and not isinstance(data[campo], list):
            raise HTTPException(
                status_code=400, detail=f"O campo {campo} deve ser uma lista de UUIDs"
            )

    success, result = db.create(collection, data)

    if not success:
        raise HTTPException(status_code=500, detail=result)

    return {"status": "sucesso", "id": result}


@app.patch("/{collection}/{uid}")
async def update_record(collection: str, uid: str, request: Request):
    """Atualiza parcialmente um registro."""
    if collection not in schemas:
        raise HTTPException(status_code=404, detail="Coleção não cadastrada no schema")
    data = await request.json()
    success, msg = db.update(collection, uid, data)
    if not success:
        raise HTTPException(status_code=404, detail=msg)
    return {"status": "sucesso", "mensagem": msg}


@app.delete("/{collection}/{uid}")
async def delete_record(collection: str, uid: str):
    """Remove um registro e limpa referências."""
    success, msg = db.delete(collection, uid)
    if not success:
        raise HTTPException(status_code=404, detail=msg)
    return {"status": "removido", "mensagem": msg}


if __name__ == "__main__":
    # Rodar o servidor: python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
