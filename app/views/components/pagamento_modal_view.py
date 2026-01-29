import customtkinter as ctk
from app.views.base_view import BaseView

class PagamentoModalView(ctk.CTkToplevel, BaseView):
    def __init__(self, master, total, controller):
        super().__init__(master)
        self.controller = controller
        self.total = total
        
        self.title("Finalizar Venda")
        self.geometry("500x650")
        self.attributes("-topmost", True)
        self.grab_set()
        self.center_window(500, 650)
        # Título e Valor em destaque
        ctk.CTkLabel(self, text="VALOR TOTAL", font=("Arial", 16)).pack(pady=(20, 0))
        ctk.CTkLabel(self, text=f"R$ {total:.2f}", 
                     font=("Arial", 45, "bold"), text_color="#2fa572").pack(pady=(0, 20))

        # Indicador de Forma de Pagamento
        self.forma_pagamento = "Dinheiro"
        self.lbl_forma = ctk.CTkLabel(self, text=f"FORMA: {self.forma_pagamento.upper()}",
                                     font=("Arial", 18, "bold"), fg_color="#1f538d",
                                     corner_radius=8, height=50, width=400)
        self.lbl_forma.pack(pady=10)

        # Grade de Botões
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=20, padx=20)

        opcoes = [
            ("💵 DINHEIRO", "Dinheiro", "#2fa572"),
            ("📱 PIX", "Pix", "#32bcad"),
            ("💳 CRÉDITO", "Crédito", "#1f538d"),
            ("💳 DÉBITO", "Débito", "#1f538d"),
            ("🥗 VR", "Vale Refeição", "#a67c00"),
            ("🛒 VA", "Vale Alimentação", "#e67e22")
        ]

        col, lin = 0, 0
        for texto, valor, cor in opcoes:
            btn = ctk.CTkButton(self.frame_botoes, text=texto, font=("Arial", 14, "bold"),
                                fg_color=cor, height=65, width=200,
                                command=lambda v=valor: self._selecionar(v))
            btn.grid(row=lin, column=col, padx=8, pady=8)
            col += 1
            if col > 1: col = 0; lin += 1

        # Botão Finalizar
        self.btn_confirmar = ctk.CTkButton(self, text="CONFIRMAR E FINALIZAR", 
                                           fg_color="#2fa572", hover_color="#218358",
                                           font=("Arial", 20, "bold"), height=80, width=420,
                                           command=self._confirmar)
        self.btn_confirmar.pack(pady=(30, 10))

    

        
    def _selecionar(self, valor):
        self.forma_pagamento = valor
        self.lbl_forma.configure(text=f"FORMA: {valor.upper()}")

    def _confirmar(self):
        # Avisa o controller que o pagamento foi feito
        self.controller.finalizar_venda_db(self.total, self.forma_pagamento, self)