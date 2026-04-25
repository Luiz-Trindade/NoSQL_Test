from fastapi import FastAPI, HTTPException, Request
from conn import Collection, ValidationError
from schemas import schemas
import uvicorn
import uuid
from typing import Dict, Any, Optional

app = FastAPI(
    title="SISTEMA DE GESTÃO NO-SQL (Escola)",
    version="2.0.0",
    description="API para gestão de dados escolares com relações e recursividade.",
)

db = Collection("meu_banco_cache", schemas)


def validate_uuid(uid: str) -> bool:
    return uuid.UUID(uid, version=4) is not None


def parse_uuid_param(uid: str) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(uid, version=4)
    except (ValueError, TypeError):
        return None


@app.get("/")
async def root():
    return {
        "status": "online",
        "banco": "diskcache",
        "colecoes": list(schemas.keys()),
        "version": "2.0.0",
    }


@app.get("/health")
async def health_check():
    try:
        db.get("Alunos")
        return {"status": "healthy", "cache": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@app.get("/inspect/schemas")
async def inspect_schemas():
    return schemas


@app.get("/{collection}")
async def list_all(collection: str):
    if collection not in schemas:
        raise HTTPException(
            status_code=404, detail=f"Coleção '{collection}' não encontrada"
        )

    res = db.get(collection)
    if not res:
        return {}
    return res.all()


@app.get("/{collection}/{uid}")
async def get_record(collection: str, uid: str):
    if collection not in schemas:
        raise HTTPException(
            status_code=404, detail=f"Coleção '{collection}' não encontrada"
        )

    if parse_uuid_param(uid) is None:
        raise HTTPException(
            status_code=400, detail="ID inválido. Deve ser um UUID válido."
        )

    res = db.get(collection)
    if not res:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    all_records = res.all()
    if uid in all_records:
        return all_records[uid]
    raise HTTPException(status_code=404, detail="Registro não encontrado")


@app.get("/{collection}/filter")
async def filter_records(collection: str, campo: str, valor: str):
    if collection not in schemas:
        raise HTTPException(
            status_code=404, detail=f"Coleção '{collection}' não encontrada"
        )

    try:
        res = db.get(collection)
        if not res:
            raise HTTPException(status_code=404, detail="Coleção não encontrada")

        results = res.where(campo).is_val(valor)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


@app.post("/{collection}")
async def create_record(collection: str, request: Request):
    if collection not in schemas:
        raise HTTPException(
            status_code=404, detail=f"Coleção '{collection}' não cadastrada no schema"
        )

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400, detail="Corpo da requisição deve ser JSON válido"
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400, detail="Corpo da requisição deve ser um objeto JSON"
        )

    valid, error = db.validate_data(collection, data)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    success, result = db.create(collection, data)

    if not success:
        raise HTTPException(status_code=400, detail=result)

    return {"status": "sucesso", "id": result}


@app.patch("/{collection}/{uid}")
async def update_record(collection: str, uid: str, request: Request):
    if collection not in schemas:
        raise HTTPException(
            status_code=404, detail=f"Coleção '{collection}' não cadastrada no schema"
        )

    if parse_uuid_param(uid) is None:
        raise HTTPException(
            status_code=400, detail="ID inválido. Deve ser um UUID válido."
        )

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400, detail="Corpo da requisição deve ser JSON válido"
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400, detail="Corpo da requisição deve ser um objeto JSON"
        )

    if not data:
        raise HTTPException(status_code=400, detail="Nenhum dado para atualizar")

    col_data = db.cache.get(collection, {})
    if uid not in col_data:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    success, msg = db.update(collection, uid, data)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"status": "sucesso", "mensagem": msg}


@app.put("/{collection}/{uid}")
async def replace_record(collection: str, uid: str, request: Request):
    if collection not in schemas:
        raise HTTPException(
            status_code=404, detail=f"Coleção '{collection}' não cadastrada no schema"
        )

    if parse_uuid_param(uid) is None:
        raise HTTPException(
            status_code=400, detail="ID inválido. Deve ser um UUID válido."
        )

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400, detail="Corpo da requisição deve ser JSON válido"
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400, detail="Corpo da requisição deve ser um objeto JSON"
        )

    col_data = db.cache.get(collection, {})
    if uid not in col_data:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    new_uuid = db.generate_uuid()
    col_data[new_uuid] = data
    db.cache[collection] = col_data

    return {"status": "sucesso", "id": new_uuid}


@app.delete("/{collection}/{uid}")
async def delete_record(collection: str, uid: str):
    if collection not in schemas:
        raise HTTPException(
            status_code=404, detail=f"Coleção '{collection}' não cadastrada no schema"
        )

    if parse_uuid_param(uid) is None:
        raise HTTPException(
            status_code=400, detail="ID inválido. Deve ser um UUID válido."
        )

    success, msg = db.delete(collection, uid)
    if not success:
        raise HTTPException(status_code=404, detail=msg)
    return {"status": "removido", "mensagem": msg}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
