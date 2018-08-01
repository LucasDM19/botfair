from __future__ import print_function
import json
import requests #pip install requests

"""
Classe apenas para a utilizacao da API da Betfair.
"""
class BetfairAPI():
   def __init__(self, usuario=None, senha=None, api_key=None, sessionToken=None):
      if( sessionToken is None and usuario is not None and senha is not None and api_key is not None  ): #Eu poderia usar um SessionToken
         self.usuario = usuario
         self.senha = senha
         self.api_key = api_key
         self.sessionToken = self.fazLogin()
      elif( sessionToken is not None ): #So uso o que ja tem
         self.sessionToken = sessionToken
      else:
         raise Exception('Classe API necessita de usuario+senha+api_key OU sessionToken!')
         
   """
   Faz o login na Betfair. Precisa de um usuario, uma senha, a api key, um arquivo de certificado e um arquivo de key. 
   Os ultimos dois arquivos (.crt e .key) poderiam ser gerados usando o modulo SelfSigned.py
   """ 
   def fazLogin(self, certFile='client-2048.crt', keyFile='client-2048.key'):   
      #Tendo certeza de que os arquivos de certificado e keys realmente existem
      import os.path
      if( os.path.isfile(certFile)==False or os.path.isfile(keyFile)==False ): #Se falta algo
         from SelfSigned import create_self_signed_cert
         create_self_signed_cert(".")
         print("Certificado sendo gerado")
         #Se der Exception, so atura
      
      payload = 'username='+self.usuario+'&password='+self.senha
      headers = {'X-Application': self.api_key, 'Content-Type': 'application/x-www-form-urlencoded'}
       
      resp = requests.post('https://identitysso.betfair.com/api/certlogin', data=payload, cert=(certFile, keyFile), headers=headers)
       
      if resp.status_code == 200:
        resp_json = resp.json()
        print( resp_json['loginStatus'] )
        #print( resp_json['sessionToken'] )
        return resp_json['sessionToken']
      else:
        raise Exception(" Falha no processo de Logon da API da Betfair." )
   """
   Apenas verifica se o login foi feito ou nao.
   """
   def estaLogado(self):
      if( self.sessionToken == None ):
         return False
      return True
      
   """
   Metodo generico, que apenas faz as chamadas da API usando rest. Os filtros dos detalhes aparecem apenas nos metodos especificos.
   """
   def APIRest(self, metodo = "listEventTypes/", json_req='{"filter":{ }}' ):
      endpoint = "https://api.betfair.com/exchange/betting/rest/v1.0/"
      header = { 'X-Application' : self.api_key, 'X-Authentication' : self.sessionToken ,'content-type' : 'application/json' }
      url = endpoint + metodo
      response = requests.post(url, data=json_req, headers=header)
      #print (json.dumps(json.loads(response.text), indent=3))
      return json.loads(response.text) #Formato Json
    
   """
   Exibe todos os mercados (Soccer, Tennis, Golf, Cricket, Rugby Union, etc).
   Soccer eh o Id 1
   Passe a api_key, que deve ser gerada para cada conta. Precisa de SessionToken, que vem depois do login. json_req eh o filtro. 
   Returna o Json, com todos os esportes disponiveis.
   """
   def listaTiposDeEventos(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listEventTypes/", json_req=json_req)

   """
   Obtem a lista de partidas de futebol no periodo determinado.
   Returna o Json
   """
   def obtemPartidasDeFutebol(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listEvents/", json_req=json_req)

   """
   Obtem todos as opcoes de aposta de uma determinada partida.
   Necessario filtro.
   Retorna um Json com todos os mercados.
   """
   def obtemTodosMercadosDasPartidas(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listMarketCatalogue/", json_req=json_req)

   """
   Retorna todas as odds de um grupo de mercados.
   Necessario api_key, sessionToken e o filtro.
   Retorna um Json com todas as odds dos mercados.
   """
   def obtemOddsDosMercados(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listMarketBook/", json_req=json_req)
 
   """
   Efetua uma aposta na BetFair
   Precisa de um marketId (Under/Over 1.5 Goals, por exemplo) e selecionId (Under 1.5 Goals, por exemplo).
   """ 
   def aposta(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "placeOrders/", json_req=json_req)
   
   """
   Consulta todas as apostas correspondidas. 
   Retorna um Json.
   """
   def consultaApostasEfetuadas(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listCurrentOrders/", json_req=json_req)

   """
   Consulta o que aconteceu com a aposta, depois que o evento acabou. 
   """
   def consultaResultadoApostas(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listMarketBook/", json_req=json_req)

"""
Classe que le um arquivo de configuracao, e retorna os itens apropriados.
"""
class ConfigFile():
   def __init__(self, nomeArquivo='config.bot'):
      self.nomeArquivo = nomeArquivo
      
   """
   Oculto os dados mais sensiveis em um arquivo de configuracao.
   Poderia ser melhorado com um dicionario, com o nome da categoria.
   Poderia validar para nao ter chaves duplicadas
   """
   def leConfiguracoesDoArquivo(self):
      lines = [line.rstrip('\n') for line in open(self.nomeArquivo)]
      tuples=[(p.split('=')) for p in lines]
      user = [tuples[idx][1] for idx in range(len(tuples)) if tuples[idx][0] == 'user'][0] #O zero no final indica que pegarei apenas o primeiro.
      pwd = [tuples[idx][1] for idx in range(len(tuples)) if tuples[idx][0] == 'pass'][0] #Senha
      api_key = [tuples[idx][1] for idx in range(len(tuples)) if tuples[idx][0] == 'api_key'][0] #api_key
      return (user, pwd, api_key)

"""
Classe que determina o comportamento do Bot. Nao importa muito se tem base de dados, se acessa Json, ou se usa alguma API.
"""
class BotFair():
   def __init__(self, api=None, bdOption=False):
      if(api is None): #Nao poderia
         raise Exception('Invalid API values for BotFair!')
      if(api.estaLogado() == False): #Falta o logon
         api.fazLogin()
      self.api = api
      if(bdOption): #Se devo conectar no banco
         self.bd = BancodeDados()
         
   """
   Obtem o ID de um esporte, com base no nome.
   """
   def obtemIdDoFutebol(self, eventTypeName="Soccer", lazyMode=False):
      if( lazyMode and eventTypeName == "Soccer" ) : return '1' #Para evitar chamadas desnecessarias
      filtroVazio = '{"filter":{ }}'
      je = self.api.listaTiposDeEventos()
      eventID = [je[idx]['eventType']['id'] for idx in range(len(je)) if je[idx]['eventType']['name']== eventTypeName ][0] #Ja sei que o ID de Soccer eh 1
      return eventID
   
   """
   Obtem a lista de partidas que comecarao nos proximos trinta minutos.
   """
   def obtemListaDePartidas(self, horas=0, minutos=30):
      import datetime
      now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
      future = (datetime.datetime.now() + datetime.timedelta(hours=horas, minutes=minutos)).strftime('%Y-%m-%dT%H:%M:%SZ')
      filtro=('{"filter":{"eventTypeIds":["1"], '
         ' "turnsInPlay" : true, '
         ' "marketStartTime":{"from":"' + now + '", "to":"' + future + '"}},'
         ' "sort":"FIRST_TO_START","maxResults":"1",'
         '"marketProjection":["RUNNER_METADATA"]}')
      self.jPartidas = api.obtemPartidasDeFutebol(json_req=filtro) #Obtendo o Json das partidas
      #print( self.jPartidas )
      for idx in range(len(self.jPartidas)):
         print( "Partida# ",idx,": ID=",self.jPartidas[idx]["event"]["id"], ", Nome=", self.jPartidas[idx]["event"]["name"], ", timezone=",self.jPartidas[idx]["event"]["timezone"], ", openDate=", self.jPartidas[idx]["event"]["openDate"], ", marketCount=", self.jPartidas[idx]["marketCount"] ) 
      
   def ObtemMercadosDisponiveis(self):
      pass
   
   """
   Temporario, antes de gravar no BD
   """
   def ExibeTodosDados(self, soccerID='1', horas=0, minutos=30):   
      #Obtendo a lista de partidas de futebol que estao programadas
      import datetime
      now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
      future = (datetime.datetime.now() + datetime.timedelta(hours=horas, minutes=minutos)).strftime('%Y-%m-%dT%H:%M:%SZ')
      filtro=('{"filter":{"eventTypeIds":["' + soccerID + '"], '
         ' "turnsInPlay" : true, '
         ' "marketStartTime":{"from":"' + now + '", "to":"' + future + '"}},'
         ' "sort":"FIRST_TO_START","maxResults":"1",'
         '"marketProjection":["RUNNER_METADATA"]}')
      jp = api.obtemPartidasDeFutebol(json_req=filtro) #Obtendo o Json das partidas
      for idx in range(len(jp)):
         #print( "Partida# ",idx,": ID=",jp[idx]["event"]["id"], ", Nome=", jp[idx]["event"]["name"], ", timezone=",jp[idx]["event"]["timezone"], ", openDate=", jp[idx]["event"]["openDate"], ", marketCount=", jp[idx]["marketCount"] ) 
         
         #Para cada partida, obtem todos os tipos de aposta para uma determinada partida
         #Obtendo todos os tipos de aposta para uma determinada partida
         eventID = jp[idx]["event"]["id"] #Para testar
         filtro='{"filter": {"eventIds": [ "' + eventID +'" ] }, "maxResults": "200", "marketProjection": [ "COMPETITION", "EVENT", "EVENT_TYPE", "RUNNER_DESCRIPTION", "RUNNER_METADATA", "MARKET_START_TIME" ] }'
         jm = api.obtemTodosMercadosDasPartidas(json_req=filtro)
         #if("marketId" in jm[0] ): #Tem futebol nesse esquemex
         #print( [(jm[idx2]["marketId"], jm[idx]["marketName"] ) for idx2 in range(len(jm)) ] )
         #goalLineMarketIds = [ jm[idx2]["marketId"]  for idx2 in range(len(jm)) if jm[idx2]["marketName"].startswith('Over/Under')  ] #Todos os GoalLine (Under/Over)
         #print("GoalLines=", [ jm[idx2]["marketName"]  for idx2 in range(len(jm)) if jm[idx2]["marketName"].startswith('Over/Under') ] )
         for idxMid in range(len(jm)): #Para cada mercado que seja Under/Over nessa partida
            if( jm[idxMid]["marketName"].startswith('Over/Under') ) : #Apenas Under/Over importa
               #print("Mercado #", idxMid, " ID=", jm[idxMid]["marketId"], ", Nome=", jm[idxMid]["marketName"] )
      
               #Obtendo as odds de cada um dos mercados
               marketId = jm[idxMid]["marketId"]
               dic_markets = {} #Mapear selectionID com runnerName
               for r in [ jm[ind]  for ind in range(len(jm)) if jm[ind]["marketId"] == marketId  ][0]["runners"] : #Olhando os runners
                  dic_markets[ r["selectionId"] ] = r["runnerName"]
               #print( [ jm[idx]  for idx in range(len(jm)) if jm[idx]["marketId"] == marketId  ] ) #Json inteiro do exemplo
               filtro= '{ "marketIds": ["' + marketId + '"], "priceProjection": { "priceData": ["EX_BEST_OFFERS", "EX_TRADED"], "virtualise": "true" } }'
               jo = api.obtemOddsDosMercados(json_req=filtro)
               
               for idxRun in range(len(jo)): #Para cada odd disponivel nessa selecao                  
                  runners = jo[idxRun]["runners"]
                  for idxSel in range(len(runners)): #Para cada opcao de selecao 
                     selectionId = runners[idxSel]["selectionId"]
                     #print( "Id=", selectionId, "Sel=", dic_markets[selectionId] )
                     #for idxBack in range(len(jo[idxRun]["runners"][idxSel]["ex"]["availableToBack"])): #Mostrando odds de Back
                        #print( "OddsBack#",idxBack,"=", jo[idxRun]["runners"][idxSel]["ex"]["availableToBack"][idxBack] )
                     #for idxLay in range(len(jo[idxRun]["runners"][idxSel]["ex"]["availableToLay"])): #Mostrando odds Lay
                        #print( "OddsLay#",idxLay,"=", jo[idxRun]["runners"][idxSel]["ex"]["availableToLay"][idxLay] )
                     if( len(jo[idxRun]["runners"][idxSel]["ex"]["availableToBack"]) >= 1 ): #Se tem odds
                        stats = SoccerStats(url='http://bot-ao.com/stats.json') #Classe para obter o Json
                        jstat = stats.getStats()
                        idPartidaBetFair = [ jp[x]["event"]["id"] for x in range(len(jp)) ] #IDs da API
                        idPartidaJson = [ jstat[x]["id_bf"] for x in range(len(jstat)) ] #IDs do Json
                        idsValidos = [id for id in idPartidaJson if id in idPartidaBetFair] #IDs que aparecem em ambos
                        self.estatisticas = stats #salva para uso posterior
                        #if( jp[idx]["event"]["id"] in idsValidos ): #Exibir apenas o que tem estatistica
                        if(True):
                           print("Partida# ",idx,": ID=",jp[idx]["event"]["id"], ", Nome=", jp[idx]["event"]["name"], ", timezone=",jp[idx]["event"]["timezone"], ", openDate=", jp[idx]["event"]["openDate"], ", marketCount=", jp[idx]["marketCount"],
                                 "Mercado #", idxMid, " ID=", jm[idxMid]["marketId"], ", Nome=", jm[idxMid]["marketName"],
                                 "SelectionId=", selectionId, "Sel=", dic_markets[selectionId],
                                 "Melhor Odds: ", jo[idxRun]["runners"][idxSel]["ex"]["availableToBack"][0]["price"])
                           bdIdEquipe = self.bd.salvaTabelaTimes( nome= jp[idx]["event"]["name"] )
                           bdIdBf = self.bd.salvaTabelaPartidas( idBF=jp[idx]["event"]["id"], idEquipes=bdIdEquipe, openDate=jp[idx]["event"]["openDate"] ) #bdIdBf == idx
                           bdIdMercado = self.bd.salvaTabelaMercados( nome=jm[idxMid]["marketName"] )
                           bdIdSelecao = self.bd.salvaTabelaSelecoes( idMercado=bdIdMercado, nome=dic_markets[selectionId] )
                           import time    
                           timeStamp = time.strftime('%Y-%m-%d %H:%M:%S')
                           bdRetorno = self.bd.salvaTabelaOdds( idPartida=bdIdBf, idSelecao=bdIdSelecao, timestamp=timeStamp, bestOdd=jo[idxRun]["runners"][idxSel]["ex"]["availableToBack"][0]["price"] )
                           
                           
                     else: #Sem odds para esse mercado!
                        pass #Ta de boas
                        #print( "Partida# ",idx,": ID=",jp[idx]["event"]["id"], ", Nome=", jp[idx]["event"]["name"], ", timezone=",jp[idx]["event"]["timezone"], ", openDate=", jp[idx]["event"]["openDate"], ", marketCount=", jp[idx]["marketCount"],
                        #      "Mercado #", idxMid, " ID=", jm[idxMid]["marketId"], ", Nome=", jm[idxMid]["marketName"],
                        #      "SelectionId=", selectionId, "Sel=", dic_markets[selectionId], 
                        #      " - Sem ODDS!" )
                     
                  #Aqui ele teoricamente decidiria se apostaria ou nao. Variavel foi definida acima
                  if( False ): #Nao aposta
                     #Se apostasse...
                     filtro='{ "marketId": "'+ marketId +'", "instructions": [ { "selectionId": "' + str(selectionId) + '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "2", "price": "3", "persistenceType": "LAPSE" } } ] }'
                     #ja = api.aposta(json_req=filtro) #Cuidado
      
      #Consultando as apostas atuais
      filtro = '{"marketIds":[],"orderProjection":"ALL","dateRange":{}}' #Poderia filtrar pelo marketId, mas deixa
      jaa = api.consultaApostasEfetuadas(json_req=filtro)
      print("Tem agora ", str(len(jaa["currentOrders"])), " apostas")
      
      #Vendo se a aposta teve retorno positivo ou negativo
      filtro='{"marketIds":[],"priceProjection":{"priceData":["EX_BEST_OFFERS"]}}, "id": 1}' #Precisa do marketId!
      jra = api.consultaResultadoApostas(json_req=filtro)
   
   """
   Metodo principal do Bot. A logica principal. O camisa nove. O macaco da bola azul.
   """
   def roda(self):
      self.soccerID = self.obtemIdDoFutebol(eventTypeName="Soccer", lazyMode=True) #Sempre eh 1
      #self.obtemListaDePartidas(horas=0, minutos=30) #Partidas que comecam nos proximos 30 minutos
      self.ExibeTodosDados(horas=1, minutos=30) #Refatorar isso depois

"""
Uma classe apenas para obter os dados do Json, com estatisticas.
"""
class SoccerStats():
   def __init__(self, url='http://bot-ao.com/stats.json'):
      self.url = url
   def getStats(self):
      try:
         from urllib.request import urlopen
      except ImportError:
         from urllib2 import urlopen
      import json 
      try:
         with urlopen( self.url ) as url:
            data = json.loads(url.read().decode())
            #print(data)
            return(data)
      except AttributeError:
         url = urlopen( self.url )
         data = json.loads(url.read().decode())
         return(data)
"""
Classe que se conecta com um banco de dados.
"""
class BancodeDados():
   def __init__(self):
      config = {
        'user': 'hg1fo340',
        'password': 'rr842135',
        'host': 'bot-ao.com',
        'database': 'hg1fo340_bot',
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
          
if __name__ == "__main__":                    
   #input("Continuando...")
   
   cf = ConfigFile()
   u, s, a = cf.leConfiguracoesDoArquivo() #Informacoes estao armazenadas em um arquivo
   api = BetfairAPI(usuario=u, senha=s, api_key=a)
   print("Session Token=",api.sessionToken)
   bot = BotFair(api, bdOption=True)
   bot.roda()
   