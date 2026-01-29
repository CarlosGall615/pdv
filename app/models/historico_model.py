import json
import os
from datetime import datetime, timedelta

class HistoricoModel:

    def __init__(self):

        self.arquivo = "historico_pesagens.json"



    def ler_todos(self):
        
        if not os.path.exists(self.arquivo):
            return []
        try:
            with open(self.arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []



    def salvar_registro(self, dados):
        
        agora = datetime.now()

        # 1. Prepara o dado exatamente como o Dashboard espera
        nova_entrada = {
            "data": agora.strftime("%Y-%m-%d"),
            "hora": agora.strftime("%H:%M:%S"),
            "peso": float(dados['peso']),
            "total": float(dados['total'])
        }

        # 2. Tenta ler o arquivo usando o caminho definido no seu Model
        registros = []
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding="utf-8") as f:
                    registros = json.load(f)
            except:
                registros = []

        # 3. Adiciona a nova entrada e grava
        registros.append(nova_entrada)
        
        with open(self.arquivo, 'w', encoding="utf-8") as f:
            json.dump(registros, f, indent=4)



    def obter_dados_filtrados(self, periodo="Dia"):
        
        """Filtra os dados com base no período selecionado."""
        todos_dados = self.ler_todos()
        hoje = datetime.now()
        filtrados = []

        for item in todos_dados:
            try:
                # Converte a string de data do JSON para objeto datetime
                data_item = datetime.strptime(item['data'], "%Y-%m-%d")
                
                if periodo == "Dia":
                    if data_item.date() == hoje.date():
                        filtrados.append(item)
                elif periodo == "Semana":
                    if data_item > hoje - timedelta(days=7):
                        filtrados.append(item)
                elif periodo == "Mês":
                    if data_item > hoje - timedelta(days=30):
                        filtrados.append(item)
            except Exception as e:
                print(f"Erro ao processar item do histórico: {e}")
                continue
        
        return filtrados