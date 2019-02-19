from __future__ import print_function
from Hush import usuarioAPI, senhaAPI, APIKey, statsURL, habilitarBD
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
      stats = SoccerStats(url=statsURL) #Classe para obter o Json
      self.estatisticas = stats #salva para uso posterior
         
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
      #for idx in range(len(self.jPartidas)):
      #   print( "Partida# ",idx,": ID=",self.jPartidas[idx]["event"]["id"], ", Nome=", self.jPartidas[idx]["event"]["name"], ", timezone=",self.jPartidas[idx]["event"]["timezone"], ", openDate=", self.jPartidas[idx]["event"]["openDate"], ", marketCount=", self.jPartidas[idx]["marketCount"] ) 
      
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
      x = self.obtemListaDePartidas(horas=0, minutos=30) #Partidas que comecam nos proximos 30 minutos
      #self.ExibeTodosDados(horas=1, minutos=30) #Refatorar isso depois
      
   """
   Metodo que coleta as odds de jogos em andamento
   """
   def atualizaOdds(self):
      filtro=('{"filter":{'
         ' "inPlayOnly" : true, '
         ' "sort":"FIRST_TO_START","maxResults":"100"]}')
      self.jPartidas = api.obtemPartidasDeFutebol(json_req=filtro) #Obtendo o Json das partidas
      print( self.jPartidas )
      for idx in range(len(self.jPartidas)):
         print( "Partida# ",idx,": ID=",self.jPartidas[idx]["event"]["id"], ", Nome=", self.jPartidas[idx]["event"]["name"], ", timezone=",self.jPartidas[idx]["event"]["timezone"], ", openDate=", self.jPartidas[idx]["event"]["openDate"], ", marketCount=", self.jPartidas[idx]["marketCount"] ) 
   
   #Armazena tudo em banco de dados
   def salvaDadosBD(self, dc=None):
      #Armazena tudo no BD
      bdIdEquipe = self.bd.salvaTabelaTimes( nome= dc["BetFair"]["event"]["name"] )
      bdIdBf = self.bd.salvaTabelaPartidas( idBF=dc["BetFair"]["event"]["id"], idEquipes=bdIdEquipe, openDate=dc["BetFair"]["event"]["openDate"] ) #bdIdBf == idx
      print(dc["mercados"])
      for uo in range(1,8):
         bdIdMercado = self.bd.salvaTabelaMercados( nome=dc["mercados"]["Over/Under "+str(uo)+".5 Goals"] )
         bdIdSelecao = self.bd.salvaTabelaSelecoes( idMercado=bdIdMercado, nome=dc["selecoes"]["Under "+str(uo)+".5 Goals"] )
      import time    
      timeStamp = time.strftime('%Y-%m-%d %H:%M:%S')
      try:
         for uo in range(1,8):
            bdRetorno = self.bd.salvaTabelaOdds( idPartida=bdIdBf, idSelecao=bdIdSelecao, timestamp=timeStamp, bestOdd=dc["odds"]["Under "+str(uo)+".5 Goals"] )
      except KeyError:
         pass #Sim, ignoro por enquanto
      
   # Retorna todas as melhores Odds de todos os mercados Under/Over para a partida especificada. Faz apenas duas requisicoes!
   def getOddsFromPartida(self, idBF=None):
      mercados = ['"OVER_UNDER_' + str(idg) + '5"' for idg in range(0,8)] #Todos os Unver/Over, menos 8
      filtro='{"filter": {"eventIds": [ "' + idBF +'" ], "marketTypeCodes":['+ ", ".join(mercados) +'] }, "maxResults": "200", "marketProjection": [ "RUNNER_DESCRIPTION" ] }'
      mercadosBF = api.obtemTodosMercadosDasPartidas(json_req=filtro)
      #mercadosBF = api.obtemTodosTiposDeMercados() #Todos os tipos de mercados
      
      selections = ['"' + str(mercadoBF["marketId"])+'"' for mercadoBF in mercadosBF for idx in range(len(mercadoBF["runners"]))]
      mercados = { mercadoBF["runners"][idx]["selectionId"] : mercadoBF["runners"][idx]["runnerName"]  for mercadoBF in mercadosBF for idx in range(len(mercadoBF["runners"])) } #Qual codigo de mercado eh de qual tipo
      mercadosM = { mercadoBF["marketName"] : mercadoBF["marketId"]  for mercadoBF in mercadosBF  } 
      selectionsM = { mercadoBF["runners"][idx]["runnerName"] : mercadoBF["runners"][idx]["selectionId"] for mercadoBF in mercadosBF for idx in range(len(mercadoBF["runners"])) } #Inverso do anterior
      
      filtro= '{ "marketIds": [' + ", ".join(selections) + '], "priceProjection": { "priceData": ["EX_BEST_OFFERS"], "virtualise": "true" } }'
      odds = api.obtemOddsDosMercados(json_req=filtro)
      
      melhoresOdds = { mercados[odds[idxRun]["runners"][idxSel]["selectionId"]]  :  odds[idxRun]["runners"][idxSel]["ex"]["availableToBack"][0]["price"]  for idxRun in range(len(odds))  for idxSel in range(len(odds[idxRun]["runners"])) if len(odds[idxRun]["runners"][idxSel]["ex"]["availableToBack"]) >= 1 }
      
      return melhoresOdds, selectionsM, mercadosM
   
   #Avalia os dados, e define se faz aposta ou nao
   def avaliaSeApostaOuNao(self, dc=None):
      odds = dc["odds"]
      for uo in range(1,8): #Percorrer todos os Under/Over
         goalline = 0 #jogo_selecionado.AH_Away
         COMISSAO_BETFAIR = 0.05
         minimo_indice_para_apostar = 0.02 + COMISSAO_BETFAIR
         percentual_de_kelly = 0.2
         maximo_da_banca_por_aposta = 15
         
         try:
            probU = 1.0/odds["Under "+str(uo)+".5 Goals"]/(1.0/odds["Under "+str(uo)+".5 Goals"] + 1.0/odds["Over "+str(uo)+".5 Goals"])
            probU_diff=abs(probU-0.5)
            #print(probU)
         except KeyError: #Falta algum mercado
            pass
            #print("Sem mercado")
         s_g=dc["Json"]['gh']+dc["Json"]['ga']
         s_c=dc["Json"]['ch']+dc["Json"]['ca']
         s_s=dc["Json"]['sh']+dc["Json"]['sa']
         s_da=dc["Json"]['dah']+dc["Json"]['daa'] 
         s_r=dc["Json"]['rh']+dc["Json"]['ra']
         d_g=abs(dc["Json"]['gh']-dc["Json"]['ga'])
         d_c=abs(dc["Json"]['ch']-dc["Json"]['ca'])
         d_s=abs(dc["Json"]['sh']-dc["Json"]['sa'])                                         
         d_da=abs(dc["Json"]['dah']+dc["Json"]['daa'])
         
         goal_diff=goalline-s_g
         mod0=int(goalline%1==0)
         #mod25=int(goalline%1==0.25)
         #mod50=int(goalline%1==0.50)
         #mod75=int(goalline%1==0.75)
         
         #pl_por_odds = 0.1389 + -0.0118 * s_g + -0.0037 * s_c + -0.0004 * s_da + -0.007  * s_s + -0.0324 * d_g + -0.0032 * d_c + -0.001  * d_da + 0.103  * goal_diff + 0.0311 * mod0 + 0.0359 * mod25 + 0.0231 * mod50 + -0.3799 * probUnder; 
         pl_u= 0.0091 +     -0.0761 * s_g +     -0.0026 * s_c +     -0.0002 * s_da +     -0.0068 * s_s +     -0.0218 * s_r +     -0.0248 * d_g +     -0.0012 * d_da +     -0.0014 * d_s +      0.0746 * goalline +     -0.3222 * probU_diff +      0.0002 * mod0
         if( pl_u >= minimo_indice_para_apostar): 
            percent_da_banca = pl_por_odds * percentual_de_kelly
            if (percent_da_banca >  maximo_da_banca_por_aposta) :
               percent_da_banca=maximo_da_banca_por_aposta
            return True, uo
         else:
            return False, -1
   
   #Provavel metodo para apostar com base no Json
   def BotFairGo(self):
      #print("Oe")
      jstat = self.estatisticas.getStats() #Atualizo o Json
      partidasJson = [ jstat[x]["home"]+" v "+jstat[x]["away"] for x in range(len(jstat)) ] #Partidas no formato MandanteXVisitante do Json
      #print(partidasJson)
      #print("Mae")
      self.obtemListaDePartidas(horas=3, minutos=30)
      partidasBF = [self.jPartidas[idx]["event"]["name"] for idx in range(len(self.jPartidas))]
      #print(partidasBF)
      self.dadosConsolidados = [] #Lista que une ambos as fontes
      #print(self.jPartidas[0])
      for p1 in range(len(partidasJson)):
         min = 9 #Filtro
         min_n = ""
         for p2 in range(len(partidasBF)):
            if( self.estatisticas.LD(partidasJson[p1], partidasBF[p2]) <= min ):
               #print("PB=", p2, " encontrado!")
               min = self.estatisticas.LD(partidasJson[p1], partidasBF[p2] )
               min_n = partidasBF[p2]
            #if( self.estatisticas.LD(p1, p2) <= 11 ):
         if( min_n != "" ):
            #print("PJ=", p1, "PB=", min_n, "LD=", min )
            self.dadosConsolidados.append( {"nomeBF" : min_n, "nomeJ" : partidasJson[p1], "BetFair" : self.jPartidas[p2], "Json" : jstat[p1],} )
      for dc in self.dadosConsolidados:
         print(dc["nomeBF"])
         odds, selecoes, mercados = self.getOddsFromPartida(idBF = dc["BetFair"]["event"]["id"] )
         dc["odds"] = odds
         dc["selecoes"] = selecoes
         dc["mercados"] = mercados
         #print(odds)
         
         ret, uo = self.avaliaSeApostaOuNao(dc)
         if( ret == True ):
            print("Apostarei", percent_da_banca, " na selecao ", "Under "+str(uo)+".5 Goals", ", odds=", odds["Under "+str(uo)+".5 Goals"], ", jogo=", dc["nomeBF"], " .")
            x = 1/0
            filtro='{ "marketId": "'+ marketId +'", "instructions": [ { "selectionId": "' + str(selecoes["Under "+str(uo)+".5 Goals"] ) + '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "2", "price": "3", "persistenceType": "LAPSE" } } ] }'
            #ja = api.aposta(json_req=filtro) #Cuidado
         #print( dc["nomeBF"], dc["nomeJ"], dc["Json"]["daH"] )
         #self.salvaDadosBD(dc) #Ver se reativa 
      
         
