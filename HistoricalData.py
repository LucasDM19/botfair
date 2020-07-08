import logging
import betfairlightweight
import os
import pickle
from Hush import usuarioAPI, senhaAPI, APIKey

"""
Historic is the API endpoint that can be used to
download data betfair provide.

https://historicdata.betfair.com/#/apidocs
"""

nome_dts_pickle = 'hist_lista_datas.pkl'

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
   trading = betfairlightweight.APIClient(usuarioAPI,senhaAPI, app_key=APIKey, certs='d:/python/codes/botfair/')

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
   nome_arq_pickle = 'hist_lista_arquivos.pkl'
   if( os.path.isfile(nome_arq_pickle) ): # Devo continuar a processar a lista
      with open(nome_arq_pickle, 'rb') as f:
         file_list = pickle.load(f)
   else: # Crio uma lista nova
      file_list = obtemListaDeArquivos(trading, d_ini=d_ini, m_ini=mes, a_ini=ano, d_fim=d_fim, m_fim=mes, a_fim=ano) # Só pode um mês e um ano

   lista_pendentes = [fil for fil in file_list] # Quantos arquivos ainda não foram baixados
   # download the files
   for file in file_list:
       print(file) # /xds_nfs/hdfs_supreme/BASIC/2017/Jan/1/28061114/1.128919106.bz2
       dirs = file.split('/')[3:] # ['BASIC', '2017', 'Jan', '1', '28061114', '1.128919106.bz2']
       dir2 = dirs[:-1]
       arrumaDiretorio(caminho=os.path.join("D:/", "users", "Lucas", "Downloads", "betfair_data", "data_futebol"), lista_pastas=dir2) # Me certifico de que todas as pastas existam
       caminho = os.path.join("D:/", "users", "Lucas", "Downloads", "betfair_data", "data_futebol", *dir2 ) # * https://stackoverflow.com/questions/14826888/python-os-path-join-on-a-list/14826889
       download = trading.historic.download_file(file_path=file, store_directory=caminho)
       print(download)
       lista_pendentes.remove(file) # Foi processado
       salvaProgresso(lista_pendentes, nome_arq_pickle) # Armazena a lista do que falta
       
   os.remove(nome_arq_pickle) # Quando tudo estiver ok, mata o Pickle
   
if( os.path.isfile(nome_dts_pickle) ): # Devo continuar a processar a lista
   with open(nome_dts_pickle, 'rb') as f:
      lista_datas = pickle.load(f)
else: # Crio uma lista nova
   import datetime 
   lista_datas = []
   d_ini=4
   m_ini=2
   a_ini=2017
   d_fim=31
   m_fim=12
   a_fim=2017
   dt_inicial = datetime.date(a_ini, m_ini, d_ini)
   dt_final = datetime.date(a_fim, m_fim, d_fim)
   dt_tmp = dt_inicial
   while( dt_tmp <= dt_final ):
      lista_datas.append( [dt_tmp.day, dt_tmp.month, dt_tmp.year] )
      dt_tmp += datetime.timedelta(days=1)

trading = conectaNaBetFair()
lista_datas_pendentes = [dat for dat in lista_datas] # Quantas datas ainda não foram enviadas
for dl in lista_datas:
   print( dl )
   baixaArquivosDoMes(trading, dia=dl[0], mes=dl[1], ano=dl[2] )
   lista_datas_pendentes.remove(dl)
   salvaProgresso(lista_datas_pendentes, nome_dts_pickle)
   
os.remove(nome_dts_pickle) # Quando tudo estiver ok, mata o Pickle