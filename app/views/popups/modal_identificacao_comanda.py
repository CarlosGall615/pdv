import customtkinter as ctk
from app.views.base_view import BaseView 

class ModalIdentificacao(ctk.CTkToplevel, BaseView):
    def __init__(self, parent, id_comanda, categoria_inicial, total_atual=0.0, callback_sucesso=None):
        super().__init__(parent)
        self.title(f"Identificar Entrega - {id_comanda}")
        self.geometry("400x700") # Aumentado para os novos campos
        
        self.grab_set()
        self.focus_force()
        
        self.id_comanda = id_comanda
        self.total_atual = total_atual
        self.callback_sucesso = callback_sucesso

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"DADOS DE ENTREGA", font=("Arial", 16, "bold")).pack(pady=(0, 15))

        # --- DADOS BÁSICOS ---
        ctk.CTkLabel(container, text="Nome do Cliente:", font=("Arial", 11)).pack(anchor="w")
        self.ent_nome = ctk.CTkEntry(container, width=300)
        self.ent_nome.pack(pady=(2, 10))

        ctk.CTkLabel(container, text="Telefone:", font=("Arial", 11)).pack(anchor="w")
        self.ent_telefone = ctk.CTkEntry(container, width=300)
        self.ent_telefone.pack(pady=(2, 10))

        ctk.CTkLabel(container, text="Endereço Completo:", font=("Arial", 11)).pack(anchor="w")
        self.ent_endereco = ctk.CTkTextbox(container, width=300, height=70)
        self.ent_endereco.pack(pady=(2, 10))

        # --- FINANCEIRO MOTOBOY ---
        separador = ctk.CTkFrame(container, height=2, fg_color="gray")
        separador.pack(fill="x", pady=10)

        ctk.CTkLabel(
            container, 
            text=f"TOTAL DO PEDIDO: R$ {self.total_atual:.2f}", 
            font=("Arial", 13, "bold"), 
            text_color="#27ae60"
        ).pack()

        ctk.CTkLabel(container, text="Forma de Pagamento na Entrega:", font=("Arial", 11)).pack(anchor="w")
        self.combo_pag = ctk.CTkComboBox(container, values=["CARTÃO (MAQUININHA)", "DINHEIRO", "PIX", "JÁ PAGO ONLINE", "CREDIÁRIO"], width=300)
        self.combo_pag.pack(pady=(2, 10))

        ctk.CTkLabel(container, text="Troco para quanto? (Se for dinheiro):", font=("Arial", 11)).pack(anchor="w")
        self.ent_troco = ctk.CTkEntry(container, width=300, placeholder_text="Ex: 50.00")
        self.ent_troco.pack(pady=(2, 20))

        ctk.CTkLabel(container, text="Tipo / Categoria:", font=("Arial", 12)).pack(anchor="w")

        self.combo_tipo = ctk.CTkComboBox(container, values=["BALCÃO", "DELIVERY", "MESAS", "ONLINE"], width=300)

        self.combo_tipo.set(categoria_inicial.upper())

        self.combo_tipo.pack(pady=(5, 25))
        
        self.btn_confirmar = ctk.CTkButton(
            container, 
            text="CONFIRMAR E IMPRIMIR VIA", 
            fg_color="#27ae60", 
            hover_color="#219150",
            height=45,
            command=self.confirmar
        )
        self.btn_confirmar.pack(fill="x")

    def confirmar(self):
        # Tratamento de troco
        troco_val = self.ent_troco.get().replace(',', '.').strip()
        try:
            troco_para = float(troco_val) if troco_val else 0.0
        except:
            troco_para = 0.0


        dados_identificacao = {
            'nome': self.ent_nome.get().strip(),
            'telefone': self.ent_telefone.get().strip(),
            'endereco': self.ent_endereco.get("1.0", "end-1c").strip(),
            'forma_pagamento': self.combo_pag.get(), # <--- CHAVE ESSENCIAL
            'troco_para': troco_para,
            'categoria': self.combo_tipo.get(),
            'status': 'EM PREPARO'
        }
        print(f"DEBUG MODAL: Coletado -> {dados_identificacao}")

        if self.callback_sucesso:
            # Passamos o self no final para o controller conseguir fazer o modal_window.destroy()
            self.callback_sucesso(self.id_comanda, dados_identificacao, self)

        