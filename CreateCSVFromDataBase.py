from BD import BaseDeDados
from datetime import datetime
import pandas as pd

def obtemDadosUnderOver(nome_banco):
   banco = BaseDeDados()
   banco.conectaBaseDados(nome_banco)
   retorno = banco.obtemSumarioOddsUnderOver(minuto=-59)
   df = pd.DataFrame(retorno, columns = ['MarketTime', 'MarketName', 'RunnerName', 'CurrentPrice', 'minuto_antes', 'WinLose', 'EventId'])
   #del df["minuto_antes"] # Simplifica
   print("Dados coletados")
   return df

if __name__ == '__main__':   
   df = obtemDadosUnderOver(nome_banco='D:\\Python\\Codes\\botfair\\bf_under_over_full.db') #'C:\\Users\\Lucas\\Desktop\\bf_under_over_full.db') #Teste
   df.to_csv('out_under_over_full_59.csv', index=False) # Salvando para fuçar depois