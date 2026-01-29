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
        self.geometry("400x650")
        self.attributes("-topmost", True)
        self.center_window(400, 650)
        
        # Cabeçalho
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=20, fill="x")
        
        ctk.CTkLabel(header_frame, text="CONFERÊNCIA DE CAIXA", 
                     font=("Arial", 20, "bold")).pack()
        ctk.CTkLabel(header_frame, text="Informe os valores físicos presentes no caixa", 
                     font=("Arial", 12)).pack()

        # Container para os campos (Scrollable se houver muitos métodos)
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent", height=350)
        self.container.pack(fill="both", padx=20, expand=True)

        # Criar campos para cada método (Dinheiro, Cartão, Pix, etc)
        for metodo in self.totais_esperados.keys():
            self._criar_campo_metodo(metodo)

        # Botão Finalizar
        self.btn_fechar = ctk.CTkButton(
            self, text="FINALIZAR FECHAMENTO", 
            fg_color="#D4AF37", text_color="black",
            font=("Arial", 16, "bold"), height=55,
            command=self.processar
        )
        self.btn_fechar.pack(pady=30, padx=30, fill="x")

    def _criar_campo_metodo(self, metodo):
        frame = ctk.CTkFrame(self.container, fg_color=("gray90", "gray15"))
        frame.pack(fill="x", pady=5)
        
        label_metodo = ctk.CTkLabel(frame, text=metodo.upper(), font=("Arial", 13, "bold"))
        label_metodo.pack(side="left", padx=15, pady=10)
        
        entry = ctk.CTkEntry(frame, placeholder_text="0,00", width=120, justify="right")
        entry.pack(side="right", padx=15, pady=10)
        self.inputs[metodo] = entry

    def processar(self):
        relatorio = "--- RELATÓRIO DE CONFERÊNCIA ---\n"
        relatorio += f"Data/Hora: {self.get_data_hora_atual()}\n\n"
        
        total_esperado_geral = 0
        total_informado_geral = 0

        try:
            for metodo, esperado in self.totais_esperados.items():
                # Limpeza básica do input
                digitado_raw = self.inputs[metodo].get().replace(".", "").replace(",", ".")
                digitado = float(digitado_raw) if digitado_raw else 0.0
                
                diferenca = digitado - esperado
                
                total_esperado_geral += esperado
                total_informado_geral += digitado

                relatorio += f"[{metodo.upper()}]\n"
                relatorio += f" > Esperado:  R$ {esperado:8.2f}\n"
                relatorio += f" > Informado: R$ {digitado:8.2f}\n"
                relatorio += f" > Diferença: R$ {diferenca:8.2f}\n"
                relatorio += "-" * 30 + "\n"

            relatorio += f"\nTOTAL GERAL ESPERADO:  R$ {total_esperado_geral:.2f}"
            relatorio += f"\nTOTAL GERAL INFORMADO: R$ {total_informado_geral:.2f}"
            
            dif_final = total_informado_geral - total_esperado_geral
            relatorio += f"\nDIFERENÇA FINAL:     R$ {dif_final:.2f}"

            # Confirmação Final
            if messagebox.askyesno("Confirmar", "Deseja finalizar o caixa com estes valores?", parent=self):
                self.controller.finalizar_encerrar_caixa_total(relatorio, self)
            
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido informado. Use o formato: 10,50", parent=self)

    def get_data_hora_atual(self):
        from datetime import datetime
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")