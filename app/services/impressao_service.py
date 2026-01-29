from datetime import datetime
from escpos.printer import Serial as PrinterSerial
import win32print
from app.models.empresa_model import EmpresaModel
import textwrap

class ImpressaoService:
    def __init__(self, largura_papel=38):
        self.largura = largura_papel
        self.empresa_model = EmpresaModel()
        # Configurações para impressão Serial (ajuste conforme necessário)
        self.porta_com = "COM3"
        self.baudrate = 115200
        
    def formatar_linha_dupla(self, esquerda, direita):
        """Alinha esquerda e direita com pontos entre eles"""
        espacos = self.largura - len(str(esquerda)) - len(str(direita))
        return f"{esquerda}{'.' * max(1, espacos)}{direita}\n"

    def gerar_comprovante_abertura(self, dados_sessao):
        largura = self.largura 
        cupom = []
        
        cupom.append("=" * largura + "\n")
        cupom.append("COMPROVANTE DE ABERTURA".center(largura) + "\n")
        cupom.append("DE CAIXA".center(largura) + "\n")
        cupom.append("=" * largura + "\n\n")
        
        cupom.append(f"ID SESSO: {dados_sessao['id']}\n")
        cupom.append(f"DATA/HORA: {dados_sessao['data_abertura']}\n")
        
        # Quebra nome do operador se for muito longo
        operador = f"OPERADOR : {dados_sessao['operador'].upper()}"
        linhas_op = textwrap.wrap(operador, width=largura)
        for linha in linhas_op:
            cupom.append(linha + "\n")
            
        cupom.append("-" * largura + "\n")
        
        valor_fmt = f"R$ {float(dados_sessao['valor_inicial']):.2f}"
        cupom.append(self.formatar_linha_dupla("VALOR INICIAL", valor_fmt))
        cupom.append("-" * largura + "\n\n")
        
        cupom.append("\n" * 2)
        linha_assinatura = "_" * (largura - 4)
        cupom.append(linha_assinatura.center(largura) + "\n")
        cupom.append("ASSINATURA DO OPERADOR".center(largura) + "\n")
        cupom.append("\n" * 4) 
        
        return "".join(cupom)

    def gerar_cupom_venda(self, itens, total, pagamentos, cliente=None, data_customizada=None):
        dados_empresa = self.empresa_model.obter_dados()
        cupom = []
        largura = self.largura

        # 1. LINHA DE TOPO (Decoração)
        cupom.append("=" * largura + "\n")

        # 2. SE FOR REIMPRESSÃO (ADICIONAR O AVISO AQUI)
        if data_customizada:
            cupom.append("== SEGUNDA VIA (REIMPRESSÃO) ===".center(largura) + "\n")
            
        # --- CABEÇALHO COM QUEBRA DE LINHA ---
        nome = dados_empresa.get('nome_fantasia') or "MINHA EMPRESA"
        for l in textwrap.wrap(nome.upper(), width=largura):
            cupom.append(l.center(largura) + "\n")
        
        endereco = dados_empresa.get('endereco')
        if endereco:
            for l in textwrap.wrap(endereco, width=largura):
                cupom.append(l.center(largura) + "\n")
        
        if dados_empresa.get('cnpj'):
            cupom.append(f"CNPJ: {dados_empresa['cnpj']}".center(largura) + "\n")
            
        if dados_empresa.get('telefone'):
            cupom.append(f"TEL: {dados_empresa['telefone']}".center(largura) + "\n")
            
        cupom.append("-" * largura + "\n")

        # --- CLIENTE COM QUEBRA DE LINHA ---
        if cliente:
            nome_cli = cliente.get('nome_razao') or cliente.get('nome') or "CLIENTE"
            doc_cli = cliente.get('documento') or ""
            
            # "CLIENTE: " tem 9 caracteres
            linhas_cli = textwrap.wrap(nome_cli.upper(), width=largura - 9)
            cupom.append(f"CLIENTE: {linhas_cli[0]}\n")
            for l in linhas_cli[1:]:
                cupom.append(" " * 9 + l + "\n") # Alinha abaixo do nome
                
            if doc_cli:
                cupom.append(f"CPF/CNPJ: {doc_cli}\n")
            cupom.append("-" * largura + "\n")

        # --- DATA (CORREÇÃO AQUI) ---
        if data_customizada:
            # Se veio uma data específica (reimpressão), usa ela
            data_hora = str(data_customizada)
        else:
            # Se não veio nada (venda nova), pega data/hora atual
            data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        cupom.append(f"DATA: {data_hora}\n")
        cupom.append("-" * largura + "\n")

        # --- ITENS ---
        # --- ITENS ---
        cupom.append("ITEM".ljust(14) + "QTD".center(10) + "TOTAL".rjust(largura-24) + "\n")
        
        for item in itens:
            # 1. Resolver NOME (tenta 'nome' ou 'nome_produto')
            nome_prod = item.get('nome') or item.get('nome_produto') or "Item sem nome"
            
            # 2. Resolver QUANTIDADE (tenta 'qtd' ou 'quantidade')
            qtd = item.get('qtd') if 'qtd' in item else item.get('quantidade', 1)
            
            # 3. Resolver PREÇO/TOTAL (AQUI ESTAVA O ERRO)
            # Tenta pegar o total pronto. Se não tiver, calcula (qtd * unitario)
            if 'total' in item:
                total_item = item['total']
            elif 'preco_total' in item:
                total_item = item['preco_total']
            else:
                # Fallback: Tenta pegar preço unitário e multiplicar
                preco_unit = item.get('preco_unitario') or item.get('preco') or 0
                total_item = float(qtd) * float(preco_unit)

            # Formatação para impressão
            is_peso = "KG" in nome_prod.upper()
            qtd_str = f"{qtd:.3f}" if is_peso else f"{int(qtd)} un"
            valor_item_str = f"{total_item:.2f}".rjust(largura-24)

            linhas_nome = textwrap.wrap(nome_prod, width=13)
            
            # Primeira linha: Nome (parte 1) + Qtd + Total Calculado
            cupom.append(f"{linhas_nome[0].ljust(14)}{qtd_str.center(10)}{valor_item_str}\n")
            
            # Linhas extras do nome
            for l in linhas_nome[1:]:
                cupom.append(f"{l}\n")

        cupom.append("-" * largura + "\n")

        # --- TOTAIS E PAGAMENTOS ---
        cupom.append(self.formatar_linha_dupla("TOTAL GERAL", f"R$ {total:.2f}"))
        
        cupom.append("\nFORMA(S) DE PAGAMENTO:\n")
        for forma, valor in pagamentos.items():
            if valor > 0:
                cupom.append(f"- {forma[:15].ljust(16)} R$ {valor:.2f}\n")

        # --- RODAPÉ COM QUEBRA DE LINHA ---
        cupom.append("-" * largura + "\n")
        msg_rodape = dados_empresa.get('mensagem_rodape') or "OBRIGADO E VOLTE SEMPRE!"
        for l in textwrap.wrap(msg_rodape, width=largura):
            cupom.append(l.center(largura) + "\n")
        
        cupom.append("\n" * 6)
        return "".join(cupom)

    def imprimir_raw(self, texto):
        """Impressão via Driver do Windows (Padrão)"""

            # === ADICIONE ESTAS LINHAS PARA TESTE ===
        print("\n" + "=".center(40, "="))
        print(" SIMULAÇÃO DE IMPRESSÃO (TERMINAL) ".center(40, "="))
        print(texto)
        print("=".center(40, "=") + "\n")
        # ========================================
        
        try:
            comando_corte = b'\x1d\x56\x42\x00' 
            printer_name = win32print.GetDefaultPrinter()
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Venda", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, texto.encode('cp850', errors='replace'))
                win32print.WritePrinter(hPrinter, comando_corte)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
            return True
        except Exception as e:
            print(f"Erro físico Driver: {e}")
            return False

    def imprimir_texto(self, conteudo):
        """Impressão via Porta Serial Direta (ESC/POS)"""
        p = None
        try:
            p = PrinterSerial(
                devfile=self.porta_com, 
                baudrate=self.baudrate,
                bytesize=8,
                timeout=1
            )
            # Converter para cp850 antes de enviar para suportar acentos na serial
            p._raw(conteudo.encode('cp850', errors='replace'))
            p.cut()
            return True
        except Exception as e:
            print(f"Erro físico Serial: {e}")
            return False
        finally:
            if p:
                try: p.close()
                except: pass

    def imprimir_via_cozinha(self, id_comanda, dados):
        """Gera o cupom de produção para a cozinha/copa."""
        largura = self.largura
        corpo = []
        corpo.append("=" * largura + "\n")
        corpo.append("VIA DA COZINHA".center(largura) + "\n")
        corpo.append(f"COMANDA: #{id_comanda}".center(largura) + "\n")
        corpo.append(f"DATA: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        corpo.append(f"TIPO: {dados.get('categoria', 'BALCÃO')}\n")
        corpo.append("-" * largura + "\n")
        
        for item in dados.get('itens', []):
            qtd = item.get('qtd', 1)
            nome = item.get('nome', '')[:largura-5]
            corpo.append(f"{qtd}x {nome}\n")
            
            # Se tiver observação, imprime em destaque
            obs = item.get('observacao', '')
            if obs:
                corpo.append(f"  >> OBS: {obs.upper()}\n")
        
        corpo.append("-" * largura + "\n")
        corpo.append("\n\n\n") # Espaço para corte
        
        texto_final = "".join(corpo)
        # Tenta imprimir via Driver Windows (seu método padrão)
        return self.imprimir_raw(texto_final)

    

    def imprimir_etiquetas_itens(self, id_comanda, dados):
        sucesso = True
        largura_etiqueta = 28 
        
        # --- AJUSTE DE MAPEAMENTO ---
        # Buscamos primeiro as chaves simples (do dicionário de impressão) 
        # e depois as chaves do banco (caso venha direto do BD)
        categoria = dados.get('categoria', 'BALCÃO').upper()
        
        cliente = (dados.get('nome') or 
                dados.get('cliente_nome_temp') or 
                dados.get('cliente_nome') or 
                'NÃO INFORMADO')
                
        endereco = (dados.get('endereco') or 
                    dados.get('endereco_entrega') or 
                    dados.get('cliente_endereco') or 
                    'RETIRADA')
        # ----------------------------

        for item in dados.get('itens', []):
            etiqueta = []
            
            # Cabeçalho
            cabecalho = f"#{id_comanda} | {categoria}"
            etiqueta.append(cabecalho.center(largura_etiqueta))
            etiqueta.append("-" * largura_etiqueta)
            
            # PRODUTO
            nome_prod = item.get('nome', '').upper()
            for linha in textwrap.wrap(nome_prod, width=largura_etiqueta):
                etiqueta.append(linha)
            
            # OBSERVAÇÕES
            obs = item.get('observacao', '')
            if obs:
                for linha_obs in textwrap.wrap(f">> {obs.upper()}", width=largura_etiqueta):
                    etiqueta.append(linha_obs)
            
            etiqueta.append("-" * largura_etiqueta)
            
            # CLIENTE
            # Usamos .strip() para limpar espaços e garantimos que o nome apareça
            etiqueta.append(f"NOME: {cliente[:largura_etiqueta-5].upper().strip()}")
            
            # ENDEREÇO
            if categoria == "DELIVERY":
                # Se for entrega, mostramos o endereço que agora está mapeado corretamente
                for linha_end in textwrap.wrap(f"ENDERECO: {endereco.upper()}", width=largura_etiqueta):
                    etiqueta.append(linha_end)
            
            # Envia para a impressora
            if not self.imprimir_usb_etiqueta("\n".join(etiqueta)):
                sucesso = False
                
        return sucesso
    
    def imprimir_usb_etiqueta(self, conteudo):
        """Envia a etiqueta para a 4BARCODE usando linguagem TSPL"""
        try:
            nome_encontrado = None
            impressoras = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            
            for imp in impressoras:
                if "ETIQUETADORA" in imp.upper():
                    nome_encontrado = imp
                    break
            
            if not nome_encontrado:
                return False

            # --- CONSTRUÇÃO DO COMANDO TSPL ---
            # SIZE 60 mm, 40 mm (Tamanho da etiqueta)
            # GAP 3 mm (Espaço entre etiquetas)
            # CLS (Limpa o buffer)
            # TEXT (X, Y, Fonte, Rotação, X-multi, Y-multi, "Texto")
            # PRINT 1 (Imprime uma cópia)
            
            linhas = conteudo.split('\n')
            tspl_comando = [
                "SIZE 60 mm, 40 mm",
                "GAP 3 mm, 0",
                "DIRECTION 1",
                "OFFSET 0",
                "CLS"
            ]
            
            y_pos = 10 # Começa um pouco mais acima para ganhar espaço
            
            for linha in linhas:
                if linha.strip():
                    # TEXT x, y, font, rotation, x-mul, y-mul, content
                    # Fonte "2" é boa para etiquetas, fonte "3" é maior.
                    tspl_comando.append(f'TEXT 20,{y_pos},"2",0,1,1,"{linha}"')
                    y_pos += 25 # Espaçamento entre linhas (ajuste se ficar muito apertado)
                else:
                    y_pos += 10 # Espaço para linhas vazias ou separadores
            
            tspl_comando.append("PRINT 1,1")
            # O comando 'END' às vezes causa problemas em algumas Elgins, 
            # opcionalmente pode ser removido se a impressora travar.
            
            final_payload = "\n".join(tspl_comando) + "\n"

            hPrinter = win32print.OpenPrinter(nome_encontrado)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Etiqueta_TSPL", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                
                # Importante: TSPL usa Windows-1252 ou CP850
                win32print.WritePrinter(hPrinter, final_payload.encode('cp850', errors='replace'))
                
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                print(f"TSPL: Enviado para {nome_encontrado}")
                return True
            finally:
                win32print.ClosePrinter(hPrinter)
                
        except Exception as e:
            print(f"ERRO TSPL: {e}")
            return False
        

    def imprimir_via_motoboy(self, id_comanda, dados):
        """Gera o cupom de entrega com destaque para troco e pagamentos."""
        largura = self.largura
        cupom = []

        # --- CABEÇALHO ---
        cupom.append("=" * largura + "\n")
        cupom.append("VIA DE ENTREGA (MOTOBOY)".center(largura) + "\n")
        cupom.append(f"COMANDA: #{id_comanda}".center(largura) + "\n")
        cupom.append("=" * largura + "\n")

        # --- DADOS DO CLIENTE (Lógica de prioridade) ---
        # 1. Tenta pegar da raiz do dicionário (enviado pelo seu Modal)
        # 2. Se falhar, tenta pegar de dentro do cliente_obj
        # DADOS DO CLIENTE - Prioridade absoluta para as chaves diretas
        nome_cli = str(dados.get('nome') or dados.get('cliente_obj', {}).get('nome') or "CLIENTE NÃO INFORMADO").upper()
        end_cli  = str(dados.get('endereco') or dados.get('cliente_obj', {}).get('endereco') or "RETIRADA NO BALCÃO").upper()
        tel_cli  = str(dados.get('telefone') or dados.get('cliente_obj', {}).get('telefone') or "")
        
        cupom.append(f"CLIENTE: {nome_cli}\n")
        if tel_cli:
            cupom.append(f"TEL: {tel_cli}\n")

        cupom.append("ENDEREÇO:\n")
        for linha in textwrap.wrap(end_cli, width=largura):
            cupom.append(f"{linha}\n")
        
        cupom.append("-" * largura + "\n")

        # --- ITENS ---
        cupom.append("ITENS PARA CONFERÊNCIA:\n")
        itens = dados.get('itens', [])
        for item in itens:
            qtd = item.get('qtd', 1)
            # Formatação inteligente de quantidade
            qtd_str = f"{qtd:.3f}kg" if "KG" in item.get('nome', '').upper() else f"{int(qtd)}un"
            nome_prod = item.get('nome', '').upper()[:largura-10]
            cupom.append(f"{qtd_str.ljust(8)} {nome_prod}\n")
        
        cupom.append("-" * largura + "\n")

        # --- FINANCEIRO ---
        # Prioriza total -> total_atual -> soma dos itens
        total = float(dados.get('total') or dados.get('total_atual') or 0.0)
        if total <= 0:
            total = sum(float(i.get('total', 0)) for i in itens)

        cupom.append(f"TOTAL A COBRAR: R$ {total:.2f}\n".upper())

        # Pagamento
        forma_pag = str(dados.get('forma_pagamento') or "NÃO INFORMADO").upper()
        cupom.append(f"PAGAMENTO: {forma_pag}\n")

        # --- TROCO ---
        troco_para = float(dados.get('troco_para') or 0.0)
        if troco_para > total:
            valor_troco = troco_para - total
            cupom.append("*" * largura + "\n")
            cupom.append(f"LEVAR TROCO PARA: R$ {troco_para:.2f}\n")
            cupom.append(f"VALOR DO TROCO:   R$ {valor_troco:.2f}\n")
            cupom.append("*" * largura + "\n")

        cupom.append("-" * largura + "\n")
        cupom.append(f"SAÍDA: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        cupom.append("\n" * 5)

        return self.imprimir_raw("".join(cupom))
    

    def imprimir_item_avulso_comanda(self, id_comanda, item, dados_comanda):
        """
        Copia fiel da função imprimir_etiquetas_itens para garantir 
        que a etiqueta avulsa seja idêntica às demais.
        """
        try:
            largura_etiqueta = 28 
            
            # Puxa os mesmos dados que a sua função original usa
            categoria = dados_comanda.get('categoria', 'BALCÃO').upper()
            cliente = dados_comanda.get('cliente_nome_temp') or dados_comanda.get('cliente_nome') or 'NÃO INFORMADO'
            endereco = dados_comanda.get('endereco_entrega') or dados_comanda.get('cliente_endereco') or 'RETIRADA'

            etiqueta = []
            
            # Cabeçalho (Exatamente como o seu)
            cabecalho = f"#{id_comanda} | {categoria}"
            etiqueta.append(cabecalho.center(largura_etiqueta))
            etiqueta.append("-" * largura_etiqueta)
            
            # PRODUTO com quebra de linha correta
            nome_prod = item.get('nome', '').upper()
            for linha in textwrap.wrap(nome_prod, width=largura_etiqueta):
                etiqueta.append(linha)
            
            # OBSERVAÇÕES
            obs = item.get('observacao', '')
            if obs:
                for linha_obs in textwrap.wrap(f">> {obs.upper()}", width=largura_etiqueta):
                    etiqueta.append(linha_obs)
            
            etiqueta.append("-" * largura_etiqueta)
            
            # CLIENTE
            etiqueta.append(f"CLI: {cliente[:largura_etiqueta-5].upper()}")
            
            # ENDEREÇO (Somente se for Delivery)
            if categoria == "DELIVERY":
                for linha_end in textwrap.wrap(f"END: {endereco.upper()}", width=largura_etiqueta):
                    etiqueta.append(linha_end)
            
            # Converte para string e envia para o processador TSPL que você já tem
            print(f"DEBUG: Enviando etiqueta avulsa idêntica para item: {nome_prod}")
            return self.imprimir_usb_etiqueta("\n".join(etiqueta))

        except Exception as e:
            print(f"Erro ao gerar etiqueta avulsa idêntica: {e}")
            return False