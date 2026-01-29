import customtkinter as ctk
from app.views.base_view import BaseView

class AberturaCaixaView(ctk.CTkToplevel, BaseView):

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        
        self.title("Abertura de Caixa")
        self.geometry("300x200")
        self.grab_set() 
        self.center_window(300,200) # Faz o foco ficar só nesta janela
        self.resizable(False, False)

        # Centralizar na tela
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="Informe o valor em fundo de caixa:", font=("Arial", 14)).pack(pady=20)

        self.entry_valor = ctk.CTkEntry(self, placeholder_text="R$ 0,00", width=150)
        self.entry_valor.pack(pady=10)
        self.entry_valor.focus_set()

        self.btn_confirmar = ctk.CTkButton(
            self, 
            text="Confirmar Abertura", 
            command=lambda: self.controller.confirmar_abertura_caixa(self.entry_valor.get())
        )
        self.btn_confirmar.pack(pady=20)

        # Atalho: apertar Enter confirma
        self.bind("<Return>", lambda e: self.controller.confirmar_abertura_caixa(self.entry_valor.get()))


        