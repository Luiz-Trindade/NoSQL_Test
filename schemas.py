# Metadata structure
schemas = {
    "Alunos": {"nome": "str", "idade": "int"},
    "Professores": {"nome": "str", "idade": "int"},
    "Turmas": {"nome": "str", "Professores": "Professores", "Alunos": "Alunos"},
}
