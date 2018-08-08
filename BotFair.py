from __future__ import print_function
from Hush import usuarioAPI, senhaAPI, APIKey, statsURL
from BD import BancodeDados
from Stats import SoccerStats
from RestAPI import BetfairAPI
from argparse import ArgumentParser

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
      self.soccerID = self.obtemIdDoFutebol(eventTypeName="Soccer", lazyMode=True) #Sempre eh 1
         
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
                        stats = SoccerStats(url=statsURL) #Classe para obter o Json
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
      self.obtemListaDePartidas(horas=0, minutos=30) #Partidas que comecam nos proximos 30 minutos
      #self.ExibeTodosDados(horas=1, minutos=30) #Refatorar isso depois
      
   """
   Metodo que coleta as odds de jogos em andamento
   """
   def atualizaOdds(self):
      filtro=('{"filter":{'
         ' "inPlayOnly" : true, '
         ' "sort":"FIRST_TO_START","maxResults":"100"]}')
         #'"marketProjection":["RUNNER_METADATA"]}')
      self.jPartidas = api.obtemPartidasDeFutebol(json_req=filtro) #Obtendo o Json das partidas
      print( self.jPartidas )
      for idx in range(len(self.jPartidas)):
         print( "Partida# ",idx,": ID=",self.jPartidas[idx]["event"]["id"], ", Nome=", self.jPartidas[idx]["event"]["name"], ", timezone=",self.jPartidas[idx]["event"]["timezone"], ", openDate=", self.jPartidas[idx]["event"]["openDate"], ", marketCount=", self.jPartidas[idx]["marketCount"] ) 
      
if __name__ == "__main__":
   parser = ArgumentParser()
   parser.add_argument("-p", "--partidas", action="store_false", dest="partidas", help="Coleta apenas as proximas partidas")
   parser.add_argument("-o", "--odds", action="store_false", dest="odds", help="Coleta apenas as odds de jogos correntes")
   parser.add_argument("-d", "--horas", dest="horas", help="Horas de antecedencia da partida para coletar odds", default=0)
   parser.add_argument("-m", "--minutos", dest="minutos", help="Minutos de antecedencia da partida para coletar odds", default=30)
   parser.add_argument("-f", "--frequencia", dest="freq", help="Frequencia, em segundos, para coletar as odds", default=30)
   args = parser.parse_args()
   print(args)

   #input("Continuando...")
   u, s, a = usuarioAPI, senhaAPI, APIKey
   api = BetfairAPI(usuario=u, senha=s, api_key=a)
   print("Session Token=",api.sessionToken)
   bot = BotFair(api, bdOption=True)
   #bot.roda()
   if args.odds:
      bot.atualizaOdds()
   if args.partidas:
      bot.ExibeTodosDados(horas=0, minutos=30)
   