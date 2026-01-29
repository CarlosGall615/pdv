import customtkinter as ctk
from app.views.base_view import BaseView

class LoginView(ctk.CTk, BaseView):

    def __init__(self):
        
        super().__init__()

        # Configurações da Janela Principal
        self.title("Acesso ao Sistema")
        self.geometry("600x700")
        self.configure(fg_color="#2F5965") # Fundo Azul Petróleo
        self.center_window(600, 700)

        # Centralizar o conteúdo criando um Card
        self.card = ctk.CTkFrame(
            self, 
            fg_color="#4C727D", 
            border_color="#D4AF37", 
            border_width=3, 
            corner_radius=30,
            width=450,
            height=600
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False) # Mantém o tamanho do card

        # --- CONTEÚDO DO LOGIN ---
        
        # Ícone de Cadeado ou Logo
        ctk.CTkLabel(self.card, text="🔐", font=("Arial", 70)).pack(pady=(50, 10))
        
        ctk.CTkLabel(
            self.card, 
            text="BEM-VINDO", 
            font=("Segoe UI", 28, "bold"), 
            text_color="#D4AF37"
        ).pack(pady=(0, 30))

        # Campo Usuário
        ctk.CTkLabel(self.card, text='USUÁRIO', font=("Segoe UI", 12, "bold"), text_color="white").pack(padx=50, anchor="w")
        self.entry_usuario = ctk.CTkEntry(
            self.card, 
            placeholder_text='CPF ou E-mail',
            width=350,
            height=45,
            border_color="#D4AF37",
            fg_color="#2F5965"
        )
        self.entry_usuario.pack(pady=(5, 20))

        # Campo Senha
        ctk.CTkLabel(self.card, text='SENHA', font=("Segoe UI", 12, "bold"), text_color="white").pack(padx=50, anchor="w")
        self.entry_senha = ctk.CTkEntry(
            self.card, 
            placeholder_text="Senha de Acesso", 
            show="*",
            width=350,
            height=45,
            border_color="#D4AF37",
            fg_color="#2F5965"
        )
        self.entry_senha.pack(pady=(5, 30))
        
        # Botão Entrar (Vinho Clássico)
        self.btn_entrar = ctk.CTkButton(
            self.card, 
            text='ACESSAR SISTEMA',
            font=("Segoe UI", 16, "bold"),
            fg_color="#6C3940",
            hover_color="#552d32",
            width=350,
            height=50,
            corner_radius=12
        )
        self.btn_entrar.pack(pady=10)

        # Botão Criar Conta (Estilo Outline / Mais discreto)
        self.btn_criar_conta = ctk.CTkButton(
            self.card, 
            text='Não possui conta? Registre-se',
            font=("Segoe UI", 12, "underline"),
            fg_color="transparent",
            text_color="#D4AF37",
            hover_color="#4C727D",
            width=350,
            height=30,
            
        )
        self.btn_criar_conta.pack(pady=10)

    

