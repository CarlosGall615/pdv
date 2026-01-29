import customtkinter as ctk
from app.views.base_view import BaseView

class ConfiguracaoEmpresaView(ctk.CTkToplevel, BaseView):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        
        self.title("Dados da Empresa - Emitente")
        self.geometry("500x600")
        
        # Centraliza usando sua BaseView
        if hasattr(self, "centralizar"):
            self.centralizar(500, 600)
            
        self.grab_set() # Foco total nesta janela
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Título da Tela
        ctk.CTkLabel(self, text="📝 Cadastro do Emitente", 
                     font=("Arial", 20, "bold")).pack(pady=20)

        # Container para os campos (Scrollable se precisar de muitos dados)
        self.frame_campos = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_campos.pack(fill="both", expand=True, padx=40)

        # Dicionário para facilitar a criação dos campos
        self.entries = {}
        campos = [
            ("Nome Fantasia", "nome_fantasia"),
            ("Razão Social", "razao_social"),
            ("CNPJ", "cnpj"),
            ("Endereço Completo", "endereco"),
            ("Telefone", "telefone"),
            ("Mensagem no Rodapé", "mensagem_rodape")
        ]

        for rotulo, chave in campos:
            lbl = ctk.CTkLabel(self.frame_campos, text=rotulo, font=("Arial", 12, "bold"))
            lbl.pack(anchor="w", pady=(10, 0))
            
            entry = ctk.CTkEntry(self.frame_campos, placeholder_text=f"Digite {rotulo}...", width=400)
            entry.pack(pady=(2, 5))
            self.entries[chave] = entry

        # Botão Salvar
        self.btn_salvar = ctk.CTkButton(
            self, 
            text="💾 Salvar Configurações", 
            command=self._ao_clicar_salvar,
            font=("Arial", 14, "bold"),
            height=45,
            fg_color="#2fa572", # Verde
            hover_color="#227d56"
        )
        self.btn_salvar.pack(pady=30)

    def _ao_clicar_salvar(self):
        # Coleta todos os dados das entries
        dados = {chave: entry.get() for chave, entry in self.entries.items()}
        self.controller.salvar_dados_empresa(dados)