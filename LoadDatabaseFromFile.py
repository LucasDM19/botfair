#coding: utf-8
from Hush import caminhos_or as caminho_inicial, caminho_destino_bz2
from os import listdir
from os import path
import os
import bz2
import json
from shutil import copyfile
import sqlite3
import operator # Para odenar um dicionário
import sys
import datetime # Parâmetros de data
import pickle

def iniciaBanco(nome_banco):
   conn = sqlite3.connect(nome_banco)
   c = conn.cursor()

   c.execute('create table if not exists odds (RunnerId, RaceId, LastTradedPrice, PublishedTime)')
   #c.execute('create table if not exists odds_position (RunnerId, RaceId, CurrentPrice , MinutesUntillRace INTEGER)') # Odds por minuto
   c.execute('create table if not exists races (MarketTime, InplayTimestamp, MarketName, EventId, Country)')
   c.execute('create table if not exists afs (RunnerId, RaceId, AdjustmentFactor, PublishedTime)')
   #c.execute('create table if not exists afs_position (RunnerId, RaceId, CurrentAF, MinutesUntillRace INTEGER)') # AFs por minuto
   c.execute('create table if not exists runners (RunnerId, RaceId, EventId, RunnerName, WinLose INTEGER, BSP INTEGER)')
   return c, conn

def insere_bz2_sqlite(arquivo_bz2, arquivo):
   global c, conn, lista_ids, nome_arqs_pickle, dados_proc
   with bz2.open(arquivo_bz2, "rt") as bz_file:
      md=json.loads( next(bz_file)  )['mc'][0]['marketDefinition']
      race_id=arquivo.replace('.bz2','')
      inplay_timestamp=0

      for linha in bz_file:
         obj=json.loads( linha  )
         race_id=obj['mc'][0]['id']
         time=obj['pt']/1000.0
         if 'rc' in obj['mc'][0]  :
            for odd in obj['mc'][0]['rc']:
                #print("Tem odds", odd['id'], race_id, odd['ltp'], time )
                c.execute("insert or replace into  odds values (?,?,?,datetime(?,'unixepoch'))", [odd['id'], race_id, odd['ltp'], time ])
         
         if 'marketDefinition' in obj['mc'][0]:
             md=obj['mc'][0]['marketDefinition']                
             
             #if inplay_timestamp==0 and md['inPlay']==True and 'OVER_UNDER_' in md['marketType'] :
             if ( md['status']=='SUSPENDED' and 'OVER_UNDER_' in md['marketType']  and [md['eventId'], md['eventName']] not in lista_ids ) : 
               #print("Tem races", md['marketTime'], inplay_timestamp, md['eventName'], md['eventId'], md['countryCode'] )
               inplay_timestamp=time        
               c.execute("insert or replace into races values (?,datetime(?,'unixepoch'),?,?,?)", [md['marketTime'], inplay_timestamp, md['eventName'], int(md['eventId']), md['countryCode'] ])
               lista_ids.append( [md['eventId'], md['eventName']] )

             #if( md['eventName'] == 'FC Bastia-Borgo v Concarneau' ):
             #if( md['eventName'] == 'FC Zugdidi v FC Kolkheti Poti' ): print( obj['mc'][0] )
             #if (md['status']=='SUSPENDED' or md['status']=='OPEN') :
             if (md['status']=='CLOSED' and 'OVER_UNDER_' in md['marketType'] ) : 
               for runner in md['runners']:
                  #print("Tem Runners", runner['id'], race_id, md['eventId'], runner['name'],1 if runner['status']=='WINNER' else (0 if runner['status']=='LOSER' else -1), runner['bsp'] if 'bsp' in runner else -1 )
                  c.execute("insert or replace into runners values (?,?,?,?,?,?)", [runner['id'], race_id, int(md['eventId']), runner['name'],1 if runner['status']=='WINNER' else (0 if runner['status']=='LOSER' else -1), runner['bsp'] if 'bsp' in runner else -1 ])

      conn.commit()
      dados_proc['ids'] = lista_ids
      salvaProgresso(dados_proc, nome_arqs_pickle)

