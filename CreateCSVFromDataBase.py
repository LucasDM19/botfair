from BD import BaseDeDados
from datetime import datetime
import pandas as pd

def obtemDadosUnderOver(nome_banco):
   banco = BaseDeDados()
   banco.conectaBaseDados(nome_banco)
   retorno = banco.obtemSumarioOddsUnderOver(minuto=-90)
   #for r in retorno: print(r)
   df = pd.DataFrame(retorno, columns = ['MarketTime', 'MarketName', 'RunnerName', 'CurrentPrice', 'minuto_antes', 'WinLose', ])
   print("Dados coletados")
   return df

if __name__ == '__main__':   
   df = obtemDadosUnderOver(nome_banco='D:\\Python\\Codes\\botfair\\bf_under_over_full.db') #'C:\\Users\\Lucas\\Desktop\\bf_under_over_full.db') #Teste
   df.to_csv('out_under_over_full_90.csv', index=False) # Salvando para fuçar depois