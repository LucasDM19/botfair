#coding: utf-8
from __future__ import print_function
from Hush import usuarioAPI, senhaAPI, APIKey, statsURL, habilitarBD
from BD import BancodeDados
from Stats import SoccerStats
from RestAPI import BetfairAPI
from argparse import ArgumentParser
import os, pickle
from datetime import datetime
from datetime import timedelta

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
   
   """
   Obtem a lista de partidas que comecarao nos proximos trinta minutos.
   Baseado na que obtem os dados Win de Londres.
   """   
   def obtemListaPartidasAndamento(self, horas=0, minutos=45):
      import datetime
      #now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
      now_fuso = datetime.datetime.now() + datetime.timedelta(hours=3, minutes=0) # Horário de Londres
      faz_45_minutos = (now_fuso + datetime.timedelta(hours=horas, minutes=-1*minutos-15)).strftime('%Y-%m-%dT%H:%M:%SZ')
      daqui_45_minutos = (now_fuso + datetime.timedelta(hours=horas, minutes=-1*minutos+15)).strftime('%Y-%m-%dT%H:%M:%SZ')
      #print("Inicio e fim:", faz_45_minutos, daqui_45_minutos)
      filtro=('{"filter":{"eventTypeIds":["1"],  '
         ' "turnsInPlay" : true, "inPlayOnly" : true, '
         ' "marketStartTime":{"from":"' + faz_45_minutos + '", "to":"' + daqui_45_minutos + '"}},'
         ' "sort":"FIRST_TO_START","maxResults":"100",'
         '"marketProjection":["RUNNER_DESCRIPTION","EVENT","MARKET_START_TIME"]}')
      self.jPartidas = api.obtemTodosMercadosDasPartidas(json_req=filtro) #Obtendo o Json das partidas
      #print("Teste", self.jPartidas) #[p for p in self.jPartidas ][1] )

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
      
      #mercadosM = { mercadoBF["marketName"] : mercadoBF["marketId"]  for mercadoBF in mercadosBF  } 
      mercadosM = { mercadoBF["runners"][idx]["selectionId"] : mercadoBF["marketId"]  for mercadoBF in mercadosBF for idx in range(len(mercadoBF["runners"])) } #Qual codigo de mercado eh de qual tipo
      
      selectionsM = { mercadoBF["runners"][idx]["runnerName"] : mercadoBF["runners"][idx]["selectionId"] for mercadoBF in mercadosBF for idx in range(len(mercadoBF["runners"])) } #Inverso do anterior
      
      filtro= '{ "marketIds": [' + ", ".join(selections) + '], "priceProjection": { "priceData": ["EX_BEST_OFFERS"], "virtualise": "true" } }'
      odds = api.obtemOddsDosMercados(json_req=filtro)
      
      melhoresOdds = { mercados[odds[idxRun]["runners"][idxSel]["selectionId"]]  :  odds[idxRun]["runners"][idxSel]["ex"]["availableToBack"][0]["price"]  for idxRun in range(len(odds))  for idxSel in range(len(odds[idxRun]["runners"])) if len(odds[idxRun]["runners"][idxSel]["ex"]["availableToBack"]) >= 1 }
      
      return melhoresOdds, selectionsM, mercadosM
   
   #Avalia os dados, e define se faz aposta ou nao
   def avaliaSeApostaOuNao(self, dc=None):
      odds = dc["odds"]
      merc_gols = [int(i.replace("Under ","").replace(".5 Goals","").replace("Over ","")) for i in odds.keys()]
      merc_gols = list(set(merc_gols))
      dic_op_aposta = {} # Todas as opções válidas de apostar
      dic_tipo_aposta = {} # Qual fica melhor entre Under ou Over
      #print("gols=", merc_gols, "<>", dc["nomeBF"] )
      for uo in merc_gols: #range(1,8): #Percorrer todos os Under/Over que estiverem disponiveis
         #goalline = 0 #jogo_selecionado.AH_Away
         goalline = uo + 0.5 # Parece que goalline eh o total de gols da aposta
         COMISSAO_BETFAIR = 0.05
         minimo_indice_para_apostar = 0.02 + COMISSAO_BETFAIR
         maximo_da_banca_por_aposta = 0.10 #0.10 ideal
         
         try:
            oddsU = odds["Under "+str(uo)+".5 Goals"]
            #probU = 1.0/odds["Under "+str(uo)+".5 Goals"]/(1.0/odds["Under "+str(uo)+".5 Goals"] + 1.0/odds["Over "+str(uo)+".5 Goals"])
            #probU_diff=abs(probU-0.5)
            #print(probU, oddsU, uo)
         except KeyError: #Falta algum mercado
            pass
            #print("Sem mercado")
            #probU_diff=0
            oddsU = 0
         try:
            oddsO = odds["Over "+str(uo)+".5 Goals"]
         except KeyError: #Falta algum mercado
            pass
            oddsO = 0
         s_g=dc["Json"]['gH']+dc["Json"]['gA']
         s_c=dc["Json"]['cH']+dc["Json"]['cA']
         s_s=dc["Json"]['sH']+dc["Json"]['sA']
         s_da=dc["Json"]['daH']+dc["Json"]['daA'] 
         #s_r=dc["Json"]['rh']+dc["Json"]['ra']
         s_r = dc["Json"]['sr']
         d_g=abs(dc["Json"]['gH']-dc["Json"]['gA'])
         d_c=abs(dc["Json"]['cH']-dc["Json"]['cA'])
         d_s=abs(dc["Json"]['sH']-dc["Json"]['sA'])                                         
         d_da=abs(dc["Json"]['daH']+dc["Json"]['daA'])
         handicap = dc["Json"]['handicap']
         
         goal_diff=goalline-s_g
         #print("Teste Diff=", goal_diff)
         mod0=int(goalline%1==0)
         #mod25=int(goalline%1==0.25)
         #mod50=int(goalline%1==0.50)
         #mod75=int(goalline%1==0.75)
         import math 
         X=s_g/math.log(s_s+0.75)
         #Y=Math.pow(s_s,1.5)
         L1=math.log(1+s_s)
         L2=math.log(1+L1)
         L3=math.log(1+L2)
         #W = 0 #W=Number(home.includes('Women')) // Adaptar isso
         W = 0 if "Women" not in dc["nomeBF"] else 1
         
         #Equacao da Bet365
         #if( goal_diff < 1.00 or goal_diff > 4.25 or d_g>4 or (oddsU < 1.8 or oddsU > 2.25 ) ): plU_por_odds = -1 #or oddsU > 2.25
         #else: plU_por_odds = 0.0043995738960802555 * s_g +-0.010405398905277252 * s_c +-0.0003965592562558247 * s_da +-0.028474957515031863 * s_s +-0.06218665838241577 * d_g +-0.0015331107511449215 * d_da +0.1922848874872381 * goal_diff +0.16835627605647394 * oddsU +0.07048862983366744 * L1 +0.23551936088359587 * L2 +-0.30258931180186993 * L3 +-0.031020960578842485 * X +0.0678747147321701 * W +-0.46591539790406256
         
         # Criterios Bot da Bet365
         #if( plU_por_odds >= minimo_indice_para_apostar): 
         #   percent_da_banca = plU_por_odds * percentual_de_kelly
         #   if (percent_da_banca >  maximo_da_banca_por_aposta) :
         #      percent_da_banca=maximo_da_banca_por_aposta
         #   #return True, uo, percent_da_banca
         #   dic_op_aposta[uo] = percent_da_banca
         ##else:
         #   #return False, -1, 0
         
         #Equacao esepcifica Betfair
         d_goal_bf = uo-s_g
         L1=math.log(1+abs(d_goal_bf))
         M1=math.log(1+oddsU)
         d_hand_tc=abs(handicap)
         #breakpoint()
         if( (goal_diff < 1.00 or goal_diff > 4.25) or (oddsO <= 1.1 or oddsO > 2.1 ) ): kelly_OVER = -1 
         else: kelly_OVER=0.0196131*s_c+0.0098857*s_s+-0.0247524*s_r+-0.016744*d_c+0.1128363*d_hand_tc+-0.251764*d_goal_bf+-2.3750849*oddsU+-0.5023665*L1+7.1751788*M1+-2.6701679
         if( (goal_diff < 1.00 or goal_diff > 4.25) or (oddsU <= 1.1 or oddsU > 2.1 ) ): kelly_UNDER = -1 
         else: kelly_UNDER=-0.004704*s_s+0.0105575*s_r+-0.0289218*d_g+-0.0007306*d_da+0.0017628*d_s+-0.1907982*d_goal_bf+-2.0169732*oddsO+0.0169774*W+1.2183641*L1+5.8118938*M1+-3.1709947
         
         #eh so apostar de kelly >1% , e apostar metade
         minimo_kelly = 0.01
         percentual_de_kelly = 0.25 # apostar metade
         melhor_kelly = max(kelly_OVER, kelly_UNDER) # Escolho o mais alto
         tipo_aposta = "Under" if kelly_UNDER >= kelly_OVER else "Over"
         print("Avaliando:", dc["nomeBF"], ", diff=", goal_diff, ",oddsO=",oddsO, ",oddsU=", oddsU,",Json=", dc["Json"], ", Kelly_OVER=", kelly_OVER, ", Kelly_UNDER=", kelly_UNDER, "%banca=", melhor_kelly * percentual_de_kelly, ",melhor=", melhor_kelly, ",tipo=", tipo_aposta, ",UO=", uo )
         if( melhor_kelly > minimo_kelly ):
            percent_da_banca = melhor_kelly * percentual_de_kelly
            if (percent_da_banca >  maximo_da_banca_por_aposta): percent_da_banca=maximo_da_banca_por_aposta
            dic_op_aposta[uo] = percent_da_banca #/100 # Estava muito alto
            dic_tipo_aposta[uo] = tipo_aposta
               
      dic_filtro = dict(filter(lambda elem: elem[1] > 0,dic_op_aposta.items()))
      if( len(dic_filtro) == 0 ):
         #print("Sem nada para apostar", dc["nomeBF"], len(dic_op_aposta) )
         return False, "nada", -1, 0 # Sem nada para fazer
      #breakpoint()
      return True, dic_tipo_aposta[max(dic_filtro, key=dic_filtro.get)], max(dic_filtro, key=dic_filtro.get), dic_filtro[max(dic_filtro, key=dic_filtro.get)] # Retorna a melhor seleção de odd + o valor a ser apostado
   
   #Consulta a lista de apostas em andamento
   def verificaSeJaApostouOuNao(self, nome_jogo_BF=None ):
      return nome_jogo_BF not in self.dic_apostas
      
      #filtro='{ "betIds": [ "'+ bet_id +'" ] }'
      filtro='{  }'
      info = self.api.consultaApostasEfetuadas(json_req=filtro)
      #for r in info['currentOrders']:
      #   bet_id = info['currentOrders'][0]
      print( info ) 
      # Sem nada: {'currentOrders': [], 'moreAvailable': False}
      # {'currentOrders': [{'betId': '207257578280', 'marketId': '1.171651976', 'selectionId': 47972, 'handicap': 0.0, 'priceSize': {'price': 1.83, 'size': 10.0}, 'bspLiability': 0.0, 'side': 'BACK', 'status': 'EXECUTION_COMPLETE', 'persistenceType': 'LAPSE', 'orderType': 'LIMIT', 'placedDate': '2020-08-02T13:20:32.000Z', 'matchedDate': '2020-08-02T13:20:37.000Z', 'averagePriceMatched': 1.84, 'sizeMatched': 10.0, 'sizeRemaining': 0.0, 'sizeLapsed': 0.0, 'sizeCancelled': 0.0, 'sizeVoided': 0.0, 'regulatorCode': 'MALTA LOTTERIES AND GAMBLING AUTHORITY'}], 'moreAvailable': False}
      #teste = '1.171651976' #marketId
      return info
   
   #Provavel metodo para apostar com base no Json
   def BotFairGo(self):
      def salvaProgresso(lista, nome_arquivo): # Aqui, por enquanto
         with open(nome_arquivo, 'wb') as f:
            pickle.dump(lista, f)
      nome_aposta_pickle = 'apostas.pkl'
      if( os.path.isfile(nome_aposta_pickle) ): # Devo continuar a processar a lista
         with open(nome_aposta_pickle, 'rb') as f:
            self.dic_apostas = pickle.load(f)
      else:
         self.dic_apostas = {} # Só gera arquivo depois da primeira aposta
      jstat = self.estatisticas.getStats() #Atualizo o Json
      partidasJson = [ jstat[x]["home"]+" v "+jstat[x]["away"] for x in range(len(jstat)) ] #Partidas no formato MandanteXVisitante do Json
      self.obtemListaPartidasAndamento(horas=0, minutos=45) # Apenas final do primeiro tempo
      #partidasBF = list(set( [self.jPartidas[idx]["event"]["name"] for idx in range(len(self.jPartidas))] )) # Valores unicos
      #Exemplo: {'marketId': '1.171944455', 'marketName': 'Over/Under 1.5 Goals', 'marketStartTime': '2020-08-16T11:30:00.000Z', 'totalMatched': 16989.794560000002, 'runners': [{'selectionId': 1221385, 'runnerName': 'Under 1.5 Goals', 'handicap': 0.0, 'sortPriority': 1}, {'selectionId': 1221386, 'runnerName': 'Over 1.5 Goals', 'handicap': 0.0, 'sortPriority': 2}], 'event': {'id': '29949215', 'name': 'Cercle Brugge v Antwerp', 'countryCode': 'BE', 'timezone': 'GMT', 'openDate': '2020-08-16T11:30:00.000Z'}}
      partidasBF = [self.jPartidas[idx] for idx in range(len(self.jPartidas)) if 'Over/Under' in self.jPartidas[idx]['marketName'] ] # Filtrei
      self.dadosConsolidados = [] #Lista que une ambos as fontes
      for p1 in range(len(partidasJson)):
         min_ld = 7 #Jaro v SJK 2 ( Hodd v Skeid ) deu 8
         min_n = ""
         for p2 in range(len(partidasBF)):
            if( self.estatisticas.LD(partidasJson[p1], partidasBF[p2]["event"]["name"] ) <= min_ld ):
               #breakpoint()
               min_ld = self.estatisticas.LD(partidasJson[p1], partidasBF[p2]["event"]["name"] )
               min_n =  partidasBF[p2]["event"]["name"]
            if( min_n != "" ):
               #breakpoint() #self.jPartidas[p2]["event"]["name"]
               dc_odds, dc_selecoes, dc_mercados = self.getOddsFromPartida(idBF = partidasBF[p2]["event"]["id"] ) # Falta essa informação
               dc = {"nomeBF" : min_n, "nomeJ" : partidasJson[p1], "BetFair" : partidasBF[p2], "Json" : jstat[p1], "odds": dc_odds, "selecoes": dc_selecoes, "mercados": dc_mercados, }
               #self.dadosConsolidados.append( {"nomeBF" : min_n, "nomeJ" : partidasJson[p1], "BetFair" : partidasBF[p2], "Json" : jstat[p1], "odds": dc_odds, "selecoes": dc_selecoes, "mercados": dc_mercados, } )
               
            #for dc in self.dadosConsolidados:
               devo_apostar, tipo_aposta, uo, percent_da_banca = self.avaliaSeApostaOuNao(dc)
               nao_apostei_ainda = self.verificaSeJaApostouOuNao(nome_jogo_BF=dc["nomeBF"] )
               retorno_saldo = self.api.obtemSaldoDaConta() #{'availableToBetBalance': 177.94, 'exposure': 0.0, 'retainedCommission': 0.0, 'exposureLimit': -10000.0, 'discountRate': 0.0, 'pointsBalance': 20, 'wallet': 'UK'}
               saldo = int(retorno_saldo['availableToBetBalance'])
               stack_aposta = round(percent_da_banca*saldo,2) # Olha o 0.5 de precaução aí
               #if(stack_aposta > 5): stack_aposta = 5.0 # Teste
               valor_minimo_aposta = 3 # Equivalente a 2 GBP (2.62) - na verdade 3 EUR
               
               #if( uo != -1): breakpoint()  # Importante
               if( devo_apostar and nao_apostei_ainda and stack_aposta >= valor_minimo_aposta ):
                  #breakpoint()
                  odd_selecionada = dc["odds"][tipo_aposta+" "+str(uo)+".5 Goals"] #Under ou Over
                  if len([self.jPartidas[idx]['marketId'] for idx in range(len(self.jPartidas)) if ('Over/Under '+str(uo) in self.jPartidas[idx]['marketName']) and ( self.jPartidas[idx]["event"]["name"] == dc["nomeBF"] ) ]) > 0 :
                     marketId = [self.jPartidas[idx]['marketId'] for idx in range(len(self.jPartidas)) if ('Over/Under '+str(uo) in self.jPartidas[idx]['marketName']) and ( self.jPartidas[idx]["event"]["name"] == dc["nomeBF"] ) ][0]
                     print("Apostarei", percent_da_banca, ",stack=", stack_aposta, str(round(percent_da_banca*saldo,2)), ", na selecao ", tipo_aposta, str(uo)+".5 Goals", ", odds=", odd_selecionada, ", jogo=", dc["nomeBF"], "(", dc["nomeJ"], ")", "mercado=", marketId, " .")
                     
                     selectionId = str(dc["selecoes"][tipo_aposta+" "+str(uo)+".5 Goals"] )
                     filtro='{ "marketId": "'+ marketId +'", "instructions": [ { "selectionId": "' + selectionId + '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "'+str(stack_aposta)+'", "price": "'+ str(odd_selecionada) +'", "persistenceType": "LAPSE" } } ] }'
                     #breakpoint()
                     # retorno_aposta = self.api.aposta(json_req=filtro) #Cuidado
                     # if( retorno_aposta["status"] != "SUCCESS" ): #'result' not in retorno_aposta or 
                        # print("Erro:", retorno_aposta)
                     # elif( retorno_aposta['instructionReports'][0]['sizeMatched'] == 0.0 ) :
                        # print("Aposta não correspondida") #Exemplo: {'status': 'SUCCESS', 'marketId': '1.172153457', 'instructionReports': [{'status': 'SUCCESS', 'instruction': {'selectionId': 47972, 'handicap': 0.0, 'limitOrder': {'size': 5.0, 'price': 4.3, 'persistenceType': 'LAPSE'}, 'orderType': 'LIMIT', 'side': 'BACK'}, 'betId': '208573543824', 'placedDate': '2020-08-16T17:19:13.000Z', 'averagePriceMatched': 0.0, 'sizeMatched': 0.0, 'orderStatus': 'EXECUTABLE'}]}
                        # bet_id = retorno_aposta['instructionReports'][0]['betId'] # Salva o Id da aposta
                        # filtro='{"betId" : '+str(bet_id)+' }'
                        # retorno_cancelamento = self.api.cancelaAposta(json_req=filtro) # Exempo: {'status': 'SUCCESS', 'instructionReports': []}
                     # else:
                        # bet_id = retorno_aposta['instructionReports'][0]['betId'] # Salva o Id da aposta
                        # data_aposta = retorno_aposta['instructionReports'][0]['placedDate']
                        # self.dic_apostas[ dc["nomeBF"] ] = {'id': bet_id, 'data' : data_aposta} # Código da aposta e data da aposta
                        # salvaProgresso(self.dic_apostas, nome_aposta_pickle) # Armazena a lista de partidas apostadas
                        # self.dic_apostas = {j:i for j,i in self.dic_apostas.items() if datetime.strptime(self.dic_apostas[j]['data'], '%Y-%m-%dT%H:%M:%S.%fZ') >= (datetime.now() - timedelta(days=2)) } # Deixo apenas as partidas mais recentes na lista
                        # print("Aposta", percent_da_banca, ",stack=", stack_aposta, ", na selecao ", tipo_aposta, str(uo)+".5 Goals", ", odds=", odd_selecionada, ", jogo=", dc["nomeBF"], "(", dc["nomeJ"], ")", "mercado=", marketId, " .")
               #else: print("Nada para apostar por enquanto...")
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
         time.sleep( 30 )
   if args.odds:
      bot.atualizaOdds()
   if args.partidas:
      while True:
         try:
            bot.ExibeTodosDados(horas=int(args.horas), minutos=int(args.minutos))
         except Exception:
            print("Erro!")
            raise
   