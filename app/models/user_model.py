import json
import os

class UserModel():

    def __init__(self):
        
        self.arquivo = "usuarios.json"

        if not os.path.exists(self.arquivo):
            with open(self.arquivo, 'w') as f:
                json.dump([], f)

        self.usuario_mestre = "admin"
        self.senha_mestre = "123"

        self.usuario_cadastrados = []



    def carregar_todos(self):

        try:
            with open(self.arquivo, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        


    def cadastrar_usuario(self, nome, senha):

        usuarios = self.carregar_todos()

        for u in usuarios:
            if u['nome'] == nome:
                return False, "Usuário já cadastrado!"

        usuarios.append({"nome": nome, "senha": senha})
        
        with open(self.arquivo, 'w') as f:
            json.dump(usuarios, f, indent=4)
        return True, "Sucesso"
    


    def validar_login(self, usuario, senha):

        if usuario == self.usuario_mestre and senha == self.senha_mestre:
            return True
        
        usuarios = self.carregar_todos()
        for u in usuarios:
            if u['nome'] == usuario and u['senha'] == senha:
                return True
        return False
    


    def verificar_senha(self, nome_usuario, senha_tentada):
        # Aqui você faz o SELECT no banco de dados
        # Exemplo: SELECT senha FROM usuarios WHERE nome = nome_usuario
        # Se a senha do banco for igual a senha_tentada, retorna True
        
        # Exemplo simplificado para teste:
        usuario_no_banco = self.buscar_por_nome(nome_usuario)
        if usuario_no_banco and usuario_no_banco['senha'] == senha_tentada:
            return True
        return False