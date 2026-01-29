import serial
import serial.tools.list_ports
import serial  # (Balança)
from datetime import datetime
from escpos.printer import Serial as PrinterSerial
import win32print

class BalancaModel:

    def __init__(self):

        self.porta_balanca = "COM4"
        self.porta_impressora = "COM6"
        self.baudrate_balanca = 9600
        self.baudrate_impressora = 115200
        self.balanca = None
        self.tentativas_debug = 0


    def conectar(self):

        try:
            self.balanca = serial.Serial(self.porta_balanca, self.baudrate_balanca, timeout=0.5)
            return True, "Conectado"
        except Exception as e:
            return False, str(e)



    def obter_dados(self):

        if not self.balanca or not self.balanca.is_open:
                # Só exibe o print se o contador for menor que 3
            if self.tentativas_debug < 3:
                print(f"DEBUG: Balança desconectada ou porta fechada (Aviso {self.tentativas_debug + 1}/3)")
                self.tentativas_debug += 1
            return None
        
        self.tentativas_debug = 0
        
        try:
            if self.balanca and self.balanca.is_open:
                if self.balanca.in_waiting >= 25:
                    msg = self.balanca.read(25)
                    msg_str = msg.decode('ascii', errors='ignore').strip()

                    if msg_str.startswith('\x02'):
                        msg_str = msg_str[1:]
                    if msg_str.endswith('\x03'):
                        msg_str = msg_str[:-1]

                    campos = msg_str.split()
                    if len(campos) < 3:
                        return None

                    try:
                        # Seus cálculos exatos de peso, preço e total
                        peso = int(campos[0][-3:]) / 1000.0
                        preco = int(campos[1]) / 100.0
                        valor_total = int(campos[2]) / 100.0
                        
                        return {
                            "tara": 0.0,
                            "peso": peso,
                            "preco_por_kg": preco,
                            "total": valor_total
                        }
                    except ValueError:
                        return None
            return None
        except Exception as e:
            print(f"Erro na leitura: {e}")
            return None
        


    def gerar_ean13(self, cod_produto, peso, preco):

        total_centavos = int(round(peso * preco * 100))
        inteiro = total_centavos // 100
        centavos = total_centavos % 100
        codigo_base = f"2{cod_produto:04d}{inteiro:05d}{centavos:02d}0"
        soma = sum(int(codigo_base[i]) * (3 if i % 2 else 1) for i in range(12))
        dv = (10 - (soma % 10)) % 10
        return codigo_base[:-1] + str(dv)
    


    def imprimir_comanda(self, dados):


        p = None
        try:
            # Usando o PrinterSerial que você importou com alias
            p = PrinterSerial(
                devfile=self.porta_impressora,
                baudrate=self.baudrate_impressora, # Geralmente impressoras térmicas usam 115200 ou 9600
                timeout=1
            )

            codigo_ean = self.gerar_ean13(cod_produto=1010, peso=dados['peso'], preco=dados['preco_por_kg'])
            data_hora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            p.set(align='center', width=2, height=2, bold=True)
            p.text("====== RESTAURANTE ROMEU E JULIETA ======\n\n")
            p.text("============== COMANDA Nº ===============\n\n")
            p.text(f"Peso(L): {dados['peso']:.3f}kg\n")
            p.text(f"R$/kg: {dados['preco_por_kg']:.2f}\n")
            p.text(f"TOTAL R$: {dados['total']:.2f}\n\n")
            
            p.barcode(codigo_ean, 'EAN13', width=3, height=100, pos='BELOW', font='B')
            p.text("\n\nAgradeço-te Senhor,\npelo teu amor e pela tua graça\n")
            p.text("=========================================\n\n\n")
            p.text(f"\n{data_hora}\n")
            p.text("\n\n\n\n\n") # Espaço para o corte
            p.cut()
            
            return True
        except Exception as e:
            print(f"❌ Erro na impressora: {e}")
            return False
        finally:
            if p:
                p.close()



    def listar_portas_disponiveis():

        portas = serial.tools.list_ports.comports()
        return [p.device for p in portas] or ["Nenhuma encontrada"]
    


    def imprimir_cupom_venda(self, itens, total, forma_pagamento):

        try:
            # 1. Gerar o texto (mesmo código anterior)
            conteudo = []
            conteudo.append("      NOME DO SEU RESTAURANTE      ")
            conteudo.append("-----------------------------------")
            conteudo.append(f"DATA: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            conteudo.append("-----------------------------------")
            conteudo.append("ITEM            QTD           TOTAL")
            
            for item in itens:
                nome = item['nome'][:14].ljust(14)
                qtd = f"{item['qtd']:.3f}" if "KG" in item['nome'].upper() else f"{int(item['qtd'])}x"
                total_item = f"{item['total']:.2f}".rjust(8)
                conteudo.append(f"{nome} {qtd.ljust(8)} {total_item}")
            
            conteudo.append("-----------------------------------")
            conteudo.append(f"TOTAL:              R$ {total:.2f}")
            conteudo.append(f"FORMA PAGTO: {forma_pagamento.upper()}")
            conteudo.append("-----------------------------------")
            conteudo.append("     OBRIGADO E VOLTE SEMPRE!      \n\n\n\n\n\n") # Espaço para o corte
            
            texto_final = "\n".join(conteudo)

            # 2. Comando de Corte (ESC/POS)
            # GS V 66 0 -> Comando comum para corte total/parcial
            comando_corte = b'\x1d\x56\x42\x00' 

            # 3. ENVIAR PARA A IMPRESSORA
            printer_name = win32print.GetDefaultPrinter()
            hPrinter = win32print.OpenPrinter(printer_name)
            
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Cupom de Venda", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                
                # Envia o texto do cupom
                win32print.WritePrinter(hPrinter, texto_final.encode('cp850')) # cp850 ajuda com acentos em térmicas
                
                # Envia o comando de corte
                win32print.WritePrinter(hPrinter, comando_corte)
                
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
                
                
            return True
        except Exception as e:
            print(f"Erro físico na impressora: {e}")
            return False
        


        # --- Dentro de balanca_model.py ---

        # --- Dentro de balanca_model.py ---
    def extrair_dados_etiqueta(self, barcode):
        barcode = str(barcode).strip()
        if len(barcode) != 13: return None, 0

        # SEU PADRÃO MARKETUP: 2 + ID(4) + VALOR(7) + DV(1)
        # Exemplo: 2 1010 0001550 4
        
        id_extraido = barcode[1:5]    # Pega '1010'
        valor_str = barcode[5:12]     # Pega '0001550' (os 7 dígitos de valor)
        
        valor_total = int(valor_str) / 100.0
        return id_extraido, valor_total
   
    
    def gerar_ean_mestre_busca(self, id_produto):
        """Gera o EAN-13 mestre exatamente como o cadastro gera, para busca no banco"""
        try:
            # Garante que o ID tenha 4 dígitos (ex: '0012')
            id_limpo = f"{int(id_produto):04d}"
            # Monta a base: 2 + ID + 0000000 (total 12 dígitos)
            codigo_base = f"2{id_limpo}0000000"
            
            # Calcula o dígito verificador (DV) padrão EAN-13
            soma = sum(int(codigo_base[i]) * (3 if i % 2 else 1) for i in range(12))
            dv = (10 - (soma % 10)) % 10
            
            return codigo_base + str(dv)
        except Exception as e:
            print(f"Erro ao gerar EAN de busca: {e}")
            return ""
