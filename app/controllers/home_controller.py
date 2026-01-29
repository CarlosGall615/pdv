import threading
from app.models.balanca_model import BalancaModel
import time  
import customtkinter as ctk
from datetime import datetime
from app.models.historico_model import HistoricoModel
from app.models.config_model import ConfigModel
import serial

class HomeController:

    def __init__(self, usuario_nome):
        # Criamos a view apenas UMA vez
        self.config_manager = ConfigModel()
        self.config = self.config_manager.carregar_config()
        self.historico_model = HistoricoModel()
        self.model = BalancaModel()
        self.comandas_ativas = [] # Guardaremos os objetos das comandas aqui
        self.janela_dashboard = None
        self.verificar_hardware()

        self.model.porta_balanca = self.config['porta_balanca']
        self.model.porta_impressora = self.config['porta_impressora']
        # Conexão da Balança
        sucesso, msg = self.model.conectar()
        if not sucesso:
            print(f"⚠️ Atenção: {msg}") # Aviso no console se a COM4 não abrir



    def start_monitoramento(self):
        print("🚀 Monitoramento da balança iniciado...")
        t = threading.Thread(target=self.loop_leitura, daemon=True)
        t.start()



    def loop_leitura(self):

        while True:
            try:
                dados = self.model.obter_dados()
                if dados and dados['total'] > 0:
                    self.view.after(0, lambda d=dados: self.criar_comanda_na_tela(d))
                    time.sleep(3) # Tempo para o usuário tirar o produto da balança
                time.sleep(0.5)
            except Exception as e:
                print(f"Erro no loop de leitura: {e}")
                break



    def criar_comanda_na_tela(self, dados):
        
        # Limpar comandas que foram destruídas da lista antes de calcular o novo index
        self.comandas_ativas = [c for c in self.comandas_ativas if c.winfo_exists()]
        
        index = len(self.comandas_ativas)
        
        # Criando o Frame da Comanda
        f = ctk.CTkFrame(self.view.frame_comandas, width=170, height=200, border_width=2)
        f.grid(row=index // 4, column=index % 4, padx=10, pady=10)
        f.pack_propagate(False) # Mantém o tamanho fixo do frame
        
        ctk.CTkLabel(f, text=f"PESO: {dados['peso']:.3f}kg", font=("Arial", 14, "bold")).pack(pady=10)
        ctk.CTkLabel(f, text=f"TOTAL: R${dados['total']:.2f}").pack()
        
        # Botão Finalizar agora limpa a lista também
        btn = ctk.CTkButton(f, text="Finalizar", fg_color="green", 
                            command=lambda: self.remover_comanda(f))
        btn.pack(side="bottom", pady=10)
        
        hora_atual = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{hora_atual}] {dados['peso']:.3f}kg - R${dados['total']:.2f}\n"
        
        try:
            print(f"Enviando para a impressora na porta {self.model.porta_impressora}...")
            # Chamamos a função do model que cuida do ESC/POS
            self.model.imprimir_comanda(dados)
            print("✅ Comando de impressão enviado!")
        except Exception as e:
            print(f"❌ Erro ao imprimir: {e}")
            
        self.view.lista_logs.configure(state="normal") # Libera para escrita
        self.view.lista_logs.insert("0.0", log_msg)    # Insere no topo
        self.view.lista_logs.configure(state="disabled") # Trava novamente

        self.historico_model.salvar_registro(dados)
        self.comandas_ativas.append(f)



    def verificar_hardware(self):

        # --- TESTE DA BALANÇA ---
        balanca_ok = False
        try:
            # Tenta abrir a porta configurada
            with serial.Serial(self.model.porta_balanca, timeout=0.1) as ser:
                balanca_ok = ser.is_open
        except:
            balanca_ok = False

        # --- TESTE DA IMPRESSORA ---
        impressora_ok = False
        # Se for a mesma porta da balança, é um erro de config (conflito)
        if self.model.porta_impressora == self.model.porta_balanca:
            impressora_ok = False
        else:
            try:
                with serial.Serial(self.model.porta_impressora, timeout=0.1) as ser:
                    impressora_ok = ser.is_open
            except:
                impressora_ok = False

        # Atualiza a interface
        self.view.atualizar_cor_status("balanca", balanca_ok)
        self.view.atualizar_cor_status("impressora", impressora_ok)

        # Repete a cada 5 segundos
        self.view.after(5000, self.verificar_hardware)



    def salvar_novas_configuracoes(self, novas_configs):
        self.config_manager.salvar_config(novas_configs)
        self.config = novas_configs
        # Atualiza o hardware em tempo real
        self.model.porta_balanca = novas_configs['porta_balanca']
        self.model.porta_impressora = novas_configs['porta_impressora']
        print("✅ Configurações atualizadas e salvas!")



    def remover_comanda(self, frame):
        frame.destroy()
        # O próximo 'criar_comanda_na_tela' vai reorganizar os índices automaticamente



