import uuid
import diskcache
from typing import Dict, Any, List, Optional


class ValidationError(Exception):
    pass


class Query:
    def __init__(self, data, collection_name, full_cache, schemas):
        self.data = data
        self.collection_name = collection_name
        self.cache = full_cache
        self.schemas = schemas
        self.filter_field = None

    def _resolve_relations(self, record, current_col):
        resolved = record.copy()
        current_schema = self.schemas.get(current_col, {})

        for field, target_col in current_schema.items():
            if target_col not in self.schemas:
                continue
            if not isinstance(target_col, str):
                continue

            uids = resolved.get(field, [])
            if not isinstance(uids, list):
                uids = [uids] if uids else []

            target_collection_data = self.cache.get(target_col, {})
            resolved_dict = {}

            for uid in uids:
                if not isinstance(uid, str):
                    continue
                if uid in target_collection_data:
                    target_record = target_collection_data[uid]
                    resolved_dict[uid] = self._resolve_relations(
                        target_record, target_col
                    )

            resolved[field] = resolved_dict

        return resolved

    def where(self, field):
        self.filter_field = field
        return self

    def is_val(self, value):
        if not self.filter_field:
            raise ValueError("where() deve ser chamado antes de is_val()")

        results = {}
        filter_field = self.filter_field

        for uid, doc_data in self.data.items():
            if not isinstance(doc_data, dict):
                continue
            field_content = doc_data.get(filter_field)
            match = False

            if isinstance(field_content, list):
                if any(str(v) == str(value) for v in field_content):
                    match = True
            elif field_content is not None and str(field_content) == str(value):
                match = True

            if match:
                results[uid] = self._resolve_relations(doc_data, self.collection_name)

        return results

    def all(self):
        return {
            uid: self._resolve_relations(doc_data, self.collection_name)
            for uid, doc_data in self.data.items()
            if isinstance(doc_data, dict)
        }

    def filter(self, **kwargs):
        results = {}
        for uid, doc_data in self.data.items():
            if not isinstance(doc_data, dict):
                continue
            match = True
            for field, value in kwargs.items():
                if field not in doc_data:
                    match = False
                    break
                if str(doc_data[field]) != str(value):
                    match = False
                    break
            if match:
                results[uid] = self._resolve_relations(doc_data, self.collection_name)
        return results


class Collection:
    def __init__(self, cache_dir, schemas):
        self.cache = diskcache.Cache(cache_dir)
        self.schemas = schemas
        self._initialize_collections()

    def _initialize_collections(self):
        for name in self.schemas.keys():
            if name not in self.cache:
                self.cache[name] = {}

    def generate_uuid(self):
        return str(uuid.uuid4())

    def validate_data(self, collection, data):
        if collection not in self.schemas:
            return False, f"Coleção '{collection}' não encontrada no schema."

        schema_fields = self.schemas[collection]

        for field, expected_type in schema_fields.items():
            if field == "id":
                continue

            value = data.get(field)
            if value is None:
                return False, f"Campo obrigatório ausente: '{field}'"

            if expected_type == "int":
                if not isinstance(value, int):
                    return False, f"Campo '{field}' deve ser do tipo 'int'."

            elif expected_type == "str":
                if not isinstance(value, str):
                    return False, f"Campo '{field}' deve ser do tipo 'str'."

            elif expected_type in self.schemas:
                if not isinstance(value, list):
                    return (
                        False,
                        f"Campo '{field}' (relação) deve ser uma lista de UUIDs.",
                    )

        return True, None

    def create(self, collection, data):
        try:
            valid, error = self.validate_data(collection, data)
            if not valid:
                return False, error

            collection_data = self.cache.get(collection)
            if collection_data is None:
                collection_data = {}
                self.cache[collection] = collection_data

            new_uuid = self.generate_uuid()
            collection_data[new_uuid] = data
            self.cache[collection] = collection_data

            return True, new_uuid
        except Exception as e:
            return False, str(e)

    def update(self, collection, uid, data):
        try:
            if not uid or not isinstance(uid, str):
                return False, "ID inválido."

            col_data = self.cache.get(collection)
            if col_data is None or uid not in col_data:
                return False, "Registro não encontrado."

            col_data[uid].update(data)
            self.cache[collection] = col_data

            return True, "Registro atualizado com sucesso."
        except Exception as e:
            return False, str(e)

    def delete(self, collection, uid):
        try:
            if not uid or not isinstance(uid, str):
                return False, "ID inválido."

            col_data = self.cache.get(collection)
            if col_data is None or uid not in col_data:
                return False, "Registro não encontrado."

            col_data.pop(uid)
            self.cache[collection] = col_data

            for col_name, schema_col in self.schemas.items():
                for field, target_col in schema_col.items():
                    if target_col == collection:
                        other_col_data = self.cache.get(col_name)
                        if other_col_data:
                            for ref_uid, doc_data in list(other_col_data.items()):
                                current_refs = doc_data.get(field, [])
                                if (
                                    isinstance(current_refs, list)
                                    and uid in current_refs
                                ):
                                    current_refs.remove(uid)
                                other_col_data[ref_uid] = doc_data
                            self.cache[col_name] = other_col_data

            return True, "Registro removido com sucesso."
        except Exception as e:
            return False, str(e)

    def get(self, collection):
        if collection not in self.schemas:
            return None
        data = self.cache.get(collection)
        if data is None:
            return None
        return Query(data, collection, self.cache, self.schemas)

    def exists(self, collection, uid):
        col_data = self.cache.get(collection)
        if col_data is None:
            return False
        return uid in col_data

    def count(self, collection):
        col_data = self.cache.get(collection)
        return len(col_data) if col_data else 0
