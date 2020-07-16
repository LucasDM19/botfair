from BD import BaseDeDados
from datetime import datetime

def obtemDadosUnderOver(nome_banco):
   banco = BaseDeDados()
   banco.conectaBaseDados(nome_banco)
   data_inicial, data_final, total_partidas = banco.obtemSumarioDasPartidas()
   print("QTD=", total_partidas )
   partidas = banco.obtemPartidas(qtd_corridas=total_partidas, ordem="ASC") # ASC - Antigas primeiro, DESC - Recentes primeiro
   nomes_colunas = [] # Usa uma vez só
   for partida in partidas:
      dados_corrida = [] # Linha sobre a corrida em si
      print("Partida=", partida, ", são=", datetime.now().time() )
   
   print("Fim, por enquanto")

if __name__ == '__main__':   
   df = obtemDadosUnderOver(nome_banco='bf_under_over_leste_europeu.db') 
   df.to_csv('out_les_eur_tst.csv', index=False) # Salvando para fuçar depois