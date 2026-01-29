import customtkinter as ctk
import sys
from app.services.hardware_service import HardwareService
from app.models.venda_model import VendaModel
from app.models.balanca_model import BalancaModel
from app.views.gestao_view import GestaoView
from app.models.caixa_model import CaixaModel
from datetime import datetime 
from app.views.pages.comandas_view import ComandasView
from tkinter import messagebox
from app.views.popups.comanda_modal_view import ComandaModalView
from app.services.comanda_service import ComandaService
from app.services.pagamento_service import PagamentoService
from app.views.popups.gestao_caixa_view import GestaoCaixaView
from app.views.popups.fechamento_caixa_view import FechamentoCaixaView
from app.controllers.caixa_controller import CaixaController
from app.controllers.produto_controller import ProdutoController
from app.controllers.venda_controller import VendaController
from app.controllers.comanda_controller import ComandaController
from app.views.pages.dashboard_view import DashboardView
from app.views.popups.configuracao_empresa_view import ConfiguracaoEmpresaView
from app.models.empresa_model import EmpresaModel
from app.models.clientes_model import ClientesModel
from app.services.impressao_service import ImpressaoService

class GestaoController:
    
    def __init__(self, main_controller, usuario, produto_service=None): 
        # 0. A REFERÊNCIA MESTRE
        self.main = main_controller
        self.usuario_logado = usuario
        self.usuario = usuario # Mantendo compatibilidade com códigos que usam .usuario
        
        # 1. MODELOS: Reutiliza conexão do Main (Evita Database Locked)
        # Se main_controller tiver caixa_model, usa ele. Senão, cria novo.
        self.caixa_model = getattr(main_controller, 'caixa_model', CaixaModel())
        self.db = self.caixa_model.db
        
        # Variáveis de Estado
        self.comanda_em_edicao = None
        self.modo_pagamento_comanda = False
        self.sessao_atual = None
        
        # 2. Inicialização de Modelos de Dados
        self.balanca_model = BalancaModel()
        # Tenta pegar do main primeiro, se não existir, cria novo
        self.venda_model = getattr(main_controller, 'vendas_model', VendaModel(self.db))
        self.empresa_model = EmpresaModel(self.db)
        self.clientes_model = getattr(main_controller, 'clientes_model', ClientesModel(self.db))
        
        # 3. Serviços e Lógica de Negócio (AQUI ESTAVA O ERRO ANTES)
        # -----------------------------------------------------------
        # Lógica de Fallback: Se não veio no parâmetro, pega do main. 
        # Se não tem no main, cria do zero.
        if produto_service:
            self.produto_service = produto_service
        elif hasattr(main_controller, 'produto_service') and main_controller.produto_service:
            self.produto_service = main_controller.produto_service
        else:
            from app.services.produto_service import ProdutoService
            self.produto_service = ProdutoService()
        # -----------------------------------------------------------

        self.comanda_service = ComandaService()
        self.pagamento_service = PagamentoService()
        self.impressora = ImpressaoService()
        
        # 4. Inicializa a View Principal (GestaoView)
        from app.views.gestao_view import GestaoView
        self.view = GestaoView(usuario, self)
        
        # SINCRONIZAÇÃO CRUCIAL: 
        # Atualiza o MainController para saber que a view atual mudou
        self.main.view = self.view
        
        # 5. Inicializa os Controladores Especialistas
        # Passamos 'self' (GestaoController) para que eles acessem os serviços definidos acima
        self.caixa_ctrl = CaixaController(self)
        self.produto_ctrl = ProdutoController(self)
        self.comanda_ctrl = ComandaController(self)
        
        # O VendaController precisa acessar self.produto_service, por isso instanciamos aqui
        self.venda_ctrl = VendaController(self)

        # 6. Configura o Hardware Service (Balança e Impressora)
        config_hw = {
            'porta_balanca': self.balanca_model.porta_balanca,
            'porta_impressora': 'COM6' # Ajuste se necessário
        }
        self.hardware = HardwareService(
            config_hw, 
            self.balanca_model, 
            self.view, 
            self.view.atualizar_cor_status
        )

        # 7. Mapeia os comandos dos botões da Sidebar
        if hasattr(self.view, 'btn_dash'): # Verificação de segurança
            self.view.btn_dash.configure(command=lambda: self.view.pode_navegar(lambda: self.filtrar_dashboard("Dia")))
            self.view.btn_pdv.configure(command=lambda: self.view.pode_navegar(self.exibir_pdv))
            self.view.btn_comandas.configure(command=lambda: self.view.pode_navegar(self.exibir_comandas_pendentes))
            self.view.btn_cadastros.configure(command=lambda: self.view.pode_navegar(self.exibir_cadastros))
            self.view.btn_clientes.configure(command=lambda: self.view.pode_navegar(self.inicializar_cards_clientes))
            self.view.btn_sair.configure(command=self.fazer_logout)

        # 8. Inicia os serviços e carrega dados iniciais
        if hasattr(self.comanda_service, 'comandas_abertas'):
            self.comanda_ctrl.comandas_abertas = self.comanda_service.comandas_abertas
            
        self.hardware.iniciar_servicos(callback_comanda=self.comanda_ctrl.receber_leitura_balanca)
        
        # Mostra o dashboard inicial
        self.filtrar_dashboard("Dia")

    # ==========================================================
    # NAVEGAÇÃO E TELAS
    # ==========================================================
    def filtrar_dashboard(self, periodo):
        # 1. Limpa a tela antes de mostrar o novo conteúdo
        self.view.limpar_container()
        
        self.view.pagina_dashboard = DashboardView(self.view.container_principal, self)
        self.view.pagina_dashboard.pack(fill="both", expand=True)

        # 3. Agora busca os dados e renderiza
        dados = self.venda_model.buscar_vendas_por_periodo(periodo) 
        self.view.pagina_dashboard.renderizar_grafico(dados, periodo)



    def exibir_pdv(self):
        print(f"DEBUG: exibir_pdv chamado. Venda em curso: {self.venda_ctrl.venda_atual}")
        """Usa as funções que já existem no seu ProdutoController"""
        self.view.limpar_container()
        
        from app.views.pages.pdv_view import PdvView
        self.pagina_pdv = PdvView(self.view.container_principal, self)
        self.pagina_pdv.pack(fill="both", expand=True)
        self.view.pagina_pdv = self.pagina_pdv

        caixa_realmente_aberto = self.caixa_model.verificar_status_caixa()
        
        # --- O PONTO CHAVE ESTÁ AQUI ---
        # Verificamos se existe uma "venda em curso". 
        # Se o carrinho estiver resetado (ex: None), significa que não iniciamos o cupom ainda.
        venda_em_curso = hasattr(self.venda_ctrl, 'venda_atual') and self.venda_ctrl.venda_atual is not None

        if caixa_realmente_aberto and venda_em_curso:
            # 1. Desenha a estrutura (input de busca, carrinho, etc)
            tab_categorias = self.pagina_pdv.desenhar_estrutura_pdv(
                callback_busca=self.produto_ctrl.executar_busca_pdv,
                callback_pagar=self.abrir_finalizar_venda
            )
            
            print("DEBUG: Preenchendo visual do carrinho importado...")
            self.venda_ctrl.atualizar_visual_carrinho()
            # 2. Obtém produtos
            produtos = self.produto_ctrl.listar_produtos_atalho()
            
            # 3. RENDERIZA OS BOTÕES
            self.pagina_pdv.renderizar_grade_produtos(
                tab_categorias, 
                produtos,
                self.venda_ctrl.adicionar_item_ao_carrinho
            )
        else:
            # --- TELA DE ESPERA ---
            # Se o caixa está aberto mas não tem venda, ele cai aqui.
            # Se o caixa está fechado, também cai aqui.
            nome_usuario = self.usuario if isinstance(self.usuario, str) else self.usuario.get('nome', 'Sistema')
            
            status_atual = "ABERTO" if caixa_realmente_aberto else "FECHADO"

            self.pagina_pdv.desenhar_espera_pdv(
                usuario=nome_usuario,
                status_caixa=status_atual,
                callback_iniciar=self.iniciar_novo_cupom, # Esta função já deve setar a venda_atual
                callback_abrir_caixa=self.caixa_ctrl.solicitar_abertura_caixa 
            )



    def exibir_pdv_espera(self):
        """Força o PDV a voltar para a tela de 'Iniciar Cupom'"""
        self.venda_ctrl.limpar_venda() # Isso seta venda_atual para None
        self.exibir_pdv() # Isso desenha a tela de espera automaticamente



    def abrir_configuracoes(self):
        """Abre a tela de Hardware e Produtos que você criou na View"""
        # Porta padrão para não dar erro ao carregar a tela
        porta_atual = "COM1" 
        
        # Chama o desenho da tela que está na sua GestaoView
        self.view.desenhar_tela_configuracoes(
            porta_atual=porta_atual,
            callback_salvar=self.salvar_configuracoes_gerais
        )



    def salvar_configuracoes_gerais(self, dados):
        """Salva configurações básicas (porta da balança etc.)."""
        try:
            # Ex.: {'porta_balanca': 'COM3'}
            porta = dados.get('porta_balanca')
            if porta:
                self.balanca_model.porta_balanca = porta
                # Reconfigure hardware se necessário
                try:
                    self.hardware.reconfigurar_porta_balanca(porta)
                except Exception:
                    # Se HardwareService não tiver esse método, ignore
                    pass
            messagebox.showinfo("Sucesso", "Configurações salvas.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar as configurações: {e}")
    # ==========================================================
    # PDV E COMANDAS
    # ==========================================================
    def iniciar_novo_cupom(self):
        """Inicia uma nova venda, desenhando a estrutura completa do PDV e populando os produtos"""
        
        # 1. Validação de segurança: o caixa precisa estar aberto
        if not self.caixa_model.verificar_status_caixa():
            messagebox.showwarning("Caixa Fechado", "Realize a abertura primeiro.")
            self.exibir_pdv()
            return

        # --- AQUI ESTÁ A CHAVE DA TRAVA ---
        # Marcamos que agora existe uma venda ativa para o sistema bloquear o menu lateral
        self.venda_ctrl.venda_atual = True 

        from app.views.pages.pdv_view import PdvView
        self.view.limpar_container()
        self.pagina_pdv = PdvView(self.view.container_principal, self)
        self.pagina_pdv.pack(fill="both", expand=True)

        self.view.pagina_pdv = self.pagina_pdv
        
        # 2. Desenha a estrutura da tela (Carrinho + Busca + Categorias)
        tab_categorias = self.pagina_pdv.desenhar_estrutura_pdv(
            callback_busca=self.produto_ctrl.executar_busca_pdv, 
            callback_pagar=self.abrir_finalizar_venda
        )

        # 4. Lógica de dados: se for venda nova (não edição de comanda), limpa o carrinho
        if not self.comanda_em_edicao:
            self.venda_ctrl.limpar_venda()
            # Após o limpar_venda, precisamos reativar o venda_atual, 
            # pois o limpar_venda costuma setar como None
            self.venda_ctrl.venda_atual = True
        
        # 5. Renderiza os botões de produtos nas abas do PDV
        self.produto_ctrl.renderizar_grade(
            tab_categorias,
            callback_item=self.venda_ctrl.adicionar_item_ao_carrinho
        )
        
        # 6. Atualiza labels e estados dos botões
        self.configurar_botao_por_contexto()
        
        # 7. Garante que o foco visual volte para o campo de busca
        if self.pagina_pdv.ent_busca_pdv:
            self.pagina_pdv.ent_busca_pdv.focus()



    def configurar_botao_por_contexto(self):
        """Muda a aparência do botão de ação do PDV conforme o modo de venda"""
        try:
            # 1. Primeiro tentamos pegar a página do PDV
            pagina_pdv = getattr(self, 'pagina_pdv', None)
            if not pagina_pdv:
                return

            # 2. Buscamos o botão dentro da página do PDV (agora chamado de btn_pagar)
            btn = getattr(pagina_pdv, 'btn_pagar', None)

            # 3. Se o botão existir fisicamente na tela
            if btn and btn.winfo_exists(): 
                if self.modo_pagamento_comanda:
                    # Caso esteja finalizando uma comanda existente
                    btn.configure(
                        text="PAGAR COMANDA (F12)",
                        fg_color="#2fa572", # Verde esmeralda (sua cor original)
                        hover_color="#248259"
                    )
                else:
                    # Caso seja uma venda avulsa comum
                    btn.configure(
                        text="PAGAR AGORA (F12)",
                        fg_color="#1f538d", # Azul padrão
                        hover_color="#14375e"
                    )
        except Exception as e:
            print(f"DEBUG: Botão de contexto não disponível ({e})")



    def remover_item_comanda(self, index):
        """Ponte para o ComandaController remover o item"""
        self.comanda_ctrl.remover_item_comanda(index)



    def exibir_comandas_pendentes(self):
        # 1. Cria a tela e guarda na VIEW (para o ComandaController encontrar)
        self.view.view_comandas = self.view.desenhar_tela_comandas()
        
        # 2. Guarda também no CONTROLLER (para redundância)
        self.view_comandas = self.view.view_comandas
        
        # 3. Manda o especialista atualizar
        self.comanda_ctrl.atualizar_visual_comandas()



    def solicitar_nova_comanda(self):
        """Redireciona o pedido da View para o especialista em comandas"""
        self.comanda_ctrl.nova_comanda()




    def abrir_modal_comanda(self, id_comanda, dados):
        """Abre a janela pop-up de gerenciamento e guarda a referência"""
        from app.views.popups.comanda_modal_view import ComandaModalView
        
        # Guardamos a instância na variável que o sistema já espera
        self.modal_comanda = ComandaModalView(self.view, id_comanda, dados, self)

        self.comanda_ctrl.modal_comanda = self.modal_comanda



    def finalizar_comanda(self, id_comanda):
        """Função que recebe o ID e prepara o PDV para pagamento"""
        try:
            # --- O AJUSTE ESTÁ AQUI ---
            # Trocamos 'self.comanda_service' por 'self.comanda_ctrl'
            comanda_db = self.comanda_ctrl.get_comanda_por_id(id_comanda) 
            
            if not comanda_db:
                print("Erro: Comanda não encontrada no banco.")
                return

            # 1. Alimenta o controlador de venda (Cérebro)
            self.venda_ctrl.venda_atual = True 
            self.venda_ctrl.carrinho = comanda_db['itens']
            self.venda_ctrl.comanda_id_atual = id_comanda

            # 2. Muda para a tela do PDV (Interface)
            # Isso vai disparar o seu 'exibir_pdv' que já configuramos
            self.exibir_pdv()
            print(f"Comanda importada no PDV par pagamento{id_comanda}")
        except Exception as e:
            print(f"Erro ao importar comanda para o PDV: {e}")

    # ADICIONE ESTA FUNÇÃO NO GESTAO_CONTROLLER TAMBÉM:
    def cancelar_comanda_total(self, id_comanda, modal_window):
        """Atalho que repassa para o ComandaController fazer a exclusão real"""
        return self.comanda_ctrl.cancelar_comanda_total(id_comanda, modal_window)

    def imprimir_extrato_comanda(self, id_comanda):
        """Lógica para enviar para a impressora térmica (vazio por enquanto)"""
        print(f"Enviando extrato da Comanda {id_comanda} para impressora...")
        messagebox.showinfo("Impressão", f"Extrato da Comanda {id_comanda} enviado!")




    def lancar_comanda(self, comanda, index):
        """Carrega a comanda no PDV. Usa finalizar_comanda de forma unificada."""
        # tenta extrair id da comanda (vindo do view)
        id_comanda = None
        if isinstance(comanda, dict):
            id_comanda = comanda.get('id') or comanda.get('codigo') or comanda.get('numero')
        if id_comanda is None:
            # fallback por índice (quando a lista for ordenada)
            try:
                keys = list(self.comanda_ctrl.comandas_abertas.keys())
                id_comanda = keys[index] if index is not None and index < len(keys) else None
            except Exception:
                id_comanda = None

        if id_comanda:
            self.finalizar_comanda(id_comanda)
        else:
            messagebox.showerror("Erro", "Não foi possível identificar a comanda para lançar.")



    def abrir_finalizar_venda(self):
        """Gatilho do botão principal do PDV: Decide o fluxo."""
        if not self.venda_ctrl.carrinho:
            messagebox.showwarning("Aviso", "O carrinho está vazio!")
            return

        total_venda = sum(item['total'] for item in self.venda_ctrl.carrinho)
        

        # 1. CASO: COMANDA
        if self.comanda_em_edicao:
            id_id = self.comanda_em_edicao
            msg = f"Deseja FINALIZAR O PAGAMENTO da comanda {id_id}?\n(Clique 'Não' para apenas salvar os itens na conta)"
            
            escolha = messagebox.askyesnocancel("Ação de Comanda", msg)

            if escolha is True: # Escolheu Finalizar/Pagar agora
                self._abrir_modal_pagamento(total_venda)
            elif escolha is False: # Escolheu apenas Salvar/Adicionar itens
                self._salvar_itens_na_comanda(id_id)
            return

        # 2. CASO: VENDA DIRETA
        else:
            self._abrir_modal_pagamento(total_venda)



    def renderizar_botoes_produtos_modal(self, tabview, callback_item):
        """
        Ponte para renderizar a grade de produtos dentro do modal de comandas.
        """
        # Chamamos o especialista em produtos para desenhar na aba do modal
        self.produto_ctrl.renderizar_grade(
            tabview=tabview, 
            callback_item=callback_item
        )



    def _salvar_itens_na_comanda(self, id_id):
        """Atualiza a comanda no dicionário e volta para a grade."""
        self.comanda_ctrl.comandas_abertas[id_id]['itens'] = self.venda_ctrl.carrinho.copy()
        self.comanda_ctrl.comandas_abertas[id_id]['total'] = sum(item['total'] for item in self.venda_ctrl.carrinho)
        
        self.comanda_em_edicao = None
        self.venda_ctrl.carrinho = []
        messagebox.showinfo("Sucesso", f"Comanda {id_id} atualizada!")
        self.exibir_comandas_pendentes()



    def _abrir_modal_pagamento(self, total):
        """Apenas abre a janela. A lógica de fechar o banco fica no 'finalizar_venda_db'."""
        from app.views.popups.pagamento_modal_view import PagamentoModalView
        self.modal_pgto = PagamentoModalView(self.view, total, controller=self.venda_ctrl)



    def finalizar_venda_db(self, total, forma, modal_pgto):
        # 1. Recupera a sessão persistente do banco
        # Importante: self.sessao_atual deve ter sido carregada no verificar_caixa_no_inicio
        sessao_id = self.sessao_atual['id'] if hasattr(self, 'sessao_atual') else None
        
        if not sessao_id:
            messagebox.showerror("Erro Crítico", "Sessão de caixa não encontrada! Reabra o caixa para continuar.")
            return

        # 2. Pega o ID do cliente se houver um selecionado
        cliente_id = getattr(self.venda_ctrl, 'cliente_atual_venda', {}).get('id')

        # 3. Salva a venda (SQL + JSON)
        # Mudamos para 'registrar_venda' pois é o nome que está no seu VendaModel
        venda_id = self.venda_model.registrar_venda(
            carrinho=self.venda_ctrl.carrinho,
            total=total,
            forma_pagamento=forma,
            usuario=self.usuario_logado, # Campo obrigatório no seu Model
            sessao_id=sessao_id,
            cliente_id=cliente_id
        )
        
        if venda_id:
            # 4. Limpa comanda se a venda veio de uma
            if self.comanda_em_edicao:
                self.comanda_ctrl.comandas_abertas.pop(self.comanda_em_edicao, None)

            # 5. Limpeza de interface e memória
            self.venda_ctrl.limpar_venda()
            
            # Se você usa essa variável no venda_ctrl, limpamos ela aqui
            if hasattr(self.venda_ctrl, 'cliente_atual_venda'):
                self.venda_ctrl.cliente_atual_venda = None 
                
            self.comanda_em_edicao = None
            
            if modal_pgto:
                modal_pgto.destroy()
            
            messagebox.showinfo("Sucesso", f"Venda {venda_id} Finalizada!")
            self.exibir_pdv()
        else:
            messagebox.showerror("Erro", "Falha ao gravar venda. Verifique o log do sistema.")



    def finalizar_fechamento_caixa(self, dados_conferencia):
        try:
            resumo = self.caixa_model.obter_resumo_caixa(self.caixa_model.sessao_id)
            d = resumo['detalhado']

            texto = (
                f"--- FECHAMENTO DETALHADO ---\n\n"
                f"💰 ABERTURA: R$ {resumo['abertura']:.2f}\n"
                f"➕ REFORÇOS: R$ {resumo['reforcos']:.2f}\n"
                f"➖ SANGRIAS: R$ {resumo['sangrias']:.2f}\n"
                f"💵 DINHEIRO EM ESPÉCIE: R$ {d['Dinheiro']:.2f}\n"
                f"---------------------------------\n"
                f"📊 SALDO FINAL GAVETA: R$ {resumo['saldo_gaveta']:.2f}\n\n"
                f"--- OUTROS MÉTODOS ---\n"
                f"📱 PIX: R$ {d['Pix']:.2f}\n"
                f"💳 CRÉDITO: R$ {d['Crédito']:.2f}\n"
                f"💳 DÉBITO: R$ {d['Débito']:.2f}\n"
                f"🥗 VALE REFEIÇÃO (VR): R$ {d['Vale Refeição']:.2f}\n"
                f"🛒 VALE ALIMENTAÇÃO (VA): R$ {d['Vale Alimentação']:.2f}\n"
                f"📝 CREDIÁRIO: R$ {d['Crediário']:.2f}\n"
                f"---------------------------------\n"
                f"🚀 FATURAMENTO TOTAL: R$ {resumo['faturamento']:.2f}\n\n"
                f"Confirmar encerramento do caixa?"
            )

            if messagebox.askyesno("Conferência de Caixa", texto):
                self.caixa_model.fechar_caixa()
                # ... resto do código de fechar janelas ...
                messagebox.showinfo("Sucesso", "Caixa encerrado com sucesso!")
                self.exibir_pdv()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao detalhar: {e}")



    def verificar_caixa_aberto(self):
        """
        Verifica se o caixa está aberto no banco de dados.
        Retorna True se aberto, False se fechado (e avisa o usuário).
        """
        status = self.caixa_model.verificar_status_caixa()
        
        if not status:
            messagebox.showwarning("Caixa Fechado", "O caixa precisa estar ABERTO para gerenciar comandas.")
            return False
        return True



    def gerenciar_comanda(self, id_comanda):
        # 1. Busca os dados da comanda no banco
        comanda = self.db.fetch_one("SELECT * FROM comandas WHERE id = ?", (id_comanda,))
        
        if comanda:
            # 2. Busca os ITENS vinculados a essa comanda
            # Ajuste 'itens_comanda' para o nome real da sua tabela de produtos da comanda
            query_itens = """
            SELECT nome_produto as nome, quantidade as qtd, 
                   preco_unitario as preco_unit, total_item as total 
            FROM comandas_itens 
            WHERE comanda_id = ?
        """
            itens_db = self.db.fetch_all(query_itens, (id_comanda,))
            
            # 3. Monta o dicionário completo
            dados_modal = dict(comanda) # Converte para dicionário
            dados_modal['itens'] = itens_db if itens_db else [] # Adiciona a lista de itens (mesmo que vazia)
            
            # 4. Abre o modal com os dados carregados
            self.modal_comanda = ComandaModalView(self.view, id_comanda, dados_modal, self)
            self.comanda_ctrl.modal_comanda = self.modal_comanda
        else:
            messagebox.showerror("Erro", "Não foi possível carregar os dados da comanda.")
        


    def salvar_dados_comanda_direto(self, id_comanda, dados, modal_window=None, imprimir=True):
        """
        Salva os dados da comanda.
        imprimir=True: Comportamento padrão (botão Salvar).
        imprimir=False: Não pergunta sobre impressão (usado pelo botão Pagar).
        """
        try:
            print(f"DEBUG: Iniciando salvamento completo da comanda {id_comanda}. Imprimir={imprimir}")

            # 1. MAPEAMENTO DE DADOS
            nome_cli = str(dados.get('nome') or dados.get('cliente_nome_temp') or "").upper()
            end_cli  = str(dados.get('endereco') or dados.get('endereco_entrega') or "").upper()
            tel_cli  = str(dados.get('telefone') or dados.get('telefone_temp') or "")
            forma_p  = str(dados.get('forma_pagamento') or dados.get('forma_pagamento_entrega') or "NÃO INFORMADO").upper()
            troco_p  = dados.get('troco_para', 0)
            categ    = str(dados.get('categoria') or "DELIVERY").upper()
            status_novo = str(dados.get('status') or "ABERTO").upper() 

            # 2. RECUPERA ITENS DA TELA (Do Modal)
            itens_da_tela = []
            # Tenta pegar os dados diretamente do argumento 'dados' primeiro
            if 'itens' in dados and dados['itens']:
                itens_da_tela = dados['itens']
            # Fallback para pegar do controller se não vier no argumento
            elif hasattr(self.comanda_ctrl, 'modal_comanda') and self.comanda_ctrl.modal_comanda:
                itens_da_tela = self.comanda_ctrl.modal_comanda.dados.get('itens', [])
            
            # Recalcula total baseado no que está na tela
            total_v = sum(float(i.get('total', 0)) for i in itens_da_tela)

            # ==============================================================================
            # PARTE 1: ATUALIZA O CABEÇALHO
            # ==============================================================================
            self.db.execute(
                """UPDATE comandas SET 
                   status = ?, 
                   categoria = ?, 
                   cliente_nome_temp = ?, 
                   endereco_entrega = ?, 
                   telefone_temp = ?, 
                   troco_para = ?, 
                   forma_pagamento_entrega = ?, 
                   total = ?
                   WHERE id = ?""",
                (status_novo, categ, nome_cli, end_cli, tel_cli, troco_p, forma_p, total_v, id_comanda)
            )

            # ==============================================================================
            # PARTE 2: ATUALIZA OS ITENS
            # ==============================================================================
            self.db.execute("DELETE FROM comandas_itens WHERE comanda_id = ?", (id_comanda,))

            query_item = """
                INSERT INTO comandas_itens 
                (comanda_id, produto_id, nome_produto, quantidade, preco_unitario, total_item, observacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            for item in itens_da_tela:
                preco = float(
                item.get('preco_unit') or 
                item.get('preco_unitario') or 
                item.get('preco') or 
                item.get('preco_venda') or 
                0.0
            )
            
            # Tenta pegar a quantidade
            qtd = float(item.get('qtd') or item.get('quantidade') or 1.0)

            # Recalcula o total se ele estiver zerado ou ausente
            tot_item_cru = item.get('total') or item.get('total_item') or 0.0
            tot_item = float(tot_item_cru)
            
            if tot_item <= 0 and preco > 0:
                tot_item = preco * qtd
            
            # Executa o INSERT garantindo que 'preco' não é zero (se o produto tiver preço)
            self.db.execute(query_item, (
                id_comanda,
                item.get('produto_id'), 
                item.get('nome'),
                qtd,
                preco,    # <--- Agora garantimos que pegou o valor certo
                tot_item, 
                item.get('observacao', '')
            ))

            if hasattr(self.db, 'conn') and self.db.conn:
                self.db.conn.commit()
            
            print(f"DEBUG: Comanda {id_comanda} salva com {len(itens_da_tela)} itens.")

            # ==============================================================================
            # PARTE 3: IMPRESSÃO (Controlada pelo flag imprimir)
            # ==============================================================================
            if imprimir:
                dados_impressao = {
                    'id': id_comanda,
                    'total': total_v,
                    'categoria': categ,
                    'itens': itens_da_tela,
                    'troco_para': troco_p,
                    'forma_pagamento': forma_p,
                    'nome': nome_cli if nome_cli else "CLIENTE NÃO INFORMADO",
                    'endereco': end_cli if end_cli else "RETIRADA NO BALCÃO",
                    'telefone': tel_cli
                }

                if total_v > 0:
                    if messagebox.askyesno("Etiquetas", "Deseja imprimir as etiquetas?"):
                        # Verifique se no seu GestaoController o serviço é self.impressora ou self.impressao_service
                        service = getattr(self, 'impressora', getattr(self, 'impressao_service', None))
                        
                        if service:
                            service.imprimir_etiquetas_itens(id_comanda, dados_impressao)
                            service.imprimir_via_motoboy(id_comanda, dados_impressao)
                        else:
                            print("AVISO: Serviço de impressão não encontrado no GestaoController")

            # Fecha Modal e Atualiza Tela de Fundo
            if modal_window:
                modal_window.destroy()
            
            if hasattr(self, 'comanda_ctrl'):
                self.comanda_ctrl.atualizar_visual_comandas()

        except Exception as e:
            print(f"ERRO CRÍTICO NO SALVAMENTO: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro ao Salvar", f"Falha: {e}")

    def salvar_edicao_comanda(self, id_id):
            """Salva os itens que estão no carrinho do PDV de volta para a comanda"""
            try:
                # 1. Pega os itens que estão no VendaController (o novo dono do carrinho)
                itens_do_carrinho = self.venda_ctrl.carrinho.copy()
                
                # 2. Salva no ComandaController (o novo dono do dicionário)
                self.comanda_ctrl.comandas_abertas[id_id]['itens'] = itens_do_carrinho
                
                # 3. Recalcula o total da comanda
                novo_total = sum(item['total'] for item in itens_do_carrinho)
                self.comanda_ctrl.comandas_abertas[id_id]['total'] = novo_total
                
                messagebox.showinfo("Sucesso", f"Alterações da comanda {id_id} salvas!")
                
                # 4. Limpa o PDV e volta para a tela de comandas
                self.comanda_em_edicao = None
                self.venda_ctrl.limpar_venda()
                self.exibir_comandas_pendentes()
                self.configurar_botao_por_contexto()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar a comanda: {e}")


    


    # No seu GestaoController.py

    # ... dentro da classe GestaoController ...

    def desenhar_linha_comanda_modal(self, container, idx, item):
        """Chama o componente visual da PdvView conectando os eventos do Modal"""
        # Importação local para evitar ciclo de importação
        from app.views.pages.pdv_view import PdvView
        import customtkinter as ctk # Garanta que ctk está importado
        
        def acao_editar_obs():
            # --- LÓGICA ANTI-TRAVAMENTO (GRAB RELEASE) ---
            modal_pai = None
            
            # Procura o modal aberto na view principal
            for child in self.view.winfo_children():
                if isinstance(child, ctk.CTkToplevel):
                    modal_pai = child
                    break
            
            # Libera o foco temporariamente
            if modal_pai:
                modal_pai.grab_release()

            # Abre o diálogo
            dialogo = ctk.CTkInputDialog(
                text=f"Observação para {item['nome']}:", 
                title="Editar Observação"
            )
            
            # Centraliza o diálogo (opcional, ajuda na UX)
            dialogo.geometry(f"+{self.view.winfo_rootx()+50}+{self.view.winfo_rooty()+50}")
            
            texto_obs = dialogo.get_input()
            
            # Retoma o foco para o modal (Independente se digitou ou cancelou)
            if modal_pai:
                modal_pai.grab_set()
                modal_pai.lift() # Traz para frente de novo

            # Se digitou algo, salva
            if texto_obs is not None:
                # Chama a função que criamos no ComandaController
                self.comanda_ctrl.definir_obs_item(idx, texto_obs)
                
                # Atualiza a tela
                if modal_pai and hasattr(modal_pai, 'atualizar_lista_itens'):
                    modal_pai.atualizar_lista_itens()

        # Renderiza a linha usando o componente visual padrão
        PdvView.criar_linha_carrinho(
            item=item,
            cb_mais=lambda: self.alterar_qtd_comanda(idx, 1),
            cb_menos=lambda: self.alterar_qtd_comanda(idx, -1),
            cb_remover=lambda: self.remover_item_comanda(idx),
            cb_manual=lambda valor: self.comanda_ctrl.definir_qtd_manual_comanda(idx, valor),
            cb_obs=acao_editar_obs, 
            container_pai=container 
        )



    def alterar_qtd_comanda(self, index, delta):
        """Repassa a alteração de quantidade para o controller especialista"""
        if hasattr(self, 'modal_comanda'):
            # Garante que o ComandaController tenha a referência atualizada do modal
            self.comanda_ctrl.modal_comanda = self.modal_comanda
            self.comanda_ctrl.alterar_qtd_comanda(index, delta)



    def solicitar_exclusao_venda(self, venda):
        # 1. Pede a senha primeiro
        senha_dialog = ctk.CTkInputDialog(text="Digite a senha de GERENTE:", title="Autorização")
        senha = senha_dialog.get_input()

        if senha == "123":
            # 2. Confirma a intenção
            if messagebox.askyesno("Confirmar", f"Deseja excluir a venda de R$ {venda['total']:.2f}?"):
                
                # 3. Chama o Model para remover
                sucesso = self.caixa_model.cancelar_venda(venda)
                
                if sucesso:
                    messagebox.showinfo("Sucesso", "Venda excluída!")
                    
                    # --- O PULO DO GATO ESTÁ AQUI ---
                    # 4. Pegamos os dados ATUALIZADOS do Model
                    resumo_novo = self.caixa_model.obter_resumo_caixa()
                    vendas_e_mov_novas = self.caixa_model.obter_vendas_dia() + self.caixa_model.obter_movimentacoes_dia()
                    
                    # 5. Ordenamos a lista novamente (opcional, mas recomendado)
                    vendas_e_mov_novas.sort(key=lambda x: x['hora'], reverse=True)

                    # 6. Avisamos a View existente para se atualizar, em vez de criar uma nova
                    if hasattr(self.main, 'janela_gestao') and self.main.janela_gestao:
                        self.main.janela_gestao.atualizar_resumo_tela(resumo_novo)
                        self.main.janela_gestao.atualizar_lista_vendas(vendas_e_mov_novas)
                    
                else:
                    messagebox.showerror("Erro", "Não foi possível localizar a venda no sistema.")
        else:
            if senha is not None: 
                messagebox.showerror("Erro", "Senha incorreta!")



    def processar_busca_pdv(self, codigo):
        """
        Processa a busca do PDV (Produto ou Comanda).
        Recebe 'codigo' diretamente do evento <Return>, evitando erro de leitura de widget.
        """
        if not codigo: 
            return
            
        codigo = codigo.strip()
        
        # 1. Tenta buscar PRODUTO
        # Agora self.produto_service está garantido pelo __init__
        produto = self.produto_service.buscar_por_codigo_ou_nome(codigo)
        
        if produto:
            # Se achou, manda para o VendaController adicionar
            self.venda_ctrl.adicionar_item_ao_carrinho(
                produto['nome'], 1, produto['preco'], produto['id']
            )
            self._limpar_campo_busca_pdv()
            return

        # 2. Se não achou produto e é numérico -> Tenta importar COMANDA
        if codigo.isdigit():
            id_comanda = int(codigo)
            print(f"Tentando importar comanda ID: {id_comanda}")
            
            # Manda o VendaController importar
            self.venda_ctrl.importar_comanda(id_comanda)
            
            self._limpar_campo_busca_pdv()
        else:
            from tkinter import messagebox
            messagebox.showwarning("Não encontrado", "Produto ou Comanda não localizados.")
            self._limpar_campo_busca_pdv()

    def _limpar_campo_busca_pdv(self):
        """Limpa o campo de busca sem causar erro se a tela mudou"""
        try:
            # Tenta acessar via pdv_view se existir na view principal
            if hasattr(self.view, 'pdv_view') and self.view.pdv_view:
                self.view.pdv_view.ent_busca_pdv.delete(0, 'end')
            # Ou tenta acessar diretamente se a view atual tiver esse atributo
            elif hasattr(self.view, 'ent_busca_pdv'):
                self.view.ent_busca_pdv.delete(0, 'end')
        except Exception:
            pass # Se não der pra limpar, apenas ignora

    def _limpar_campo_busca_pdv(self):
        """Função auxiliar segura para limpar o campo de busca"""
        try:
            # Tenta acessar via pdv_view se existir
            if hasattr(self.view, 'pdv_view') and self.view.pdv_view:
                self.view.pdv_view.ent_busca_pdv.delete(0, 'end')
            # Ou tenta acessar diretamente se a view for o próprio PDV
            elif hasattr(self.view, 'ent_busca_pdv'):
                self.view.ent_busca_pdv.delete(0, 'end')
        except Exception as e:
            print(f"Erro menor ao limpar campo: {e}")



    def salvar_produto_no_banco(self, dados):
        """Interface entre a View de Cadastro e o Controller de Produtos"""
        if self.produto_service:
            # Chama o serviço especializado em produtos
            sucesso, mensagem = self.produto_service.cadastrar_produto(dados)
            if sucesso:
                # Se salvou um atalho, manda o PDV atualizar os botões na hora
                self.atualizar_atalhos_no_pdv()
                return True
            else:
                print(f"Erro ao salvar: {mensagem}")
                return False
        return False



    def atualizar_atalhos_no_pdv(self):
        """Força o PDV a reler o banco de dados e desenhar os novos botões"""
        if self.produto_service:
            atalhos_atualizados = self.produto_service.listar_atalhos()
            # Se você estiver na tela do PDV, ele redesenha
            if hasattr(self.view, 'tabview_categorias'): # Verifique o nome do seu container de botões
                 self.renderizar_botoes_produtos(self.view.tabview_categorias)



    def renderizar_botoes_produtos(self, tabview=None):
        """Redesenha os atalhos do PDV (grade de produtos)."""
        if tabview is None:
            tabview = getattr(self.view, 'tabview_categorias', None)
        if not tabview:
            return
        if hasattr(self.produto_ctrl, 'renderizar_grade'):
            try:
                self.produto_ctrl.renderizar_grade(
                    tabview,
                    callback_item=getattr(self.venda_ctrl, 'adicionar_item_ao_carrinho', None)
                )
            except Exception as e:
                print(f"Aviso: não foi possível renderizar atalhos do PDV: {e}")

        # Funções de redirecionamento para o Caixa
   
   

    def abrir_gestao(self):
        if not self.verificar_caixa_aberto():
            return
        
        # IMPORTANTE: Pegamos o ID da sessão persistente que o GestaoController recuperou
        sessao_id = self.main.sessao_atual['id'] if hasattr(self.main, 'sessao_atual') else None
        
        if sessao_id:
            # Buscamos direto do Banco de Dados, ignorando as listas vazias da memória
            vendas = self.caixa_model.obter_vendas_dia_db(sessao_id)
            movs = self.caixa_model.obter_movimentacoes_dia_db(sessao_id)
            
            # O resumo também deve ser recalculado com base no banco
            resumo = self.caixa_model.obter_resumo_caixa_db(sessao_id)
        else:
            # Fallback caso algo falhe
            vendas = []
            movs = []
            resumo = self.caixa_model.obter_resumo_caixa()

        lista = (vendas + movs)
        lista.sort(key=lambda x: x.get('hora', '00:00'), reverse=True)
        
        from app.views.popups.gestao_caixa_view import GestaoCaixaView
        self.main.janela_gestao = GestaoCaixaView(
            master=self.view,
            controller=self, 
            dados_vendas=lista,
            resumo=resumo
        )



    def acionar_sangria(self):
        self.caixa_ctrl.abrir_modal_movimentacao("SANGRIA")



    def acionar_reforco(self):
        self.caixa_ctrl.abrir_modal_movimentacao("REFORÇO")



    def exibir_abertura_caixa(self):
        self.caixa_ctrl.mostrar_tela_abertura_caixa()



    def mostrar_tela_abertura_caixa(self):
    # Em vez de ter a lógica aqui, delega para o especialista
        self.caixa_ctrl.abrir_modal_abertura()



    def processar_salvamento_produto(self, dados):
        """Recebe os dados da View e utiliza o ProdutoController para salvar"""
        
        # 1. Tratamento básico de tipos (converte strings da View para números)
        try:
            # Criamos o dicionário que o ProdutoController/Database espera
            dados_formatados = {
                'ean': dados.get('ean'),
                'nome': dados.get('nome').upper() if dados.get('nome') else "",
                'preco_venda': float(dados.get('preco_venda') or 0),
                'preco_custo': float(dados.get('preco_custo') or 0),
                'categoria': dados.get('categoria'),
                'exibir_atalho': 1 if dados.get('exibir_atalho') else 0,
                'tipo': dados.get('tipo'),
                'unidade': dados.get('unidade'),
                'codigo_interno': dados.get('codigo_interno'),
                'codigo_balanca': dados.get('codigo_balanca'),
                'estoque_min': float(dados.get('estoque_min') or 0),
                'estoque_max': float(dados.get('estoque_max') or 0),
                'controlar_estoque': 1 if dados.get('controlar_estoque') else 0,
                'ncm': dados.get('ncm'),
                'cest': dados.get('cest'),
                'origem': dados.get('origem'),
                'classificacao': dados.get('classificacao')
            }

            # 2. Chama o ProdutoController (ele já tem o self.db configurado)
            # O self.produto_ctrl é quem deve gerenciar isso
            sucesso, mensagem = self.produto_ctrl.cadastrar_produto(dados_formatados)

            if sucesso:
                messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")
                self.exibir_pdv() # Volta para o PDV para ver o produto novo
            else:
                messagebox.showerror("Erro", f"Falha ao salvar: {mensagem}")

        except ValueError:
            messagebox.showerror("Erro de Digitação", "Preços e Estoque devem ser números válidos.")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro: {e}")

    

    def exibir_cadastros(self):
        """Abre a tela de gerenciamento de produtos"""
        print("Abrindo tela de cadastros...")
        from app.views.pages.cadastro_produto_view import CadastroProdutoView
        
        self.view.limpar_container()
        # Instancia a página e guarda a referência
        self.pagina_cadastro = CadastroProdutoView(self.view.container_principal, self)
        self.pagina_cadastro.pack(fill="both", expand=True)



    def listar_todos_produtos(self):
        """Busca os produtos e decide se abre uma nova janela ou apenas atualiza a atual"""
        try:
            query = "SELECT * FROM produtos ORDER BY nome ASC"
            produtos = self.produto_ctrl.db.fetch_all(query)
            
            # Se a janela já existe e não foi fechada (está 'winfo_exists')
            if hasattr(self, 'popup_lista') and self.popup_lista.winfo_exists():
                self.popup_lista.renderizar_lista(produtos)
                self.popup_lista.focus() # Traz para frente
            else:
                # Se não existe, cria do zero
                from app.views.popups.lista_produtos_view import ListaProdutosView
                self.popup_lista = ListaProdutosView(self.view, self, produtos)
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar lista: {e}")



    def carregar_produto_para_edicao(self, produto):
        """Pega os dados do popup e joga nos campos da tela de cadastro"""
        try:
            # 1. Referência da página de cadastro que está aberta
            pg = self.pagina_cadastro
            
            # 2. Limpa os campos antes de preencher
            pg.ent_nome.delete(0, 'end')
            pg.ent_venda.delete(0, 'end')
            pg.ent_ean.delete(0, 'end')
            pg.ent_cod_interno.delete(0, 'end')
            pg.ent_cod_balanca.delete(0, 'end')
            pg.ent_ncm.delete(0, 'end')
            # ... limpe outros se necessário ...

            # 3. Preenche com os novos dados
            pg.ent_nome.insert(0, produto.get('nome', ''))
            pg.ent_venda.insert(0, str(produto.get('preco', '')))
            pg.ent_ean.insert(0, produto.get('codigo_barras', ''))
            pg.ent_cod_interno.insert(0, produto.get('codigo_interno', '') or '')
            pg.ent_cod_balanca.insert(0, produto.get('codigo_balanca', '') or '')
            pg.ent_ncm.insert(0, produto.get('ncm', '') or '')
            
            # Ajusta os OptionMenus (Categorias, Unidades, etc)
            if hasattr(pg, 'opt_categoria'):
                pg.opt_categoria.set(produto.get('categoria', 'Geral'))
                
            # 4. Fecha o popup automaticamente após carregar
            if hasattr(self, 'popup_lista'):
                self.popup_lista.destroy()
                
            messagebox.showinfo("Edição", f"Produto '{produto['nome']}' carregado para edição.")

        except Exception as e:
            messagebox.showerror("Erro ao carregar", f"Falha ao carregar dados para os campos: {e}")


    def solicitar_exclusao_produto(self, produto):
        """Lógica de exclusão com confirmação"""
        confirmar = messagebox.askyesno("Confirmar Exclusão", f"Deseja realmente excluir o produto:\n{produto['nome']}?")
        if confirmar:
            # Chama a função de excluir que você já tem no ProdutoController
            if self.produto_ctrl.excluir(produto['codigo_barras']):
                messagebox.showinfo("Sucesso", "Produto removido!")
                self.listar_todos_produtos() # Atualiza o popup
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o produto.")




    def obter_todos_produtos_lista(self):
        """Busca a lista completa de produtos no banco para o popup"""
        query = "SELECT * FROM produtos ORDER BY nome ASC"
        
        # Tentativa 1: Se o banco estiver dentro do caixa_model
        if hasattr(self.caixa_model, 'db'):
            return self.caixa_model.db.fetch_all(query)
        
        # Tentativa 2: Se o banco estiver direto no controller
        elif hasattr(self, 'db'):
            return self.db.fetch_all(query)
        
        # Tentativa 3: Se o banco estiver no produto_ctrl (que você já usou antes)
        else:
            return self.produto_ctrl.db.fetch_all(query)



    def filtrar_produtos_popup(self, termo):
        """Filtra a lista no popup enquanto o usuário digita"""
        try:
            # Busca por nome ou por código de barras
            query = """
                SELECT * FROM produtos 
                WHERE nome LIKE ? OR codigo_barras LIKE ? OR codigo_interno LIKE ?
                ORDER BY nome ASC
            """
            params = (f'%{termo}%', f'%{termo}%', f'%{termo}%')
            produtos = self.produto_ctrl.db.fetch_all(query, params)
            
            # Atualiza apenas o conteúdo do scroll sem fechar a janela
            if hasattr(self, 'popup_lista') and self.popup_lista.winfo_exists():
                self.popup_lista.renderizar_lista(produtos)
        except Exception as e:
            print(f"Erro ao filtrar: {e}")

    

    def fazer_logout(self):
        self.hardware.parar() # Para as threads antes de sair
        self.view.destroy()
        sys.exit(0)



    def iniciar(self):
        
        self.view.mainloop()



    def abrir_configuracoes_empresa(self):
        """Abre a tela e já carrega os dados existentes"""
        self.janela_empresa = ConfiguracaoEmpresaView(self.view, self)
        
        # Carrega dados do Banco
        dados_atuais = self.empresa_model.obter_dados()
        
        # Preenche os campos da View
        if dados_atuais:
            for chave, valor in dados_atuais.items():
                if chave in self.janela_empresa.entries and valor:
                    self.janela_empresa.entries[chave].insert(0, str(valor))



    def salvar_dados_empresa(self, dados):
        """Recebe os dados da View e manda para o Model"""
        try:
            if self.empresa_model.salvar_dados(dados):
                messagebox.showinfo("Sucesso", "Dados da empresa atualizados!")
                self.janela_empresa.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")    

    
    def salvar_cliente(self, dados):
        """Prepara os dados e envia para o ClientesModel"""
        try:
            # 1. Captura o documento e limpa (remove . , - /)
            doc_bruto = dados.get('cpf') or dados.get('cnpj') or dados.get('documento')
            
            if not doc_bruto:
                messagebox.showwarning("Atenção", "O CPF/CNPJ é obrigatório!")
                return

            # Mantém apenas os números
            doc_limpo = "".join(filter(str.isdigit, str(doc_bruto)))
            
            # 2. Atualiza o dicionário com o documento limpo e define o tipo se estiver faltando
            dados['documento'] = doc_limpo
            if 'tipo' not in dados:
                dados['tipo'] = 'F' if len(doc_limpo) <= 11 else 'J'

            # 3. Chama o Model
            if self.clientes_model.salvar_cliente(dados):
                messagebox.showinfo("Sucesso", "Cliente salvo com sucesso!")
                # Recarrega a lista na tela
                self.listar_todos_clientes()
            else:
                # Se cair aqui, o erro foi capturado pelo 'except' do Model
                messagebox.showerror("Erro", "Erro ao salvar no Banco de Dados. Verifique o console.")

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha no Controller: {e}")

            

    def atualizar_lista_clientes(self, busca=""):
        clientes = self.clientes_model.listar_clientes(busca)
        # Aqui você chamaria um método na View para renderizar os cards dos clientes
        self.view.renderizar_lista(clientes)


    def listar_todos_clientes(self):
        """Busca todos os clientes e solicita que a View os mostre."""
        try:
            clientes = self.clientes_model.listar_clientes()
            
            # Verifica se a página de clientes está instanciada
            if hasattr(self, 'pagina_clientes'):
                self.pagina_clientes.renderizar_lista(clientes)
            else:
                print("Página de clientes não encontrada.")
        except Exception as e:
            print(f"Erro ao listar clientes: {e}")

    def inicializar_cards_clientes(self):
        
        try:
            from app.views.pages.clientes_view import ClientesView
            self.view.limpar_container()

            self.pagina_clientes = ClientesView(self.view.container_principal, self)
            self.pagina_clientes.pack(fill="both", expand=True)
            
            self.pagina_clientes.exibir_escolha_inicial()
            
            print("MVC: Página de clientes inicializada via Controller.")
        except Exception as e:
            print(f"Erro ao inicializar página de clientes: {e}")

    def reimprimir_comprovante(self, venda_id):
        """Reimprime o cupom de uma venda antiga baseada no ID"""
        if not venda_id:
            messagebox.showwarning("Aviso", "Esta movimentação não possui comprovante vinculado.")
            return

        if not messagebox.askyesno("Reimpressão", "Deseja reimprimir o comprovante desta venda?"):
            return

        try:
            print(f"DEBUG: Iniciando reimpressão da venda {venda_id}...")
            
            # 1. Busca os dados da VENDA (Total, Data, Cliente ID)
            # Você precisará garantir que tem um método para buscar venda por ID no VendaModel
            # Se não tiver, podemos fazer uma query direta aqui ou adicionar no model.
            # Vou assumir que você pode usar o db_manager direto ou o model:
            
            query_venda = "SELECT * FROM vendas WHERE id = ?"
            dados_venda = self.caixa_model.db.fetch_one(query_venda, (venda_id,))
            
            if not dados_venda:
                messagebox.showerror("Erro", "Venda original não encontrada.")
                return

            # 2. Busca os ITENS da venda
            query_itens = "SELECT * FROM vendas_itens WHERE venda_id = ?"
            itens_venda = self.caixa_model.db.fetch_all(query_itens, (venda_id,))

            # 3. Busca o CLIENTE (se houver)
            dados_cliente = None
            if dados_venda.get('cliente_id'):
                dados_cliente = self.clientes_model.buscar_por_id(dados_venda['cliente_id'])

            # 4. Prepara o dicionário de pagamentos (Simulado, pois o histórico detalhado pode variar)
            # Se você salvou o json de pagamentos no banco, use-o. Se não, assumimos Crediário.
            pagamentos_simulados = {"Crediário / ": dados_venda['total']}

            # 5. Chama o Serviço de Impressão
            servico_impressao = ImpressaoService(largura_papel=38) # Ajuste conforme sua impressora
            
            conteudo = servico_impressao.gerar_cupom_venda(
                itens=itens_venda,
                total=dados_venda['total'],
                pagamentos=pagamentos_simulados,
                cliente=dados_cliente,
                # Dica: Se seu gerar_cupom aceitar, mande a data original
                data_customizada=dados_venda.get('data_venda') 
            )
            
            servico_impressao.imprimir_raw(conteudo)
            messagebox.showinfo("Sucesso", "Enviado para impressão!")

        except Exception as e:
            print(f"Erro ao reimprimir: {e}")
            messagebox.showerror("Erro", f"Falha na impressão: {e}")

    # --- NOVO BLOCO DE RECEBIMENTO (Adicione no GestaoController) ---

    # Adicione o parametro view_origem
    def iniciar_recebimento_selecao(self, cliente, view_origem):
        pendencias = self.clientes_model.buscar_contas_pendentes(cliente['id'])
        
        if not pendencias:
            from tkinter import messagebox
            messagebox.showinfo("Aviso", "Este cliente não possui contas pendentes.")
            return

        # Callback 1: Paga mas NÃO atualiza a tela
        def acao_pagar(ids):
            # O parâmetro atualizar_interface=False é crucial aqui
            return self._processar_pagamento_lote(cliente, ids, atualizar_interface=False)
        
        # Callback 2: Atualiza a tela usando a view correta
        def acao_refresh():
            # Usa view_origem para garantir que atualizamos a tela certa
            if hasattr(view_origem, 'exibir_ficha_financeira_completa'):
                 # Se a view tiver o método direto
                 view_origem.exibir_ficha_financeira_completa(cliente)
            else:
                 # Fallback para o método do controller (se necessário)
                 self.exibir_ficha_financeira_completa(cliente)

        # CORREÇÃO PRINCIPAL AQUI:
        # Usamos 'view_origem' em vez de 'self.view'
        view_origem.abrir_modal_recebimento_selecao(pendencias, acao_pagar, acao_refresh)

    def _processar_pagamento_lote(self, cliente, lista_ids, atualizar_interface=True):
        """Recebe os IDs e manda quitar. O parâmetro controla se a tela recarrega."""
        if not lista_ids: return False

        sucesso = self.clientes_model.quitar_contas_lote(lista_ids)
        
        if sucesso:
            if atualizar_interface:
                self.exibir_ficha_financeira_completa(cliente)
            return True
        else:
            return False


    def abrir_pesquisa_financeiro(self):
        """Pede para a View mostrar a lista de seleção específica para financeiro"""
        clientes = self.clientes_model.listar_clientes("")
        if clientes:
            # Chamamos a nova função de busca simplificada que criamos acima
            self.pagina_clientes.abrir_pesquisa_financeiro_view(clientes)


    def carregar_financeiro_cliente(self, cliente):
        """Busca dados reais e atualiza a ficha financeira na View"""
        # 1. Busca os números no Model
        resumo = self.clientes_model.buscar_resumo_financeiro(cliente['id'])
        
        # 2. Algoritmo de Score (Simples: se tem vencida, score cai)
        score = 100
        if resumo['vencidas'] > 0:
            score = 40  # Risco Alto
        elif resumo['total_compras'] > 0:
            score = 95  # Ótimo cliente
            
        # Adicionamos o score ao dicionário de resumo
        resumo['score'] = score
        
        # 3. Manda a View renderizar com dados REAIS
        self.pagina_clientes.exibir_ficha_financeira(cliente, resumo)


    def exibir_ficha_financeira_completa(self, cliente):
        """Prepara os dados e chama a tela do cliente"""
        try:
            # 1. Busca os dados
            resumo = self.clientes_model.buscar_resumo_financeiro(cliente['id'])
            timeline = self.clientes_model.buscar_movimentacoes_timeline(cliente['id'])
            
            # 2. Verifica se a página existe (agora usando a variável correta)
            if hasattr(self, 'pagina_clientes') and self.pagina_clientes:
                # Chama a função na View
                self.pagina_clientes.exibir_ficha_financeira(cliente, resumo, timeline)
            
            # Fallback (Plano B caso algo dê errado)
            elif hasattr(self.view, 'clientes_view'):
                self.view.clientes_view.exibir_ficha_financeira(cliente, resumo, timeline)
            
            else:
                print("ERRO CRÍTICO: O Controller não encontrou a 'pagina_clientes'.")
                from tkinter import messagebox
                messagebox.showerror("Erro de Interface", "Não foi possível localizar a tela de clientes.")

        except Exception as e:
            print(f"Erro ao abrir ficha financeira: {e}")

    

    def registrar_pagamento_cliente(self, cliente_id, valor_pago):
        """Lógica para abater dívidas do crediário"""
        # 1. Busca todas as contas pendentes do cliente (da mais antiga para a mais nova)
        contas = self.clientes_model.buscar_contas_pendentes(cliente_id)
        
        valor_restante = valor_pago
        
        for conta in contas:
            if valor_restante <= 0: break
            
            divida_atual = conta['valor_total'] - conta['valor_pago']
            
            if valor_restante >= divida_atual:
                # Paga a conta inteira
                novo_valor_pago = conta['valor_total']
                status = 'PAGO'
                valor_restante -= divida_atual
            else:
                # Paga apenas uma parte
                novo_valor_pago = conta['valor_pago'] + valor_restante
                status = 'PARCIAL'
                valor_restante = 0
                
            # Atualiza no banco
            self.clientes_model.atualizar_pagamento_crediario(conta['id'], novo_valor_pago, status)



    def inicializar_pagina_clientes(self):
        """
        Este é o método principal que a GestaoView chama para abrir a tela.
        Ele limpa o centro do sistema e carrega a ClientesView.
        """
        try:
            # 1. Busca os dados iniciais do Model
            clientes = self.clientes_model.listar_clientes()
            
            # 2. Import local para evitar erro de importação circular
            from app.views.pages.clientes_view import ClientesView
            
            # 3. Limpa o container principal da tela
            self.view.limpar_container()

            # 4. Instancia a página de clientes e a exibe
            self.pagina_clientes = ClientesView(self.view.container_principal, self)
            self.pagina_clientes.pack(fill="both", expand=True)
            
            # 5. Manda a página desenhar a lista de clientes recebida
            #self.pagina_clientes.renderizar_lista(clientes)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar tela de clientes: {e}")

    def filtrar_clientes(self, termo):
        """Atualiza a lista de clientes enquanto o usuário digita na busca"""
        try:
            clientes = self.clientes_model.listar_clientes(termo)
            if hasattr(self, 'pagina_clientes'):
                self.pagina_clientes.renderizar_lista(clientes)
        except Exception as e:
            print(f"Erro ao filtrar clientes: {e}")


    def identificar_cliente_venda(self, busca):
        """Busca o cliente e o identifica tanto na Gestão quanto no Controller de Venda"""
        if not busca:
            messagebox.showwarning("Aviso", "Digite o nome ou documento do cliente.")
            return

        # Busca no ClientesModel (que já criamos)
        clientes = self.clientes_model.listar_clientes(busca)

        if not clientes:
            messagebox.showerror("Erro", "Cliente não encontrado.")
            return
        
        # Se encontrou mais de um, aqui você poderia abrir um modal de seleção.
        # Por enquanto, vamos pegar o primeiro encontrado:
        cliente = clientes[0]

        # --- O PULO DO GATO ---
        # 1. Salva no especialista de vendas (para o crediário funcionar)
        self.venda_ctrl.cliente_atual_venda = cliente
        
        # 2. Atualiza a UI do PDV (se você tiver um label de nome de cliente)
        # Supondo que na sua GestaoView (ou PDV) tenha um label para isso:
        try:
            if hasattr(self.view, 'pagina_pdv'):
                # Atualiza o texto, a cor para destacar e o ícone
                self.view.pagina_pdv.lbl_cliente_nome.configure(
                    text=f"👤 CLIENTE: {cliente['nome_razao'].upper()}",
                    text_color="#D4AF37" # Cor dourada para indicar que está identificado
                )
                # Limpa o campo de busca
                self.view.pagina_pdv.ent_busca_cliente.delete(0, 'end')
        except Exception as e:
            print(f"Erro ao atualizar label do PDV: {e}")

        messagebox.showinfo("Sucesso", f"Cliente {cliente['nome_razao']} identificado!")

    def validar_limite_crediario(self, cliente_id, valor_venda):
        """Verifica se o cliente pode comprar no fiado"""
        try:
            # Busca o cliente atualizado no banco
            cliente = self.clientes_model.buscar_por_id(cliente_id)
            
            limite = cliente.get('limite_credito', 0)
            deve = cliente.get('saldo_devedor', 0)
            disponivel = limite - deve
            
            if valor_venda <= disponivel:
                return True, "Limite disponível"
            else:
                return False, f"Limite insuficiente! Disponível: R$ {disponivel:.2f}"
        except Exception as e:
            return False, f"Erro ao validar crédito: {e}"
        
    def deletar_cliente(self, cliente_id):
        """Solicita a exclusão do cliente ao model."""
        if self.clientes_model.deletar(cliente_id):
            print(f"CLIENTE {cliente_id} deletado com sucesso!")
            return True
        
        return False
    

    def verificar_caixa_no_inicio(self):
        query = "SELECT * FROM caixa_sessoes WHERE status = 'ABERTO' LIMIT 1"
        caixa_aberto = self.db.fetch_all(query)
        
        if caixa_aberto:
            self.sessao_atual = caixa_aberto[0]
            # SINCRONIZAÇÃO CRUCIAL:
            self.caixa_model.sessao_id = self.sessao_atual['id'] 
            self.caixa_model.caixa_aberto = True
            print(f"Gestão: Sincronizado com Sessão ID {self.caixa_model.sessao_id}")
            return True
        return False
        

    def preparar_fechamento_caixa(self):
        """Pega os dados da sessão aberta para exibir na tela de fechamento."""
        if hasattr(self, 'sessao_atual'):
            sessao_id = self.sessao_atual['id']
            # Busca a lista de vendas do banco
            vendas = self.vendas_model.obter_extrato_fechamento(sessao_id)
            
            # Calcula o total acumulado em dinheiro
            total_caixa = sum(v['total'] for v in vendas) + self.sessao_atual['valor_inicial']
            
            # Chama a View de fechamento (que vamos criar)
            self.view.exibir_tela_fechamento(vendas, total_caixa)


    def abrir_gestao_caixa(self):
        # Em vez de tentar ler o banco aqui, delega para o CaixaController 
        # que já corrigimos acima. Isso garante que o fluxo seja o mesmo.
        if hasattr(self, 'caixa_ctrl'):
            self.caixa_ctrl.abrir_gestao()
        else:
            # Caso o controlador não esteja instanciado
            from app.controllers.caixa_controller import CaixaController
            self.caixa_ctrl = CaixaController(self.main)
            self.caixa_ctrl.abrir_gestao()