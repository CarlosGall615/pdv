import json
import os

class ConfigModel:

    def __init__(self):

        self.arquivo_config = "config.json"
        self.config_padrao = {
            "porta_balanca": "COM1",
            "baudrate_balanca": 9600,
            "porta_impressora": "COM2",
            "baudrate_impressora": 115200
        }
        self.carregar_config()



    def carregar_config(self):

        if not os.path.exists(self.arquivo_config):
            self.salvar_config(self.config_padrao)
            return self.config_padrao
        
        with open(self.arquivo_config, 'r') as f:
            return json.load(f)



    def salvar_config(self, novos_dados):

        with open(self.arquivo_config, 'w') as f:
            json.dump(novos_dados, f, indent=4)


            