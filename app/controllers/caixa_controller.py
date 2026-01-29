from tkinter import messagebox
import customtkinter as ctk
from app.services.impressao_service import ImpressaoService
class CaixaController:

    def __init__(self, main_controller):
        self.main = main_controller  
        self.view = main_controller.view
        self.caixa_model = main_controller.caixa_model
        self.impressao_service = ImpressaoService()
    # --- AUXILIARES ---

    def verificar_caixa_aberto(self):
        """Apenas verifica e avisa. NÃO abre a tela de abertura automaticamente."""
        sessao_id = self.caixa_model.sessao_id
        
        # Tenta buscar no main se não estiver no model
        if not sessao_id:
            if hasattr(self.main, 'sessao_atual') and self.main.sessao_atual:
                sessao_id = self.main.sessao_atual.get('id')

        if not sessao_id:
            # Apenas exibe o aviso
            messagebox.showwarning("Caixa Fechado", "O caixa precisa estar ABERTO para acessar a gestão.")
            # REMOVI A LINHA: self.mostrar_tela_abertura_caixa() 
            return False
            
        return True

    def solicitar_abertura_caixa(self):
        """Função de atalho para evitar o erro de AttributeError"""
        # Delegamos para a função que você já usa no sistema
        if hasattr(self, 'mostrar_tela_abertura_caixa'):
            self.mostrar_tela_abertura_caixa()
        else:
            # Caso o nome no seu controller seja outro, ajuste aqui:
            self.abrir_modal_abertura()
    # --- ABERTURA ---

    def mostrar_tela_abertura_caixa(self):
        """Abre o modal de abertura de caixa usando o popup correto"""
        from app.views.popups.abertura_caixa_view import AberturaCaixaView
        
        # Pega a janela principal para ser o 'master'
        janela_master = getattr(self.main, 'view', None) or self.view
        
        # Cria a instância da janelinha
        self.modal_abertura = AberturaCaixaView(
            master=janela_master, 
            controller=self
        )


    def confirmar_abertura_caixa(self, valor_str):
        try:
            # Conversão de valor
            valor = float(valor_str.replace(",", "."))
            
            # 1. Abre no banco
            self.caixa_model.abrir_caixa(valor)
            
            # 2. Recupera os dados da sessão (agora com ID e Data do Banco)
            sessao_info = self.caixa_model.obter_sessao_ativa()
            
            if sessao_info:
                # Sincroniza com o Main
                self.main.sessao_atual = sessao_info
                self.caixa_model.sessao_id = sessao_info['id']

                # --- NOVA PARTE: IMPRESSÃO DO COMPROVANTE ---
                try:
                    nome_usuario = getattr(self.main, 'usuario_logado', 'OPERADOR PADRÃO')
                    # Prepara os dados para o cupom
                    # Se o banco não retornar o nome do operador, usamos o do main
                    dados_comprovante = {
                        'id': sessao_info['id'],
                        'operador': nome_usuario,
                        'valor_inicial': valor,
                        'data_abertura': sessao_info.get('data_abertura', self.get_data_hora_atual())
                    }
                    
                    # Gera o texto usando a sua classe de serviço
                    texto_cupom = self.impressao_service.gerar_comprovante_abertura(dados_comprovante)
                    
                    # Envia para a Bematech (ajuste o nome do seu atributo de impressora aqui)
                    self.impressao_service.imprimir_texto(texto_cupom)
                    
                except Exception as e_print:
                    # Se a impressora falhar, avisamos mas não travamos o sistema
                    print(f"Erro ao imprimir comprovante: {e_print}")
                # ---------------------------------------------

                if hasattr(self, 'modal_abertura') and self.modal_abertura:
                    self.modal_abertura.destroy()
                
                messagebox.showinfo("Sucesso", f"Caixa aberto com R$ {valor:.2f}")
                
                # 3. Redireciona para o PDV/Vendas
                self.main.exibir_pdv() 
            else:
                raise Exception("Não foi possível recuperar a sessão aberta do banco.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir caixa: {e}")

    def get_data_hora_atual(self):
        from datetime import datetime
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # --- GESTÃO E CONFERÊNCIA ---

    def abrir_gestao(self):

        if not self.verificar_caixa_aberto():
            return #
        # 1. Recupera o ID da sessão ativa
        sessao_id = self.caixa_model.sessao_id
        if not sessao_id:
            if hasattr(self.main, 'sessao_atual') and self.main.sessao_atual:
                sessao_id = self.main.sessao_atual.get('id')

        # 2. Busca os dados necessários para a View
        resumo = self.caixa_model.obter_resumo_caixa(sessao_id)
        
        # SEGURANÇA: Se o resumo der erro ou retornar None, usamos o fallback manual
        # SEGURANÇA: Fallback atualizado para não quebrar o fechamento detalhado
        if not resumo:
            resumo = {
                'abertura': 0.0, 'faturamento_total': 0.0, 'saldo_atual_dinheiro': 0.0,
                'reforcos': 0.0, 'sangrias': 0.0,
                'detalhado': {
                    "Dinheiro": 0.0, "Pix": 0.0, "Crédito": 0.0, "Débito": 0.0,
                    "Vale Refeição": 0.0, "Vale Alimentação": 0.0, "Crediário": 0.0
                }
            }

        vendas = self.caixa_model.obter_vendas_dia(sessao_id) or []
        movimentacoes = self.caixa_model.obter_movimentacoes_dia(sessao_id) or []
        
        # Une e ordena a lista
        dados_completos = vendas + movimentacoes
        dados_completos.sort(key=lambda x: x.get('hora', '00:00'), reverse=True)

        # 3. Abre a View
        from app.views.popups.gestao_caixa_view import GestaoCaixaView
        
        # Tentamos encontrar o master correto: ou self.main.view ou self.view
        janela_master = getattr(self.main, 'view', None) or getattr(self, 'view', None)

        self.main.janela_gestao = GestaoCaixaView(
            master=janela_master, 
            controller=self,
            resumo=resumo,
            dados_vendas=dados_completos
        )



    def processar_fechamento(self):
        """Prepara os dados detalhados e abre a sua View de Conferência"""
        try:
            # 1. Busca o resumo detalhado do Model
            sessao_id = self.caixa_model.sessao_id
            resumo = self.caixa_model.obter_resumo_caixa(sessao_id)
            
            if not resumo:
                messagebox.showerror("Erro", "Não foi possível recuperar os dados da sessão.")
                return

            # 2. MAPEAMENTO: Usa as chaves exatas do dicionário 'detalhado' do Model
            detalhado = resumo['detalhado']
            totais_conferencia = {
                "Dinheiro": resumo['saldo_atual_dinheiro'],
                "Pix": detalhado.get("Pix", 0.0),
                "Crédito": detalhado.get("Crédito", 0.0),
                "Débito": detalhado.get("Débito", 0.0),
                "Vale Refeição": detalhado.get("Vale Refeição", 0.0),
                "Vale Alimentação": detalhado.get("Vale Alimentação", 0.0),
                "Crediário": detalhado.get("Crediário", 0.0)
            }

            # 3. ABRIR A JANELA - CORREÇÃO DA REFERÊNCIA
            from app.views.popups.fechamento_caixa_view import FechamentoCaixaView
            
            # Buscamos a janela exatamente onde você a salvou em 'abrir_gestao'
            janela_pai = getattr(self.main, 'janela_gestao', None)
            
            self.janela_conferencia = FechamentoCaixaView(
                master=janela_pai, # Agora o master é a janela física salva no main
                controller=self,
                totais_esperados=totais_conferencia
            )

        except Exception as e:
            print(f"Erro ao abrir conferência: {e}")
            messagebox.showerror("Erro", f"Falha ao processar dados: {e}")

    


    def finalizar_encerrar_caixa_total(self, relatorio, view_conferencia):
        """Recebe o relatório pronto da View e encerra o sistema"""
        try:
                # 1. Recuperamos o resumo uma última vez para pegar o valor exato
            resumo = self.caixa_model.obter_resumo_caixa(self.caixa_model.sessao_id)
            valor_para_banco = resumo['saldo_atual_dinheiro']

            # 2. Manda o Model fechar passando o VALOR FINAL (Missão Corrigida!)
            self.caixa_model.fechar_caixa(valor_para_banco)
            
            # 2. Exibe o MessageBox que você queria com o relatório final
            # parent=view_conferencia garante que o popup fique em cima da janela
            view_conferencia.attributes("-topmost", False)
            messagebox.showinfo("Fechamento Concluído", relatorio, parent=view_conferencia)
            
            # 3. Limpa as sessões e flags
            self.caixa_aberto = False
            if self.main:
                self.main.sessao_atual = None
                
            # 4. Destrói as janelas
            view_conferencia.destroy()
            if hasattr(self, 'janela_gestao') and self.main.janela_gestao:
                self.main.janela_gestao.destroy()
                self.main.janela_gestao = None

            # 5. Volta para a tela principal (Bloqueada)
            self.main.exibir_pdv()

        except Exception as e:
            print(f"Erro no encerramento final: {e}")
            messagebox.showerror("Erro", f"Não foi possível encerrar o banco: {e}")

    # --- MOVIMENTAÇÕES (SANGRIA/REFORÇO) ---

    def abrir_modal_movimentacao(self, tipo):
        if not self.verificar_caixa_aberto():
            return

        dialogo = ctk.CTkInputDialog(text=f"Valor do(a) {tipo}:", title=tipo)
        valor_str = dialogo.get_input()

        if valor_str is not None:

            if valor_str.strip() == "": return
            try:
                valor = float(valor_str.replace(",", "."))
                motivo_diag = ctk.CTkInputDialog(text="Justificativa:", title="Motivo")
                motivo = motivo_diag.get_input() or "Não informado"

                # --- AJUSTE AQUI: Pega o ID da sessão ---
                sessao_id = None
                if hasattr(self.main, 'sessao_atual') and self.main.sessao_atual:
                    sessao_id = self.main.sessao_atual.get('id')

                # Passa o sessao_id para o model
                nome_usuario = getattr(self.main, 'usuario_logado', 'SISTEMA')
                sucesso = self.caixa_model.lancar_movimentacao(
                    tipo=tipo, 
                    valor=valor, 
                    motivo=motivo, 
                    operador=nome_usuario,
                    sessao_id=sessao_id # <--- Adicione este parâmetro
                )

                if sucesso:
                    messagebox.showinfo("Sucesso", f"{tipo} registrada!")
                    if hasattr(self.main, 'janela_gestao') and self.main.janela_gestao.winfo_exists():
                        # Ao invés de destroy, vamos apenas atualizar
                        self.abrir_gestao() 
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido.")



    def lancar_movimentacao(self, tipo):
        """Redireciona para o método que abre o input de valor"""
        self.abrir_modal_movimentacao(tipo)



    def solicitar_exclusao_venda(self, venda):
        # 1. Cria o diálogo de senha
        senha_dialog = ctk.CTkInputDialog(
            text="Digite a senha de GERENTE:",
            title="Autorização"
        )
        
        # Centralização e foco
        from app.views.base_view import BaseView
        BaseView.center_window(senha_dialog, 300, 150)
        senha_dialog.attributes("-topmost", True)
        senha_dialog.after(10, lambda: senha_dialog.focus_force())
        
        senha = senha_dialog.get_input()
        
        # 2. Validação da Senha
        if senha == "123":
            # CORREÇÃO: Usamos .get('valor') ou .get('total') para evitar o KeyError
            valor_venda = float(venda.get('valor') or venda.get('total') or 0)
            
            # 3. Confirmação visual
            msg = f"Deseja excluir a venda de R$ {valor_venda:.2f}?"
            if messagebox.askyesno("Confirmar", msg, parent=self.main.janela_gestao):
                
                # 4. Executa a exclusão no Model (passando apenas o ID)
                venda_id = venda.get('id')
                sucesso = self.caixa_model.excluir_venda(venda_id)
                
                if sucesso:
                    messagebox.showinfo("Sucesso", "Venda excluída com sucesso!", parent=self.main.janela_gestao)
                    
                    # 5. Atualização da View Atual (sem abrir nova janela)
                    view_atual = getattr(self.main, 'janela_gestao', None)
                    
                    if view_atual and view_atual.winfo_exists():
                        # Recupera o ID da sessão
                        sessao_id = self.main.sessao_atual.get('id') if self.main.sessao_atual else self.caixa_model.sessao_id
                        
                        # Busca dados novos
                        resumo_novo = self.caixa_model.obter_resumo_caixa(sessao_id)
                        vendas = self.caixa_model.obter_vendas_dia(sessao_id)
                        movs = self.caixa_model.obter_movimentacoes_dia(sessao_id)
                        
                        # Prepara a lista única
                        lista_atualizada = vendas + movs
                        lista_atualizada.sort(key=lambda x: x.get('hora', '00:00'), reverse=True)

                        # Aplica os dados na tela existente
                        view_atual.atualizar_resumo_tela(resumo_novo)
                        view_atual.atualizar_lista_vendas(lista_atualizada)
                else:
                    messagebox.showerror("Erro", "Não foi possível excluir a venda no banco de dados.", parent=self.main.janela_gestao)
        
        elif senha is None:
            return # Cancelou o input
        else:
            messagebox.showerror("Erro", "Senha de gerente incorreta!", parent=self.main.janela_gestao)
  
               
    def remover_venda_do_banco(self, venda_id):
        self.caixa_model.remover_venda_do_banco(venda_id)
        messagebox.showinfo("Sucesso", "Venda removida!")



    def abrir_gestao_caixa(self):
        """Bloqueia o acesso se o caixa estiver fechado"""
        # 1. Verifica no banco se existe sessão aberta
        sessao_ativa = self.caixa_model.verificar_status_caixa()
        
        if not sessao_ativa:
            messagebox.showwarning(
                "Acesso Negado", 
                "O caixa está FECHADO.\n\nAbra o caixa no PDV antes de acessar a gestão."
            )
            # NÃO chamamos mostrar_tela_abertura aqui para não forçar o usuário
            return

        # 2. Se estiver aberto, busca os dados e abre a janela
        self.abrir_gestao()
        


    def atualizar_dashboard_gestao(self):
        try:
            # Pega o ID que está guardado no Controller/Model
            s_id = self.caixa_model.sessao_id
            
            if not s_id:
                print("ERRO: Sessão ID não encontrado no Controller.")
                return

            # Busca usando o ID garantido
            vendas = self.caixa_model.obter_vendas_dia(s_id)
            movimentacoes = self.caixa_model.obter_movimentacoes_dia(s_id)
            
            # Une as listas
            dados_completos = vendas + movimentacoes
            
            # Ordena: as mais recentes primeiro
            dados_completos.sort(key=lambda x: x.get('hora', '00:00'), reverse=True)

            # Envia para a View
            janela = getattr(self.main, 'janela_gestao', None)
            if janela and janela.winfo_exists():
                janela.atualizar_lista_vendas(dados_completos)
                
                # Atualiza também o resumo (total vendido, etc)
                resumo = self.caixa_model.obter_resumo_caixa(s_id)
                janela.atualizar_resumo_tela(resumo)

        except Exception as e:
            print(f"Erro ao atualizar dashboard: {e}")



    def abrir_modal_abertura(self):
        """Abre a janelinha que acabamos de criar"""
        from app.views.popups.abertura_caixa_view import AberturaCaixaView
        self.modal_abertura = AberturaCaixaView(self.main.view, self)


