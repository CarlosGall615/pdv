import customtkinter as ctk

class ConfigView(ctk.CTkFrame):

    def __init__(self, master, config_atual, portas_disponiveis, callback_salvar, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")

        # Título
        ctk.CTkLabel(self, text="⚙️ CONFIGURAÇÕES DE HARDWARE", 
                     font=("Arial", 22, "bold"), text_color="#1f538d").pack(pady=20)

        # Container Central
        self.container = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.container.pack(fill="both", expand=True, padx=40, pady=20)

        # --- Seção Balança ---
        ctk.CTkLabel(self.container, text="Configurações da Balança", font=("Arial", 16, "bold")).pack(pady=(20, 10))
        
        self.combo_balanca = self._criar_campo("Porta Serial (Balança):", portas_disponiveis, config_atual['porta_balanca'])

        # --- Seção Impressora ---
        ctk.CTkLabel(self.container, text="Configurações da Impressora", font=("Arial", 16, "bold")).pack(pady=(30, 10))
        
        self.combo_impressora = self._criar_campo("Porta Serial (Impressora):", portas_disponiveis, config_atual['porta_impressora'])

        # Botão Salvar
        self.btn_salvar = ctk.CTkButton(self.container, text="SALVAR CONFIGURAÇÕES", 
                                        fg_color="#28a745", hover_color="#218838",
                                        font=("Arial", 14, "bold"), height=45,
                                        command=lambda: callback_salvar({
                                            "porta_balanca": self.combo_balanca.get(),
                                            "porta_impressora": self.combo_impressora.get(),
                                            "baudrate_balanca": 9600,
                                            "baudrate_impressora": 115200
                                        }))
        self.btn_salvar.pack(pady=40)



    def _criar_campo(self, label_text, valores, valor_atual):

        """Helper para criar os campos de seleção"""
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.pack(fill="x", padx=100, pady=5)
        
        ctk.CTkLabel(frame, text=label_text).pack(side="left")
        combo = ctk.CTkOptionMenu(frame, values=valores, width=150)
        combo.set(valor_atual)
        combo.pack(side="right")
        return combo