import customtkinter as ctk
from app.views.base_view import BaseView
from tkinter import messagebox

class PagamentoModalView(ctk.CTkToplevel, BaseView):
    def __init__(self, master, total, controller):
        super().__init__(master)
        self.controller = controller
        self.total_original = total
        self.restante = total
        
        self.title("Finalizar Venda - Pagamento Misto")
        self.geometry("500x850") # Aumentei um pouco para caber a lista
        self.attributes("-topmost", True)
        self.grab_set()
        self.center_window(500, 850)

        # 1. Indicadores de Valor
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=20)
        
        cliente_nome = "Consumidor Final"
        if hasattr(self.controller, 'cliente_atual_venda') and self.controller.cliente_atual_venda:
            cliente_nome = self.controller.cliente_atual_venda['nome_razao'].upper()
            
        self.lbl_cliente_venda = ctk.CTkLabel(self, text=f"Cliente: {cliente_nome}", 
                                              font=("Arial", 12, "italic"), text_color="#BDC3C7")
        self.lbl_cliente_venda.pack(pady=(0, 10))

        
        ctk.CTkLabel(header, text="RESTANTE A PAGAR", font=("Arial", 14)).pack()
        self.lbl_restante = ctk.CTkLabel(header, text=f"R$ {self.restante:.2f}", 
                                         font=("Arial", 48, "bold"), text_color="#2fa572")
        self.lbl_restante.pack()

        # 2. Campo para digitar o valor que está sendo pago agora
        ctk.CTkLabel(self, text="Valor a receber:", font=("Arial", 12)).pack()
        self.entry_valor_pagar = ctk.CTkEntry(self, font=("Arial", 24, "bold"), width=300, 
                                             height=50, justify="center", placeholder_text=f"R$ {self.restante:.2f}")
        self.entry_valor_pagar.pack(pady=10)
        self.entry_valor_pagar.insert(0, f"{self.restante:.2f}") # Já sugere o total

        # 3. Grade de Botões (Agora eles ADICIONAM o pagamento)
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=10, padx=20)

        opcoes = [
            ("💵 DINHEIRO", "Dinheiro", "#2fa572"),
            ("📱 PIX", "Pix", "#32bcad"),
            ("💳 CRÉDITO", "Crédito", "#1f538d"),
            ("💳 DÉBITO", "Débito", "#1f538d"),
            ("🥗 VR", "Vale Refeição", "#a67c00"),
            ("🛒 VA", "Vale Alimentação", "#e67e22"),
            ("📝 CREDIÁRIO", "Crediário", "#6C3940")
        ]

        col, lin = 0, 0
        for texto, valor, cor in opcoes:
            btn = ctk.CTkButton(self.frame_botoes, text=texto, font=("Arial", 13, "bold"),
                                fg_color=cor, height=55, width=205,
                                command=lambda v=valor: self._adicionar_pagamento(v))
            btn.grid(row=lin, column=col, padx=5, pady=5)
            col += 1
            if col > 1: col = 0; lin += 1

        # 4. Lista de pagamentos (Textbox)
        frame_lista = ctk.CTkFrame(self, fg_color="transparent")
        frame_lista.pack(pady=10)

        ctk.CTkLabel(frame_lista, text="PAGAMENTOS ADICIONADOS:", font=("Arial", 11, "bold")).pack(side="left", padx=5)
        
        # BOTÃO LIMPAR (Novo)
        self.btn_limpar = ctk.CTkButton(frame_lista, text="🔄 LIMPAR TUDO", font=("Arial", 10, "bold"),
                                        fg_color="#c0392b", hover_color="#a93226", width=100, height=20,
                                        command=self._limpar_pagamentos)
        self.btn_limpar.pack(side="right", padx=5)

        self.txt_pagamentos = ctk.CTkTextbox(self, width=420, height=120, font=("Courier New", 14))
        self.txt_pagamentos.pack(pady=5)
        self.txt_pagamentos.configure(state="disabled")

        # 5. Botão Finalizar (Inicia desativado até quitar o total)
        self.btn_confirmar = ctk.CTkButton(self, text="FINALIZAR VENDA", 
                                           fg_color="gray", state="disabled",
                                           font=("Arial", 20, "bold"), height=70, width=420,
                                           command=self._confirmar_final)
        self.btn_confirmar.pack(pady=(20, 10))

        self.protocol("WM_DELETE_WINDOW", self._ao_fechar_janela)


    def _limpar_pagamentos(self):
        if messagebox.askyesno("Limpar", "Deseja remover os pagamentos adicionados?", parent=self):
            self.controller.limpar_pagamentos_parciais() # Chama o novo método
            self.restante = self.total_original
            self._atualizar_ui()

    def _ao_fechar_janela(self):
        # Antes de destruir a tela, garante que a memória do controller seja limpa
        self.controller.limpar_pagamentos_parciais() 
        self.destroy()


    def _adicionar_pagamento(self, metodo):
        valor_str = self.entry_valor_pagar.get().replace(",", ".")
        try:
            valor = float(valor_str)
            
            # --- VALIDAÇÃO DE CREDIÁRIO ---
            if metodo == "Crediário":
                # Verifica no controller se há um cliente real identificado
                cliente = getattr(self.controller, 'cliente_atual_venda', None)
                if not cliente:
                    messagebox.showerror("Crediário", "Identifique um cliente no PDV para usar o Crediário!", parent=self)
                    return
                
                # Validação de limite (usando a função que planejamos)
                sucesso_limite, msg = self.controller.validar_limite_crediario(valor)
                if not sucesso_limite:
                    messagebox.showerror("Limite Excedido", msg)
                    return
            # ------------------------------

            # Chama o controller para processar esse pagamento parcial
            sucesso, novo_restante = self.controller.adicionar_pagamento_parcial(metodo, valor, self.total_original)
            
            if sucesso:
                self.restante = novo_restante
                self._atualizar_ui()
            else:
                messagebox.showerror("Erro", novo_restante)
        except ValueError:
            messagebox.showerror("Erro", "Digite um valor válido.")

    def _atualizar_ui(self):
        # Atualiza o label do restante
        self.lbl_restante.configure(text=f"R$ {self.restante:.2f}")
        
        # Atualiza a lista visual de pagamentos
        self.txt_pagamentos.configure(state="normal")
        self.txt_pagamentos.delete("1.0", "end")
        for p in self.controller.pagamentos_atuais:
            self.txt_pagamentos.insert("end", f"{p['metodo']:.<25} R$ {p['valor']:>8.2f}\n")
        self.txt_pagamentos.configure(state="disabled")

        # Limpa o entry e foca o restante se ainda houver
        self.entry_valor_pagar.delete(0, 'end')
        if self.restante > 0:
            self.entry_valor_pagar.insert(0, f"{self.restante:.2f}")
        else:
            self.btn_confirmar.configure(fg_color="#2fa572", state="normal")
            self.lbl_restante.configure(text_color="white") # Indica que zerou

    def _confirmar_final(self):
        # Avisa o controller para salvar tudo e fechar o pedido
        if self.controller.finalizar_venda(self):
            
            self.destroy()
            