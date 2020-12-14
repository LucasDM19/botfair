# -*- coding: utf-8 -*-
import logging
import betfairlightweight
import os
import pickle
from Hush import usuarioAPI, senhaAPI, APIKey
import sys
import datetime
import calendar 
import sqlite3
import bz2
import json
import requests

def iniciaBanco(nome_banco):
   #conn = sqlite3.connect(nome_banco)
   #c = conn.cursor()

   c.execute('create table if not exists odds (RunnerId, RaceId, LastTradedPrice, PublishedTime)')
   #c.execute('create table if not exists odds_position (RunnerId, RaceId, CurrentPrice , MinutesUntillRace INTEGER)') # Odds por minuto
   c.execute('create table if not exists races (MarketTime, InplayTimestamp, MarketName, EventId, Country)')
   c.execute('create table if not exists afs (RunnerId, RaceId, AdjustmentFactor, PublishedTime)')
   #c.execute('create table if not exists afs_position (RunnerId, RaceId, CurrentAF, MinutesUntillRace INTEGER)') # AFs por minuto
   c.execute('create table if not exists runners (RunnerId, RaceId, EventId, RunnerName, WinLose INTEGER, BSP INTEGER)')
   #return c, conn

def insere_bz2_sqlite(arquivo_bz2, arquivo):
   #global c, conn, lista_ids, nome_arqs_pickle, dados_proc
   global lista_ids, nome_arqs_pickle, dados_proc
   url = 'http://19k.me/bf_db/CRUJ.php' # Para a parte do BD
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
                #c.execute("insert or replace into  odds values (?,?,?,datetime(?,'unixepoch'))", [odd['id'], race_id, odd['ltp'], time ])
                myobj_o = {'t' : 'o', 
                           'id' : odd['id'],
                           'race_id' : race_id,
                           'ltp' : odd['ltp'],
                           'time' : datetime.datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')   , }
                x = requests.post(url, data = myobj_o)
                #print(x.text)
         
         if 'marketDefinition' in obj['mc'][0]:
             md=obj['mc'][0]['marketDefinition']                
             
             #if inplay_timestamp==0 and md['inPlay']==True and 'OVER_UNDER_' in md['marketType'] :
             if ( md['status']=='SUSPENDED' and 'OVER_UNDER_' in md['marketType']  and [md['eventId'], md['eventName']] not in lista_ids ) : 
               #print("Tem races", md['marketTime'], inplay_timestamp, md['eventName'], md['eventId'], md['countryCode'] )
               inplay_timestamp=datetime.datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')         
               #c.execute("insert or replace into races values (?,datetime(?,'unixepoch'),?,?,?)", [md['marketTime'], inplay_timestamp, md['eventName'], int(md['eventId']), md['countryCode'] ])
               myobj_r = {'t' : 'r', 
                           'market_time' : md['marketTime'],
                           'inplay_timestamp' : inplay_timestamp,
                           'market_name' : md['eventName'],
                           'event_id' : md['eventId'],
                           'country' :  md['countryCode'], }
               x = requests.post(url, data = myobj_r)
               #print(x.text)
               lista_ids.append( [md['eventId'], md['eventName']] )

             #if( md['eventName'] == 'FC Bastia-Borgo v Concarneau' ):
             #if( md['eventName'] == 'FC Zugdidi v FC Kolkheti Poti' ): print( obj['mc'][0] )
             #if (md['status']=='SUSPENDED' or md['status']=='OPEN') :
             if (md['status']=='CLOSED' and 'OVER_UNDER_' in md['marketType'] ) : 
               for runner in md['runners']:
                  #print("Tem Runners", runner['id'], race_id, md['eventId'], runner['name'],1 if runner['status']=='WINNER' else (0 if runner['status']=='LOSER' else -1), runner['bsp'] if 'bsp' in runner else -1 )
                  #c.execute("insert or replace into runners values (?,?,?,?,?,?)", [runner['id'], race_id, int(md['eventId']), runner['name'],1 if runner['status']=='WINNER' else (0 if runner['status']=='LOSER' else -1), runner['bsp'] if 'bsp' in runner else -1 ])
                  myobj_u = {'t' : 'u', 
                              'runner_id' : runner['id'],
                              'race_id' : race_id,
                              'event_id' : md['eventId'],
                              'runner_name' : runner['name'],
                              'win_lose' : str(1 if runner['status']=='WINNER' else (0 if runner['status']=='LOSER' else -1)), 
                              'bsp' : runner['bsp'] if 'bsp' in runner else '-1' , }
                  x = requests.post(url, data = myobj_u)
                  #print(x.text)

      #conn.commit()
      dados_proc['ids'] = lista_ids
      #salvaProgresso(dados_proc, nome_arqs_pickle)

def processa_bz2(arquivo_bz2, arquivo, cam_arq=''):
   with bz2.open(arquivo_bz2, "rt") as bz_file:
      try:
         obj=json.loads( next(bz_file)  )
         marketType=obj['mc'][0]['marketDefinition']['marketType']
         countryCode=obj['mc'][0]['marketDefinition']['countryCode']
         if('OVER_UNDER_' in marketType ):
            #print("Tipo Mercado=", marketType)
            insere_bz2_sqlite(arquivo_bz2, arquivo)
         return True
      except KeyError:
        #print("CountryCode?", obj['mc'][0]['marketDefinition'] )
        #x = 1/0
        return False
        pass
      except json.decoder.JSONDecodeError:
         return False
         pass
      except OSError:
         print("Arquivo", arquivo, " com erro ***")
         return False
         #url = 'http://19k.me/bf_db/CRUJ.php' # Para a parte do BD
         #myobj_e = {'t' : 'a', 
         #            'arquivo' : arquivo,
         #            'diretorio' : cam_arq, }
         #x = requests.post(url, data = myobj_e)
      except EOFError:
         print("Erro de EOF !!!", arquivo)
         return False

"""
Historic is the API endpoint that can be used to
download data betfair provide.

https://historicdata.betfair.com/#/apidocs
"""

ext = '' if len(sys.argv) <= 1 else sys.argv[1]
ano = datetime.datetime.now().year if len(sys.argv) <= 2 else int(sys.argv[2])
mes = datetime.datetime.now().month if len(sys.argv) <= 3 else int(sys.argv[3])
dia_i = 1 if len(sys.argv) <= 4 else int(sys.argv[4])
dia_f = calendar.monthrange(ano, mes)[1] if len(sys.argv) <= 5 else int(sys.argv[5])
print( ext, ano, mes, dia_i, dia_f )
nome_dts_pickle = 'hist_lista_datas'+ext+'.pkl'

def arrumaDiretorio(caminho=None, lista_pastas=None):
   for idx_pasta in range(len(lista_pastas)):
      can = os.path.join(caminho, *lista_pastas[0:idx_pasta+1] )
      if( os.path.isdir(can) ):
         print(can, "Existe")
      else:
         print(can, "N Existe")
         os.mkdir(can) # Crio o diretorio

def conectaNaBetFair():
   # create trading instance
   import pathlib
   trading = betfairlightweight.APIClient(usuarioAPI,senhaAPI, app_key=APIKey, certs=str(pathlib.Path().absolute()))

   # login
   trading.login()
   return trading
   
def obtemListaDeArquivos(trading, d_ini, m_ini, a_ini, d_fim, m_fim, a_fim):
   # setup logging
   logging.basicConfig(level=logging.INFO)  # change to DEBUG to see log all updates

   # get my data
   my_data = trading.historic.get_my_data()
   for i in my_data:
       print(i)

   # get collection options (allows filtering)
   collection_options = trading.historic.get_collection_options(
       "Soccer", "Basic Plan", d_ini, m_ini, a_ini, d_fim, m_fim, a_fim
   )
   print(collection_options)

   # get advance basket data size
   basket_size = trading.historic.get_data_size(
       "Soccer", "Basic Plan", d_ini, m_ini, a_ini, d_fim, m_fim, a_fim # Horse Racing
   )
   print(basket_size) # {'totalSizeMB': 200, 'fileCount': 121397}

   # get file list
   file_list = trading.historic.get_file_list(
       "Soccer",
       "Basic Plan",
       from_day=d_ini,
       from_month=m_ini,
       from_year=a_ini,
       to_day=d_fim,
       to_month=m_fim,
       to_year=a_fim,
       market_types_collection=["OVER_UNDER_15", "OVER_UNDER_25", "OVER_UNDER_35", "OVER_UNDER_45", "OVER_UNDER_55", "OVER_UNDER_65", "OVER_UNDER_75", "OVER_UNDER_85"],
       countries_collection=[], #"GB", "IE"
       file_type_collection=["M", "E"], # Market ou Event
   )
   print(file_list)
   return file_list

def salvaProgresso(lista, nome_arquivo):
   with open(nome_arquivo, 'wb') as f:
      pickle.dump(lista, f)

def baixaArquivosDoMes(trading, dia, mes, ano):
   nome_arq_pickle = 'hist_lista_arquivos'+ext+'.pkl'
   if( os.path.isfile(nome_arq_pickle) ): # Devo continuar a processar a lista
      with open(nome_arq_pickle, 'rb') as f:
         file_list = pickle.load(f)
   else: # Crio uma lista nova
      file_list = obtemListaDeArquivos(trading, d_ini=dia, m_ini=mes, a_ini=ano, d_fim=dia, m_fim=mes, a_fim=ano) # Só pode um mês e um ano

   lista_pendentes = [fil for fil in file_list] # Quantos arquivos ainda não foram baixados
   # download the files
   for file in file_list:
       print(file) # /xds_nfs/hdfs_supreme/BASIC/2017/Jan/1/28061114/1.128919106.bz2
       dirs = file.split('/')[3:] # ['BASIC', '2017', 'Jan', '1', '28061114', '1.128919106.bz2']
       dir2 = dirs[:-1]
       #arrumaDiretorio(caminho=os.path.join("D:/", "users", "Lucas", "Downloads", "betfair_data", "data_futebol"), lista_pastas=dir2) # Me certifico de que todas as pastas existam
       caminho = os.path.join("D:/", "users", "Lucas", "Downloads", "betfair_data", "data_futebol", *dir2 ) # * https://stackoverflow.com/questions/14826888/python-os-path-join-on-a-list/14826889
       download_ok = False
       while not download_ok:
          try:
            #download = trading.historic.download_file(file_path=file, store_directory=caminho)
            download = trading.historic.download_file(file_path=file)
            print(download)
            ret_arq = processa_bz2(download, download, file)
            os.remove(download)
            lista_pendentes.remove(file) # Foi processado
            salvaProgresso(lista_pendentes, nome_arq_pickle) # Armazena a lista do que falta
            download_ok = ret_arq
          except ValueError as e:
            print("Lista inexistente: %s" % e)
            download_ok = True
            pass
          except Exception as e:
            print ("Teve Timeout: %s" % e)
            import time
            time.sleep(3) # Espero 3 segundos
            trading = conectaNaBetFair()
            download_ok = False
       
   os.remove(nome_arq_pickle) # Quando tudo estiver ok, mata o Pickle
   
if( os.path.isfile(nome_dts_pickle) ): # Devo continuar a processar a lista
   with open(nome_dts_pickle, 'rb') as f:
      lista_datas = pickle.load(f)
else: # Crio uma lista nova
   import datetime 
   lista_datas = []
   d_ini=dia_i
   m_ini=mes
   a_ini=ano
   d_fim=dia_f
   m_fim=mes
   a_fim=ano
   dt_inicial = datetime.date(a_ini, m_ini, d_ini)
   dt_final = datetime.date(a_fim, m_fim, d_fim)
   dt_tmp = dt_inicial
   while( dt_tmp <= dt_final ):
      lista_datas.append( [dt_tmp.day, dt_tmp.month, dt_tmp.year] )
      dt_tmp += datetime.timedelta(days=1)

#c, conn = iniciaBanco('C:\\Users\\Lucas\\Desktop\\bf_under_over_full.db')
dados_proc = {}
lista_ids = [] # Para evitar duplicados no races
dados_proc['ids'] = lista_ids
trading = conectaNaBetFair()
lista_datas_pendentes = [dat for dat in lista_datas] # Quantas datas ainda não foram enviadas
for dl in lista_datas:
   print( dl, dl[0], dl[1], dl[2] )
   baixaArquivosDoMes(trading, dia=dl[0], mes=dl[1], ano=dl[2] )
   lista_datas_pendentes.remove(dl)
   print(" *** SALVANDO AGORA!")
   salvaProgresso(lista_datas_pendentes, nome_dts_pickle)
   
os.remove(nome_dts_pickle) # Quando tudo estiver ok, mata o Pickle