import uuid
import diskcache


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
            if target_col in self.schemas:
                uids = resolved.get(field, [])
                target_collection_data = self.cache.get(target_col, {})

                resolved_dict = {}
                for uid in uids:
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
        results = {}
        for uid, doc_data in self.data.items():
            field_content = doc_data.get(self.filter_field)
            match = False
            if isinstance(field_content, list):
                if str(value) in [str(v) for v in field_content]:
                    match = True
            elif str(field_content) == str(value):
                match = True

            if match:
                results[uid] = self._resolve_relations(doc_data, self.collection_name)
        return results

    def all(self):
        return {
            uid: self._resolve_relations(doc_data, self.collection_name)
            for uid, doc_data in self.data.items()
        }


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

    def create(self, collection, data):
        try:
            collection_data = self.cache.get(collection)
            new_uuid = self.generate_uuid()
            collection_data[new_uuid] = data
            self.cache[collection] = collection_data
            return True, new_uuid
        except Exception as e:
            return False, str(e)

    def update(self, collection, uid, data):
        """
        Atualiza um registro existente.
        Realiza um 'partial update', mesclando os dados novos com os antigos.
        """
        try:
            col_data = self.cache.get(collection)

            # Verifica se a coleção existe e se o ID está lá
            if not col_data or uid not in col_data:
                return False, "Registro não encontrado."

            # O método .update() do Python mescla os dicionários.
            # Chaves existentes são sobrescritas, chaves novas (se houver) são adicionadas.
            col_data[uid].update(data)

            # Persiste a alteração no disco
            self.cache[collection] = col_data

            return True, "Registro atualizado com sucesso."
        except Exception as e:
            return False, str(e)

    def delete(self, collection, uid):
        try:
            col_data = self.cache.get(collection)
            if uid in col_data:
                col_data.pop(uid)
                self.cache[collection] = col_data

            for col_name in self.schemas.keys():
                schema_col = self.schemas.get(col_name, {})
                for field, target_col in schema_col.items():
                    if target_col == collection:
                        other_col_data = self.cache.get(col_name)
                        for _, doc_data in other_col_data.items():
                            current_refs = doc_data.get(field, [])
                            if uid in current_refs:
                                current_refs.remove(uid)
                        self.cache[col_name] = other_col_data
            return True, "Removed"
        except Exception as e:
            return False, str(e)

    def get(self, collection):
        data = self.cache.get(collection)
        if data is None:
            return None
        return Query(data, collection, self.cache, self.schemas)
