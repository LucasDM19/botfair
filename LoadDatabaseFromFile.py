#coding: utf-8
from Hush import caminhos_or, caminho_destino_bz2
from os import listdir
from os import path
import bz2
import json
from shutil import copyfile
import sqlite3
import operator # Para odenar um dicionário

def iniciaBanco(nome_banco):
   conn = sqlite3.connect(nome_banco)
   c = conn.cursor()

   c.execute('create table if not exists odds (RunnerId, RaceId, LastTradedPrice, PublishedTime)')
   c.execute('create table if not exists odds_position (RunnerId, RaceId, CurrentPrice , MinutesUntillRace INTEGER)') # Odds por minuto
   c.execute('create table if not exists races (RaceId, MarketTime, InplayTimestamp, MarketName, MarketVenue)')
   c.execute('create table if not exists afs (RunnerId, RaceId, AdjustmentFactor, PublishedTime)')
   c.execute('create table if not exists afs_position (RunnerId, RaceId, CurrentAF, MinutesUntillRace INTEGER)') # AFs por minuto
   c.execute('create table if not exists runners (RunnerId, RaceId, RunnerName, WinLose INTEGER, BSP INTEGER)')
   return c, conn

def insere_bz2_sqlite(arquivo_bz2, arquivo):
   global c, conn
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
                print("Tem odds", odd['id'], race_id, odd['ltp'], time )
                c.execute("insert or replace into  odds values (?,?,?,datetime(?,'unixepoch'))", [odd['id'], race_id, odd['ltp'], time ])
         
         if 'marketDefinition' in obj['mc'][0]:
             md=obj['mc'][0]['marketDefinition']                
             
             #if inplay_timestamp==0 and md['inPlay']==True and 'OVER_UNDER_' in md['marketType'] :
             if ( 'OVER_UNDER_' in md['marketType'] ) : #and md['eventName'] == 'FC Zugdidi v FC Kolkheti Poti'
               print("Tem races", race_id, md['marketTime'], inplay_timestamp,md['eventName'], md['name'])
               inplay_timestamp=time        
               c.execute("insert or replace into races values (?,?,datetime(?,'unixepoch'),?,?)", [race_id, md['marketTime'], inplay_timestamp,md['eventName'], md['name'] ])

             #if md['inPlay']==False :
               #print("Tem afs", md['runners'][0]['id'], race_id, md['runners'][0]['adjustmentFactor'], time)
               #for runner in md['runners']:
               #   try:
               #      c.execute("insert or replace into  afs values (?,?,?,datetime(?,'unixepoch'))", [runner['id'], race_id, runner['adjustmentFactor'], time ])
               #   except KeyError:
               #      pass
             
             #if( md['eventName'] == 'FC Bastia-Borgo v Concarneau' ):
             #if( md['eventName'] == 'FC Zugdidi v FC Kolkheti Poti' ): print( obj['mc'][0] )

             #if( md['status'] == 'OPEN' and 'OVER_UNDER_' in md['marketType']) :
               #print("Teste", md['status'] )
               #print( obj['mc'][0] )
               #x = 1/0
             #if md['status']=='CLOSED':
             if ((md['status']=='SUSPENDED' or md['status']=='OPEN') and 'OVER_UNDER_' in md['marketType'] ) : #and md['eventName'] == 'FC Zugdidi v FC Kolkheti Poti'
               for runner in md['runners']:
                  print("Tem Runners", runner['id'], race_id, runner['name'],1 if runner['status']=='WINNER' else (0 if runner['status']=='LOSER' else -1), runner['bsp'] if 'bsp' in runner else -1 )
                  c.execute("insert or replace into runners values (?,?,?,?,?)", [runner['id'], race_id, runner['name'],1 if runner['status']=='WINNER' else (0 if runner['status']=='LOSER' else -1), runner['bsp'] if 'bsp' in runner else -1 ])

      conn.commit()

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

def verificaDiretorios():  
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
   print("Carga completa")

if __name__ == '__main__':   
   c, conn = iniciaBanco('bf_under_over.db')
   verificaDiretorios()
   #recriaIndices()
   #removeDuplicatas()
   #consolidaOdds()
   #consolidaAFs()
   #fazLimpeza()