if __name__ == "__main__":
   parser = ArgumentParser()
   parser.add_argument("-p", "--partidas", action="store_true", dest="partidas", help="Coleta apenas as proximas partidas")
   parser.add_argument("-o", "--odds", action="store_true", dest="odds", help="Coleta apenas as odds de jogos correntes")
   parser.add_argument("-b", "--bot", action="store_true", dest="bot", help="Aposta usando o Json como base")
   parser.add_argument("-d", "--horas", dest="horas", help="Horas de antecedencia da partida para coletar odds", default=0)
   parser.add_argument("-m", "--minutos", dest="minutos", help="Minutos de antecedencia da partida para coletar odds", default=30)
   parser.add_argument("-f", "--frequencia", dest="freq", help="Frequencia, em segundos, para coletar as odds", default=30)
   args = parser.parse_args()
   print(args)

   #input("Continuando...")
   u, s, a = usuarioAPI, senhaAPI, APIKey
   api = BetfairAPI(usuario=u, senha=s, api_key=a)
   print("Session Token=",api.sessionToken)
   bot = BotFair(api, bdOption=habilitarBD )
   #bot.roda()
   if args.bot:
      while True:
         bot.BotFairGo()
         import time
         time.sleep( 15 )
   if args.odds:
      bot.atualizaOdds()
   if args.partidas:
      while True:
         try:
            bot.ExibeTodosDados(horas=int(args.horas), minutos=int(args.minutos))
         except Exception:
            print("Erro!")
            raise
   