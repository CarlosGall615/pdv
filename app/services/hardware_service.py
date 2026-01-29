import threading
import time
import serial
from datetime import datetime

class HardwareService:

    def __init__(self, config, balanca_model, view_root, view_callback_status):

        self.config = config
        self.model = balanca_model
        self.view_root = view_root # Necessário para o loop de status sem travar
        self.status_callback = view_callback_status
        self.rodando = False




    # --- MONITORAMENTO DE SAÚDE (BOLINHAS) ---
    def monitorar_status_loop(self):

        """Loop que roda a cada 5 segundos atualizando os ícones de conexão"""
        if not self.rodando: return
        
        balanca_ok = self._testar_porta(self.config['porta_balanca'])
        impressora_ok = True
            
        self.status_callback("balanca", balanca_ok)
        self.status_callback("impressora", impressora_ok)
        
        # Agenda a próxima verificação usando o after do CustomTkinter (Thread Safe)
        self.view_root.after(5000, self.monitorar_status_loop)



    def _testar_porta(self, porta):

        try:
            with serial.Serial(porta, timeout=0.1) as ser:
                return ser.is_open
        except: 
            return False



    # --- MONITORAMENTO DE PESAGEM (BALANÇA) ---
    # --- MONITORAMENTO DE PESAGEM (BALANÇA) ---
    def iniciar_servicos(self, callback_comanda):
        # --- TENTA CONECTAR FISICAMENTE ANTES DE INICIAR O LOOP ---
        sucesso, msg = self.model.conectar()
        if not sucesso:
            print(f"AVISO: Não foi possível abrir a porta da balança: {msg}")
            # Mesmo que falhe, o status_loop vai mostrar a "bolinha vermelha" depois
        else:
            print("Conexão serial estabelecida com sucesso.")

        self.rodando = True
        print("HardwareService: Iniciando serviços...")

        # 1. Thread do Status (Bolinhas Verde/Vermelha)
        self.monitorar_status_loop()

        # 2. Thread da Balança (Leitura Serial)
        # Ajustado para o nome correto: monitorar_balanca_loop
        self.thread_balanca = threading.Thread(
            target=self._loop_balanca, 
            args=(callback_comanda,),
            daemon=True
        )
        self.thread_balanca.start()
        print("HardwareService: Monitoramento da balança ativo.")



    def _loop_balanca(self, callback_comanda):
        self.rodando = True
        print("HardwareService: Monitoramento da balança ativo.")
        
        while self.rodando:
            try:
                dados = self.model.obter_dados()
                
                # Regra: Peso relevante e maior que 10g
                if dados and dados.get('peso', 0) > 0.010:
                    
                    # 1. PRIMEIRO: Prepara o objeto (para não dar erro de variável não definida)
                    nova_comanda = {
                        "id": dados.get('id', datetime.now().strftime("%H%M%S")),
                        "peso": dados['peso'],
                        "preco_kg": dados['preco_por_kg'],
                        "total": round(dados['peso'] * dados['preco_por_kg'], 2)
                    }
                    
                    # 2. SEGUNDO: Envia para o GestaoController salvar no Banco e atualizar a UI
                    # O after(0) evita que a interface trave
                    self.view_root.after(0, lambda d=nova_comanda: callback_comanda(d))
                    
                    # 3. TERCEIRO: Imprime o ticket físico
                    self.model.imprimir_comanda(dados)
                    
                    print(f"BALANÇA: Peso detectado ({dados['peso']}kg). Comanda enviada e impressa.")
                    
                    # 4. QUARTO: Sleep de 4 segundos para o cliente retirar o prato 
                    # e não gerar 10 comandas seguidas do mesmo peso
                    time.sleep(4)
                    
                time.sleep(0.5)
            except Exception as e:
                print(f"ERRO CRÍTICO NO LOOP DA BALANÇA: {e}")
                time.sleep(2)



    def parar(self):

        self.rodando = False