def processa_bz2(arquivo_bz2, arquivo):
   with bz2.open(arquivo_bz2, "rt") as bz_file:
      try:
         obj=json.loads( next(bz_file)  )
         marketType=obj['mc'][0]['marketDefinition']['marketType']
         countryCode=obj['mc'][0]['marketDefinition']['countryCode']
         if('OVER_UNDER_' in marketType ):
            #print("Tipo Mercado=", marketType)
            insere_bz2_sqlite(arquivo_bz2, arquivo)
      except KeyError:
        #print("CountryCode?", obj['mc'][0]['marketDefinition'] )
        #x = 1/0
        pass
      except json.decoder.JSONDecodeError:
         pass
      except OSError:
         print("Arquivo", arquivo, " com erro ***")
      except EOFError:
         print("Erro de EOF !!!", arquivo)

def verificaDiretorios(caminhos_or=caminho_inicial):  
   global nome_arqs_pickle, dados_proc
   #Verificando recursivamente os diretorios. Para quando encontra um arquivo.
   while( len(caminhos_or) > 0 ):
      caminho = caminhos_or.pop()
      for pasta in listdir(caminho):
         if(path.isfile(caminho+'\\'+pasta)):
            print("Arquivo!", caminho+'\\'+pasta)
            #if(pasta == '1.166872140.bz2'): print("Arquivo!", caminho+'\\'+pasta)
            processa_bz2(arquivo_bz2=caminho+'\\'+pasta, arquivo=pasta)
         if(path.isdir(caminho+'\\'+pasta)):
            #print("dir=", caminho + '\\'+pasta)
            caminhos_or.append(caminho + '\\'+pasta)
      dados_proc['arqs'] = caminhos_or
      salvaProgresso(dados_proc, nome_arqs_pickle)
   print("Carga completa")
   os.remove(nome_arqs_pickle) # Quando tudo estiver ok, mata o Pickle

def recriaIndices():
   global c, conn
   # Quando acaba tudo, cria (ou recria) os indices
   #c.execute("DROP INDEX IF EXISTS idx_races_EventId")
   #c.execute("CREATE INDEX idx_races_EventId ON races ( EventId ASC )")
   #c.execute("DROP INDEX IF EXISTS idx_runners_RaceId")
   #c.execute("CREATE INDEX idx_runners_RaceId ON runners ( RaceId )")
   #c.execute("DROP INDEX IF EXISTS idx_odds_RaceId")
   #c.execute("CREATE INDEX idx_odds_RaceId ON odds ( RaceId ASC )")
   #c.execute("DROP INDEX IF EXISTS idx_odds_RunnerId")
   #c.execute("CREATE INDEX idx_odds_RunnerId ON odds ( RunnerId )")
   #c.execute("DROP INDEX IF EXISTS idx_odds_RunnerId_PublishedTime")
   #c.execute("CREATE INDEX idx_odds_RunnerId_PublishedTime ON odds (RunnerId, PublishedTime)")
   #c.execute("DROP INDEX IF EXISTS idx_races_EventId_MarketTime")
   #c.execute("CREATE INDEX idx_races_EventId_MarketTime ON races (EventId, MarketTime)")
   #c.execute("DROP INDEX IF EXISTS idx_runners_EventId")
   #c.execute("CREATE INDEX idx_runners_EventId ON runners (EventId )")
   
   c.execute("DROP INDEX IF EXISTS idx_odds_position_RaceId")
   c.execute("CREATE INDEX idx_odds_position_RaceId ON odds_position ( RaceId ASC )")
   c.execute("DROP INDEX IF EXISTS idx_odds_position_RunnerId")
   c.execute("CREATE INDEX idx_odds_position_RunnerId ON odds_position ( RunnerId )")
   c.execute("DROP INDEX IF EXISTS id_odds_position_MinutesUntillRace")
   c.execute("CREATE INDEX id_odds_position_MinutesUntillRace ON odds_position (MinutesUntillRace)")
   conn.commit() # Agora sim grava tudo
   print("Índices recriados")
   
def removeDuplicatas():
   global c, conn
   # Eliminar duplicatas
   for nome_tabela in ['races', 'runners', 'odds', 'afs']: # Todas as tabelas do BD
      print("Agora arrumando tabela", nome_tabela)
      c.execute("DROP TABLE IF EXISTS temp_table")
      c.execute("CREATE TABLE temp_table as SELECT DISTINCT * FROM " + nome_tabela)
      c.execute("DELETE FROM " + nome_tabela)
      c.execute("INSERT INTO " + nome_tabela + " SELECT * FROM temp_table")
      conn.commit() # Agora sim grava tudo
   print("Duplicatas removidas")

