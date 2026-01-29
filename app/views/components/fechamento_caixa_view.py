# app/views/components/fechamento_caixa_view.py
import customtkinter as ctk
from tkinter import messagebox
from app.views.base_view import BaseView

class FechamentoCaixaView(ctk.CTkToplevel, BaseView):
    def __init__(self, master, controller, totais_esperados):
        super().__init__(master)
        self.controller = controller
        self.totais_esperados = totais_esperados
        self.inputs = {}

        self.title("Conferência de Valores")
        self.geometry("400x600")
        self.attributes("-topmost", True)
        #self.grab_set()
        self.center_window(400, 600)
        ctk.CTkLabel(self, text="CONFERÊNCIA DE CAIXA", font=("Arial", 18, "bold")).pack(pady=20)

        # Criar campos para cada método
        for metodo in self.totais_esperados.keys():
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.pack(fill="x", padx=30, pady=5)
            
            ctk.CTkLabel(frame, text=metodo, font=("Arial", 14)).pack(side="left")
            
            entry = ctk.CTkEntry(frame, placeholder_text="R$ 0,00", width=120)
            entry.pack(side="right")
            self.inputs[metodo] = entry

        self.btn_fechar = ctk.CTkButton(self, text="FINALIZAR FECHAMENTO", 
                                        fg_color="#D4AF37", text_color="black",
                                        font=("Arial", 16, "bold"), height=50,
                                        command=self.processar)
        self.btn_fechar.pack(pady=30, padx=30, fill="x")



    
    def processar(self):
        relatorio = "--- CONFERÊNCIA FINAL ---\n\n"
        try:
            for metodo, esperado in self.totais_esperados.items():
                # Pega o que o usuário digitou
                digitado_str = self.inputs[metodo].get().replace(",", ".")
                digitado = float(digitado_str) if digitado_str else 0.0
                
                diferenca = digitado - esperado
                relatorio += f"{metodo}:\n"
                relatorio += f"  Esperado: R$ {esperado:.2f}\n"
                relatorio += f"  Informado: R$ {digitado:.2f}\n"
                relatorio += f"  Diferença: R$ {diferenca:.2f}\n\n"

            # Envia o relatório pronto para o controller finalizar o sistema
            self.controller.finalizar_encerrar_caixa_total(relatorio, self)
            
        except ValueError:
            messagebox.showerror("Erro", "Por favor, digite apenas números (ex: 10.50)")