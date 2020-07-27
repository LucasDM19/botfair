from BD import BaseDeDados
from datetime import datetime
import pandas as pd

def obtemDadosUnderOver(nome_banco):
   banco = BaseDeDados()
   banco.conectaBaseDados(nome_banco)
   retorno = banco.obtemSumarioOddsUnderOver(minuto=-70)
   #for r in retorno: print(r)
   df = pd.DataFrame(retorno, columns = ['MarketTime', 'MarketName', 'RunnerName', 'CurrentPrice', 'minuto_antes', 'WinLose', ])
   print("Dados coletados")
   return df

if __name__ == '__main__':   
   df = obtemDadosUnderOver(nome_banco='C:\\Users\\Lucas\\Desktop\\bf_under_over_full.db') 
   df.to_csv('out_under_over_full.csv', index=False) # Salvando para fuçar depois