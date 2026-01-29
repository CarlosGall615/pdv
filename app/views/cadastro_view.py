import customtkinter as ctk
from app.views.base_view import BaseView
class CadastroView(ctk.CTkToplevel, BaseView):

    def __init__(self, master):
        super().__init__(master)

        # Configurações da Janela Pop-up
        self.title('Novo Cadastro de Operador')
        self.geometry('500x600')
        self.configure(fg_color="#2F5965") # Fundo Azul Petróleo
        self.attributes('-topmost', True)
        self.grab_set() # Foca apenas nesta janela
        
        self.center_window(500, 600)
        # Card Principal do Cadastro
        self.card = ctk.CTkFrame(
            self, 
            fg_color="#4C727D", 
            border_color="#D4AF37", 
            border_width=3, 
            corner_radius=25
        )
        self.card.pack(expand=True, fill="both", padx=30, pady=30)

        # Título
        ctk.CTkLabel(self.card, text="📝", font=("Arial", 50)).pack(pady=(30, 10))
        ctk.CTkLabel(
            self.card, 
            text="CRIAR CONTA", 
            font=("Segoe UI", 22, "bold"), 
            text_color="#D4AF37"
        ).pack(pady=(0, 20))

        # --- CAMPOS DE ENTRADA ---
        
        # Usuário
        self._criar_label("USUÁRIO (CPF OU E-MAIL)")
        self.cadastro_entry_nome = self._criar_entry('Ex: 123.456.789-00')
        self.cadastro_entry_nome.pack(pady=(5, 15))

        # Senha
        self._criar_label("SENHA DE ACESSO")
        self.cadastro_entry_senha = self._criar_entry('Digite uma senha forte', show="*")
        self.cadastro_entry_senha.pack(pady=(5, 15))

        # Confirmar Senha (Importante para evitar erros!)
        self._criar_label("CONFIRMAR SENHA")
        self.cadastro_entry_confirmar = self._criar_entry('Repita a senha', show="*")
        self.cadastro_entry_confirmar.pack(pady=(5, 30))

        # --- BOTÕES ---
        
        self.btn_cadastro_usuario = ctk.CTkButton(
            self.card, 
            text='SALVAR REGISTRO',
            font=("Segoe UI", 16, "bold"),
            fg_color="#6C3940", # Vinho
            hover_color="#552d32",
            width=300,
            height=50,
            corner_radius=12
        )
        self.btn_cadastro_usuario.pack(pady=5)

        self.btn_cancelar = ctk.CTkButton(
            self.card, 
            text='CANCELAR',
            font=("Segoe UI", 12),
            fg_color="transparent",
            text_color="white",
            hover_color="#3d5b64",
            command=self.destroy
        )
        self.btn_cancelar.pack(pady=10)

    def _criar_label(self, texto):
        """Auxiliar para manter o padrão das labels"""
        lbl = ctk.CTkLabel(self.card, text=texto, font=("Segoe UI", 11, "bold"), text_color="white")
        lbl.pack(padx=45, anchor="w")
        return lbl

    def _criar_entry(self, placeholder, show=""):
        """Auxiliar para manter o padrão dos inputs"""
        return ctk.CTkEntry(
            self.card, 
            placeholder_text=placeholder,
            show=show,
            width=320,
            height=40,
            border_color="#D4AF37",
            fg_color="#2F5965"
        )
    
    