def consolidaOdds():
    global c, conn
    print("Agora agrupando odds por minuto")
    c.execute("""create table if not exists odds_position as 
    SELECT RunnerId, RaceId, EventId, LastTradedPrice as CurrentPrice, Dif_Min as MinutesUntillRace
      from (SELECT races.EventId, odds.RaceId, odds.RunnerId, odds.LastTradedPrice, odds.PublishedTime,
      Cast (( JulianDay(races.MarketTime) - JulianDay(odds.PublishedTime) ) * 24 * 60 As Integer ) as Dif_Min,
       MAX(odds.PublishedTime) as ultima, odds.LastTradedPrice
      FROM odds, races, runners
      WHERE runners.RaceId = odds.RaceId
        AND runners.EventId = races.EventId
        AND runners.RunnerId = runners.RunnerId
        AND odds.RunnerId = runners.RunnerId
      GROUP BY races.EventId, odds.RaceId, odds.RunnerId, Cast (( JulianDay(races.MarketTime) - JulianDay(odds.PublishedTime) ) * 24 * 60 As Integer )
      ORDER BY races.EventId, odds.RaceId, odds.RunnerId, odds.PublishedTime) """)
    conn.commit() # Agora sim grava tudo

def fazLimpeza():
   global c, conn
   # E ainda faz aquela limpeza geral
   print("Hora do aspirador")
   c.execute("VACUUM")
   conn.commit() # Agora sim grava tudo

def descarregaDaMemoria(conn_memoria, nome):
   #conn_memoria = sqlite3.connect(':memory:')
   print("Hora de sair da memória!")

   # dump old database in the new one
   #with sqlite3.connect(nome) as new_db:
   #    new_db.executescript("".join(conn_memoria.iterdump()))
   #source = sqlite3.connect(':memory:')
   dest = sqlite3.connect(nome)
   conn_memoria.backup(dest)
   
def carregaParaMemoria(nome):
   #conn_memoria = sqlite3.connect(':memory:')
   print("Hora de entrar na memória!")

   source = sqlite3.connect(nome)
   dest = sqlite3.connect(':memory:')
   source.backup(conn_memoria)
   return dest

def salvaProgresso(lista, nome_arquivo):
   with open(nome_arquivo, 'wb') as f:
      pickle.dump(lista, f)
      
if __name__ == '__main__': 
   #ano = datetime.datetime.now().year if len(sys.argv) <= 1 else int(sys.argv[1])
   #mes = datetime.datetime.now().month if len(sys.argv) <= 2 else int(sys.argv[2])
   #nome_mes = datetime.date(year=ano, month=mes, day=1).strftime("%b")
   #caminho_mes_ano = []
   #caminho_mes_ano.append( caminho_inicial[0] + str(ano) + '\\' + str(nome_mes) + '\\' )
   #print( ano, mes, nome_mes, caminho_mes_ano )
  
   #nome_arqs_pickle = 'load_arqs.pkl'
   #nome_base_dados = 'bf_under_over_full.db'
   #c, conn = iniciaBanco('bf_under_over_'+str(ano)+str(mes)+'.db')
   #c, conn = iniciaBanco(':memory:')
   c, conn = iniciaBanco('C:\\Users\\Lucas\\Desktop\\bf_under_over_full.db')
   #if( os.path.isfile(nome_arqs_pickle) ):
   #   with open(nome_arqs_pickle, 'rb') as f:
   #      dados_proc = pickle.load(f)
   #   lista_ids = dados_proc['ids']
   #   lista_diretorios = dados_proc['arqs']
   #   verificaDiretorios(caminhos_or=lista_diretorios)
   #else:
   #   dados_proc = {}
   #   lista_ids = [] # Para evitar duplicados no races
   #   dados_proc['ids'] = lista_ids
   #   verificaDiretorios()
   #removeDuplicatas()
   consolidaOdds()
   #recriaIndices()
   #fazLimpeza()
   #descarregaDaMemoria(conn, nome_base_dados)