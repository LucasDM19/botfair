"""
Classe que se conecta com um banco de dados.
"""
class BancodeDados():
   def __init__(self):
      config = {
        'user': usuarioBD,
        'password': senhaBD,
        'host': hostBD,
        'database': databaseName,
        'raise_on_warnings': True,
      }
      #import mysql.connector7
      import mysql.connector
      self.conn = mysql.connector.connect(**config)

   #Abstrai para incluir qualquer item em qualquer tabela. 
   #Passa campos=(campo1, campo2, campo3, ...), nome da tabela e campoId=id (geralmente)
   def salvaTabela(self, campos=None, nomeTabela=None, campoId=None, valores=None):
      #Verificar se tabela existe.
      #Verificar se os campos da tabela correspondem ao informado.
      #Verificar se foi mandado campo com apenas um valor
      cursor = self.conn.cursor()
      camposBusca = tuple(campo for campo in campos if campo != campoId)
      print("Salvarei ", nomeTabela, campos, campoId, valores, camposBusca)
      if(len(camposBusca) > 1):
         query = "SELECT " + ", ".join(campos) + " FROM " + nomeTabela + " WHERE " +camposBusca[0]+ " = %s " + " ".join([" AND " +campo+ " = %s " for campo in camposBusca[1:] ])
      else:
         query = "SELECT " + ", ".join(campos) + " FROM " + nomeTabela + " WHERE " +camposBusca[0]+ " = %s "
      valores = [str(v) for v in valores] #Tentar arrumar string
      print("q=",query,", v=", valores)
      cursor.execute(query, valores )
      idRetorno = -1
      for camposR in cursor: #Refatorar a partir daqui
         idRetorno = camposR[0] #Supondo que seja o primeiro campo
      cursor.close()
      if( idRetorno != -1): #Ja tem registro
         return idRetorno #Retorna o ultimo ID encontrado
      
      #Inserindo registro novo
      cursor = self.conn.cursor()
      insert = ("INSERT INTO " + nomeTabela + 
               "(" + ",".join(camposBusca)+") "
               "VALUES ("+ ",".join(("%s",)*len(valores)) +")")
      cursor.execute(insert, valores)
      idRetorno = cursor.lastrowid
      cursor.close()
      return idRetorno
   
   #Com base no nome do confronto (Mandante v Visitante), verifica se ja tem. Se ja tiver, retorna ID. Se nao tiver, insere, e retorna ID
   def salvaTabelaTimes(self, nome):
      print("Salvarei Times:", nome)
      idRetorno = self.salvaTabela(campos=("id", "nome"), nomeTabela="bf_times", campoId="id", valores=(nome,) )
      return idRetorno
      
   #Recebe dados do ID Betfair, id das equipes, e open_date. Se ja existir, retorna ID Betfair. Se nao existir, cadastra, e retorna ID Betfair
   def salvaTabelaPartidas(self, idBF, idEquipes, openDate):
      from datetime import datetime
      dOpenDate = datetime.strptime(openDate ,'%Y-%m-%dT%H:%M:%S.000Z') #Converto a data
      sOpenDate = dOpenDate.strftime('%Y-%m-%d %H:%M:%S') #Formato mySQL
      print("Salvarei Partidas:", idBF, idEquipes, sOpenDate)
      
      idRetorno = self.salvaTabela(campos=("id_bf", "id_time", "open_date"), nomeTabela="bf_partidas", campoId="", valores=(idBF, idEquipes, sOpenDate,) )
      return idRetorno #Deve ser igual a idBF
      
   #Recebe nome do mercado. Se ja existe, retorna ID. Se nao tiver, cadastra, e retorna ID
   def salvaTabelaMercados(self, nome):
      print("Salvarei Mercados:", nome)
      idRetorno = self.salvaTabela(campos=("id", "nome"), nomeTabela="bf_mercados", campoId="id", valores=(nome,) )
      return idRetorno
      
   #Recebe id do mercado e nome da selecao. Se nao tiver, cadastra, e retorna ID. Se ja tiver, retorna ID.
   def salvaTabelaSelecoes(self, idMercado, nome):
      print("Salvarei Selecoes:", idMercado, nome)
      idRetorno = self.salvaTabela(campos=("id", "id_mercado", "nome"), nomeTabela="bf_selecoes", campoId="id", valores=(idMercado, nome,) )
      return idRetorno
      
   #Recebe id da partida, id da selecao, timestamp e a melhor odd. Sempre adiciona
   def salvaTabelaOdds(self, idPartida, idSelecao, timestamp, bestOdd):
      print("Salvarei Odds:", idPartida, idSelecao, timestamp, bestOdd)
      idRetorno = self.salvaTabela(campos=("id_partida", "id_selecao", "timestamp", "best_odd"), nomeTabela="bf_odds", campoId="", valores=(idPartida, idSelecao, timestamp, bestOdd,) )
      return idRetorno