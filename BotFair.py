#coding: utf-8
from __future__ import print_function
from Hush import usuarioAPI, senhaAPI, APIKey, statsURL, habilitarBD, statsBF
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
      self.estatisticas = SoccerStats(url=statsURL) #salva Classe para uso posterior
      self.estatisticasBF = SoccerStats(url=statsBF) #salva para uso posterior
         
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
   Obtem informacoes sobre uma partida especifica
   """
   def obtemOddsDaPartida(self, event_id):
      filtro=('{"filter":{"eventTypeIds":["1"], '
         ' "eventIds" : [' + event_id + '] '
         ' "turnsInPlay" : true, '
         ' "sort":"FIRST_TO_START","maxResults":"1",'
         '"marketProjection":["RUNNER_METADATA"]}')
      return api.obtemPartidasDeFutebol(json_req=filtro)
   
   """
   Obtem a lista de partidas que comecarao nos proximos trinta minutos.
   Baseado na que obtem os dados Win de Londres.
   """   
   def obtemListaPartidasAndamento(self, horas=0, minutos=45):
      import datetime
      #now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
      now_fuso = datetime.datetime.now() + datetime.timedelta(hours=3, minutes=0) # Horário de Londres
      faz_45_minutos = (now_fuso + datetime.timedelta(hours=horas, minutes=-81)).strftime('%Y-%m-%dT%H:%M:%SZ') # 66 minutos + 15 minutos intervalo
      daqui_45_minutos = (now_fuso + datetime.timedelta(hours=horas, minutes=-80)).strftime('%Y-%m-%dT%H:%M:%SZ') # 65 minutos + 15 minutos intervalo
      #print("Inicio e fim:", faz_45_minutos, daqui_45_minutos)
      #breakpoint()
      filtro=('{"filter":{"eventTypeIds":["1"],  '
         ' "turnsInPlay" : true, "inPlayOnly" : true, '
         ' "marketStartTime":{"from":"' + faz_45_minutos + '", "to":"' + daqui_45_minutos + '"}},'
         ' "sort":"FIRST_TO_START","maxResults":"100",'
         '"marketProjection":["RUNNER_DESCRIPTION","EVENT","MARKET_START_TIME"]}')
      self.jPartidas = api.obtemTodosMercadosDasPartidas(json_req=filtro) #Obtendo o Json das partidas
      #print("Teste", self.jPartidas) #[p for p in self.jPartidas ][1] )

   def ObtemMercadosDisponiveis(self):
      pass
   
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
      #breakpoint()
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
         maximo_da_banca_por_aposta = 0.05 #0.10 ideal, 0.05 CAUTELA
         
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
         #s_da=dc["Json"]['daH']+dc["Json"]['daA'] 
         #s_r=dc["Json"]['rh']+dc["Json"]['ra']
         #s_r = dc["Json"]['sr']
         d_g=abs(dc["Json"]['gH']-dc["Json"]['gA'])
         d_c=abs(dc["Json"]['cH']-dc["Json"]['cA'])
         #d_s=abs(dc["Json"]['sH']-dc["Json"]['sA'])                                         
         #d_da=abs(dc["Json"]['daH']+dc["Json"]['daA'])
         handicap = dc["Json"]['handicap']
         b365_goal = dc["BetFair"]['b365_goal'] # linha de gols da Bet365
         oddsU365 = dc["BetFair"]['b365_ou'] # odds para Under na Bet365
         oddsO365 = dc["BetFair"]['b365_ou'] # odds para Over na Bet365
         
         #goal_diff=goalline-s_g
         #print("Teste Diff=", goal_diff)
         mod0=int(goalline%1==0)
         #mod25=int(goalline%1==0.25)
         #mod50=int(goalline%1==0.50)
         #mod75=int(goalline%1==0.75)
         import math 
         X=s_g/math.log(s_s+0.75)
         #Y=Math.pow(s_s,1.5)
         #L1=math.log(1+s_s)
         #L2=math.log(1+L1)
         #L3=math.log(1+L2)
         #W = 0 #W=Number(home.includes('Women')) // Adaptar isso
         W = 1 if "Women" in dc["nomeBF"] or "(W)" in dc["nomeBF"] else 0
         
         #Equacao esepcifica Betfair
         d_goal_bf = uo-s_g
         #L1=math.log(1+abs(d_goal_bf))
         #UM1=math.log(1+oddsU)
         #OM1=math.log(1+oddsO)
         #d_hand_tc=abs(handicap)
         oddsOL1 = math.log(1+oddsO)
         oddsUL1 = math.log(1+oddsU)
         #oddsL2 = math.log(1+oddsL1)
         #oddsL3 = math.log(1+oddsL2)
         goal_diff = b365_goal - s_g
         if(goal_diff == 0 or goalline == 0):
            return False, "nada", -1, 0 # Sem nada para fazer, pois da 1/0
         Z = (goalline - s_g)/goal_diff
         gg = s_g/goalline
         s_gL1=math.log(1+s_g)
         """
         goal é a linha de gols da Betfair 1.5, 2.5, 3.5, ..
         b365_goal é a linha de gols da Bet365
         odds são as odds do back para a determinada seleção na Betfair
         oddsO são as odds para Over na Bet365
         oddsU são as odds para Under na Bet365
         goal_diff = b365_goal - s_g
         Z=(goal-s_g)/goal_diff
         gg=s_g/goal
         oddsL1=log(1+odds)
         s_gL1=log(1+s_g)
         """
         if( (goal_diff < -1 or goal_diff > 10.0) or (oddsO < 1.3 or oddsO > 2.2 ) ): kelly_OVER = -1 
         else: kelly_OVER=-0.4442718 * goalline + 0.3790217 * s_g + 0.386046 * goal_diff + -0.4385253 * oddsO + 0.0020811 * s_c + 0.2945769 * oddsU365 + 0.0193414 * d_g + 0.0015613 * d_c + -0.1368251 * Z + 3.1544002 * oddsOL1 + 0.3614609 * gg +-1.0847816
         if( (d_g > 4) or (oddsU < 1.3 or oddsU > 2.2 ) ): kelly_UNDER = -1 
         else: kelly_UNDER=-0.2234772 * s_g +0.325941 * goalline +-0.9310255 * oddsU +-0.2675861 * goal_diff +-0.0098466 * s_s +0.0383662 * handicap +0.1037659 * W +0.1338302 * oddsO365 +-0.0304003 * d_g +3.5695531 * oddsUL1 +-0.2307464 * s_gL1 +-0.32225066
         #eh so apostar de kelly >1% , e apostar metade
         minimo_kelly = 0.01
         percentual_de_kelly = 0.5 # apostar metade
         melhor_kelly = max(kelly_OVER, kelly_UNDER) # Escolho o mais alto
         tipo_aposta = "Under" if kelly_UNDER >= kelly_OVER else "Over"
         #print("Avaliando:", dc["nomeBF"], ", diff=", goal_diff, ",oddsO=",oddsO, ",oddsU=", oddsU,",Json=", dc["Json"], ", Kelly_OVER=", kelly_OVER, ", Kelly_UNDER=", kelly_UNDER, "%banca=", melhor_kelly * percentual_de_kelly, ",melhor=", melhor_kelly, ",tipo=", tipo_aposta, ",UO=", uo )
         if( melhor_kelly > minimo_kelly ):
            percent_da_banca = melhor_kelly * percentual_de_kelly
            if (percent_da_banca >  maximo_da_banca_por_aposta): percent_da_banca=maximo_da_banca_por_aposta
            dic_op_aposta[uo] = percent_da_banca #/100 # Estava muito alto
            dic_tipo_aposta[uo] = tipo_aposta
               
      dic_filtro = dict(filter(lambda elem: elem[1] > 0,dic_op_aposta.items()))
      if( len(dic_filtro) == 0 ):
         #print("Sem nada para apostar", dc["nomeBF"], len(dic_op_aposta) )
         return False, "nada", -1, 0 # Sem nada para fazer
      #if( max(dic_filtro, key=dic_filtro.get) > 0.10 ): breakpoint()
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
      #partidasJson = [ jstat[x]["home"]+" v "+jstat[x]["away"] for x in range(len(jstat)) ] #Partidas no formato MandanteXVisitante do Json
      jstatBF = self.estatisticasBF.getStats() #Atualizo o Json
      for partidaBF in jstatBF: # Para cada partida que aparece no Json da BetFair
         id_bf = str(partidaBF['id_bf']) # EventId
         id_ic = partidaBF['id_tc'] # Id do TotalCorner
         nomeBF = partidaBF['home_bf'] + " v " + partidaBF['away_bf'] # Nome BetFair
         nomeJ = partidaBF['home_tc'] + " v " + partidaBF['away_tc'] # Nome Total Corner
         if( len([j for j in jstat if j['jogo_id'] == id_ic]) != 0 ): # Vez ou outra tem dados vazios no Json
            jstat_x = [j for j in jstat if j['jogo_id'] == id_ic][0] # Apenas as stats especificas
            #partidaBF_x = self.obtemOddsDaPartida(event_id = id_bf)
            dc_odds, dc_selecoes, dc_mercados = self.getOddsFromPartida(idBF = id_bf ) # Falta essa informação
            dc = {"nomeBF" : nomeBF, "nomeJ" : nomeJ, "BetFair" : partidaBF, "Json" : jstat_x, "odds": dc_odds, "selecoes": dc_selecoes, "mercados": dc_mercados, }
            #breakpoint()
            devo_apostar, tipo_aposta, uo, percent_da_banca = self.avaliaSeApostaOuNao(dc)
            nao_apostei_ainda = self.verificaSeJaApostouOuNao(nome_jogo_BF=dc["nomeBF"] )
            retorno_saldo = self.api.obtemSaldoDaConta() #{'availableToBetBalance': 177.94, 'exposure': 0.0, 'retainedCommission': 0.0, 'exposureLimit': -10000.0, 'discountRate': 0.0, 'pointsBalance': 20, 'wallet': 'UK'}
            saldo = int(retorno_saldo['availableToBetBalance'])
            #if( percent_da_banca > 0.05 ): percent_da_banca = 0.05
            stack_aposta = round(percent_da_banca*saldo,2) 
            #valor_minimo_aposta = 3 # Equivalente a 2 GBP (2.62) - na verdade 3 EUR
            valor_minimo_aposta = 0 # Teste
            
            if( devo_apostar and nao_apostei_ainda and stack_aposta >= valor_minimo_aposta ):
               #breakpoint()
               odd_selecionada = dc["odds"][tipo_aposta+" "+str(uo)+".5 Goals"] #Under ou Over
               #if len([self.jPartidas[idx]['marketId'] for idx in range(len(self.jPartidas)) if ('Over/Under '+str(uo) in self.jPartidas[idx]['marketName']) and ( self.jPartidas[idx]["event"]["name"] == dc["nomeBF"] ) ]) > 0 :
               if( 'Over/Under '+str(uo) in dc_odds.keys() ): # Odd valida
                  #marketId = [self.jPartidas[idx]['marketId'] for idx in range(len(self.jPartidas)) if ('Over/Under '+str(uo) in self.jPartidas[idx]['marketName']) and ( self.jPartidas[idx]["event"]["name"] == dc["nomeBF"] ) ][0]
                  marketId = dc_mercados[id_bf] # Com base no EventId, obtenho MarketId
                  #print("Apostarei", percent_da_banca, ",stack=", stack_aposta, str(round(percent_da_banca*saldo,2)), ", na selecao ", tipo_aposta, str(uo)+".5 Goals", ", odds=", odd_selecionada, ", jogo=", dc["nomeBF"], "(", dc["nomeJ"], ")", "mercado=", marketId, " .")
                  
                  selectionId = str(dc["selecoes"][tipo_aposta+" "+str(uo)+".5 Goals"] )
                  filtro='{ "marketId": "'+ marketId +'", "instructions": [ { "selectionId": "' + selectionId + '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "'+str(stack_aposta)+'", "price": "'+ str(odd_selecionada) +'", "persistenceType": "LAPSE" } } ] }'
                  #breakpoint()
                  
                  from datetime import datetime
                  url = 'http://19k.me/bf_db/CRUJ.php' # Para a parte do BD
                  myobj_e = {'t' : 'a', 
                              'percent_banca' : str(percent_da_banca),
                              'stack_aposta' : str(stack_aposta), 
                              'selecao' : str(tipo_aposta)+str(uo)+".5 Goals",
                              'odds' : str(odd_selecionada),
                              'jogo' : dc["nomeBF"],
                              'mercado' : marketId,
                              'hora' : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                              'bet_id' : '-1',
                              'user' : 'lucasmuzel@gmail.com',}
                  x = requests.post(url, data = myobj_e)
                  print("Aposta", percent_da_banca, ",stack=", stack_aposta, ", na selecao ", tipo_aposta, str(uo)+".5 Goals", ", odds=", odd_selecionada, ", jogo=", dc["nomeBF"], "(", dc["nomeJ"], ")", "mercado=", marketId, " .")
                  self.dic_apostas[ dc["nomeBF"] ] = {'id': bet_id, 'data' : datetime.now().strftime('%Y-%m-%d %H:%M:%S') } # Código da aposta e data da aposta
                  salvaProgresso(self.dic_apostas, nome_aposta_pickle) # Armazena a lista de partidas apostadas
                  
                  # retorno_aposta = self.api.aposta(json_req=filtro) #Cuidado
                  # if( retorno_aposta["status"] != "SUCCESS" ): #'result' not in retorno_aposta or 
                     # print("Erro:", retorno_aposta)
                  # elif( retorno_aposta['instructionReports'][0]['sizeMatched'] == 0.0 ) :
                     # #print("Aposta não correspondida") #Exemplo: {'status': 'SUCCESS', 'marketId': '1.172153457', 'instructionReports': [{'status': 'SUCCESS', 'instruction': {'selectionId': 47972, 'handicap': 0.0, 'limitOrder': {'size': 5.0, 'price': 4.3, 'persistenceType': 'LAPSE'}, 'orderType': 'LIMIT', 'side': 'BACK'}, 'betId': '208573543824', 'placedDate': '2020-08-16T17:19:13.000Z', 'averagePriceMatched': 0.0, 'sizeMatched': 0.0, 'orderStatus': 'EXECUTABLE'}]}
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
       
if __name__ == "__main__":
   u, s, a = usuarioAPI, senhaAPI, APIKey
   api = BetfairAPI(usuario=u, senha=s, api_key=a)
   print("Session Token=",api.sessionToken)
   bot = BotFair(api, bdOption=habilitarBD )
   while True:
      bot.BotFairGo()
      import time
      time.sleep( 30 )
   