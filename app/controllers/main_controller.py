from app.views.main_view import LoginView
from app.views.popups.cadastro_view import CadastroView
from app.models.user_model import UserModel
from app.models.caixa_model import CaixaModel
from app.controllers.gestao_controller import GestaoController
from app.controllers.venda_controller import VendaController
from app.controllers.produto_controller import ProdutoController
from app.models.clientes_model import ClientesModel
from tkinter import messagebox
from app.models.venda_model import VendaModel
# --- IMPORTAÇÃO NOVA (Adicione esta linha) ---
from app.services.produto_service import ProdutoService 
# ---------------------------------------------

class MainController():

    def __init__(self):
        self.view = LoginView()
        self.view.btn_entrar.configure(command=self.fazer_login)
        self.view.btn_criar_conta.configure(command=self.abrir_tela_cadastro)
        
        self.janela_cadastro = None
        self.model = UserModel()
        self.caixa_model = CaixaModel()
        self.venda_model = VendaModel(self.caixa_model.db)
        self.clientes_model = ClientesModel()
        self.sessao_atual = None
        


    def fazer_login(self):
        usuario = self.view.entry_usuario.get()
        senha = self.view.entry_senha.get()

        if self.model.validar_login(usuario, senha):
            self.view.withdraw() 
            self.usuario_logado = usuario 

            sessao_ativa = self.caixa_model.obter_sessao_ativa() 

            if sessao_ativa:
                self.sessao_atual = {'id': sessao_ativa['id']}
                self.caixa_model.sessao_id = sessao_ativa['id']
                print(f"SESSÃO RECUPERADA: ID {sessao_ativa['id']}")
            else:
                self.sessao_atual = None
                self.caixa_model.sessao_id = None
                print("NENHUMA SESSÃO ATIVA: O sistema iniciará fechado.")

            # --- CORREÇÃO AQUI ---
            
            # 1. Instancia o SERVIÇO (Lógica de Dados)
            # Passamos o DB do caixa_model para reaproveitar a conexão
            self.produto_service = ProdutoService(self.caixa_model.db) 
            
            # 2. Instancia o CONTROLLER (Telas de cadastro de produto)
            self.produto_ctrl = ProdutoController(self)
            
            # 3. Instancia o VendaController
            self.venda_ctrl = VendaController(self) 
            
            # 4. Instancia a Gestão
            # Passamos o produto_service correto agora!
            self.sistema_gestao = GestaoController(
                self, 
                self.usuario_logado, 
                produto_service=self.produto_service
            )
            
            self.sistema_gestao.iniciar()
        else:
            messagebox.showerror("Login", "Usuário ou Senha inválidos.")



    def abrir_sistema_gestao(self, usuario):
        # CORREÇÃO: Passe 'self' antes do usuário
        self.sistema = GestaoController(self, usuario) 
        self.sistema.iniciar()



    def abrir_tela_cadastro(self):

        if self.janela_cadastro is None or not self.janela_cadastro.winfo_exists():
            self.janela_cadastro = CadastroView(master=self.view)
            self.janela_cadastro.btn_cadastro_usuario.configure(command=self.salvar_novo_usuario)
        else:
            self.janela_cadastro.focus()
        


    def salvar_novo_usuario(self):

        nome_usuario = self.janela_cadastro.cadastro_entry_nome.get()
        senha_usuario = self.janela_cadastro.cadastro_entry_senha.get()
        
        if nome_usuario == "" or senha_usuario == "":
            messagebox.showwarning("Atenção", "Preencha todos os campos", parent=self.janela_cadastro)
            return
        
        sucesso, msg = self.model.cadastrar_usuario(nome_usuario, senha_usuario)
        if sucesso:
            messagebox.showinfo("Cadastro", f"Usuário {nome_usuario} cadastrado com sucesso!", parent=self.janela_cadastro)
            self.janela_cadastro.destroy()
        else:
            messagebox.showerror("Erro", msg, parent=self.janela_cadastro)
        


    def iniciar(self):

        self.view.mainloop()


        