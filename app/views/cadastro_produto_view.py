import customtkinter as ctk
from tkinter import messagebox

class CadastroProdutoView(ctk.CTkToplevel):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.title("Sistema ERP - Cadastro de Produtos")
        self.geometry("450x550")
        self.configure(fg_color="#2F5965")
        
        self.grab_set() # Foca apenas nesta janela

        # Título
        ctk.CTkLabel(self, text="NOVO PRODUTO", font=("Arial", 22, "bold"), text_color="#D4AF37").pack(pady=20)

        # Container
        self.frame = ctk.CTkFrame(self, fg_color="#4C727D", border_color="#D4AF37", border_width=1)
        self.frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Campos
        self.ent_nome = self._criar_input("Nome do Produto:")
        self.ent_preco = self._criar_input("Preço de Venda (R$):")
        self.ent_codigo = self._criar_input("Código de Barras:")
        self.ent_cat = self._criar_input("Categoria (ex: Bebidas):")

        # Switch de Atalho
        self.var_atalho = ctk.IntVar(value=0)
        self.sw_atalho = ctk.CTkSwitch(self.frame, text="Exibir como ATALHO no PDV", 
                                       variable=self.var_atalho, 
                                       text_color="white", font=("Arial", 12, "bold"),
                                       progress_color="#D4AF37")
        self.sw_atalho.pack(pady=20, padx=20, anchor="w")

        # Botão Salvar
        self.btn_salvar = ctk.CTkButton(self, text="CONCLUIR CADASTRO", 
                                        fg_color="#D4AF37", text_color="black",
                                        font=("Arial", 14, "bold"), height=45,
                                        command=self.confirmar_salvamento)
        self.btn_salvar.pack(pady=20, padx=20, fill="x")

    def _criar_input(self, label_text):
        ctk.CTkLabel(self.frame, text=label_text, text_color="white").pack(padx=20, pady=(10,0), anchor="w")
        entry = ctk.CTkEntry(self.frame, fg_color="#2F5965", border_color="#D4AF37")
        entry.pack(fill="x", padx=20, pady=5)
        return entry

    def confirmar_salvamento(self):
        try:
            dados = {
                "nome": self.ent_nome.get(),
                "preco": float(self.ent_preco.get().replace(",", ".")),
                "codigo": self.ent_codigo.get(),
                "categoria": self.ent_cat.get(),
                "atalho": self.var_atalho.get()
            }
            if not dados["nome"] or not dados["preco"]:
                raise ValueError
                
            if self.controller.salvar_produto_no_banco(dados):
                messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")
                self.destroy()
            else:
                messagebox.showerror("Erro", "Código de barras já existe!")
        except ValueError:
            messagebox.showerror("Erro", "Preencha Nome e Preço corretamente!")