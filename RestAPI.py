#coding: utf-8
import requests #pip install requests
import json

"""
Classe apenas para a utilizacao da API da Betfair.
"""
class BetfairAPI():
   def __init__(self, usuario=None, senha=None, api_key=None, sessionToken=None):
      if( sessionToken is None and usuario is not None and senha is not None and api_key is not None  ): #Eu poderia usar um SessionToken
         self.usuario = usuario
         self.senha = senha
         self.api_key = api_key
         self.sessionToken = self.fazLogin()
      elif( sessionToken is not None ): #So uso o que ja tem
         self.sessionToken = sessionToken
      else:
         raise Exception('Classe API necessita de usuario+senha+api_key OU sessionToken!')
         
   """
   Faz o login na Betfair. Precisa de um usuario, uma senha, a api key, um arquivo de certificado e um arquivo de key. 
   Os ultimos dois arquivos (.crt e .key) poderiam ser gerados usando o modulo SelfSigned.py
   """ 
   def fazLogin(self, certFile='client-2048.crt', keyFile='client-2048.key'):   
      #Tendo certeza de que os arquivos de certificado e keys realmente existem
      import os.path
      if( os.path.isfile(certFile)==False or os.path.isfile(keyFile)==False ): #Se falta algo
         from SelfSigned import create_self_signed_cert
         create_self_signed_cert(".")
         print("Certificado sendo gerado")
         #Se der Exception, so atura
      
      payload = 'username='+self.usuario+'&password='+self.senha
      headers = {'X-Application': self.api_key, 'Content-Type': 'application/x-www-form-urlencoded'}
       
      resp = requests.post('https://identitysso-cert.betfair.com/api/certlogin', data=payload, cert=(certFile, keyFile), headers=headers)
       
      if resp.status_code == 200:
        resp_json = resp.json()
        print( resp_json['loginStatus'] )
        #print( resp_json['sessionToken'] )
        return resp_json['sessionToken']
      else:
        raise Exception(" Falha no processo de Logon da API da Betfair." )
   """
   Apenas verifica se o login foi feito ou nao.
   """
   def estaLogado(self):
      if( self.sessionToken == None ):
         return False
      return True
      
   """
   Metodo generico, que apenas faz as chamadas da API usando rest. Os filtros dos detalhes aparecem apenas nos metodos especificos.
   Existem outros endpoints, como o account.
   """
   def APIRest(self, metodo = "listEventTypes/", json_req='{"filter":{ }}', endpoint = "https://api.betfair.com/exchange/betting/rest/v1.0/" ):
      header = { 'X-Application' : self.api_key, 'X-Authentication' : self.sessionToken ,'content-type' : 'application/json' }
      url = endpoint + metodo
      response = requests.post(url, data=json_req, headers=header)
      #print (json.dumps(json.loads(response.text), indent=3))
      return json.loads(response.text) #Formato Json
   
   """
   Retorna o saldo da conta informada.
   Note que o endpoin é diferente do padrão nesse caaso.
   """
   def obtemSaldoDaConta(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "getAccountFunds/", json_req=json_req, endpoint='https://api.betfair.com/exchange/account/rest/v1.0/')
      
   """
   Exibe todos os mercados (Soccer, Tennis, Golf, Cricket, Rugby Union, etc).
   Soccer eh o Id 1
   Passe a api_key, que deve ser gerada para cada conta. Precisa de SessionToken, que vem depois do login. json_req eh o filtro. 
   Returna o Json, com todos os esportes disponiveis.
   """
   def listaTiposDeEventos(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listEventTypes/", json_req=json_req)

   """
   Obtem a lista de partidas de futebol no periodo determinado.
   Returna o Json
   """
   def obtemPartidasDeFutebol(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listEvents/", json_req=json_req)

   """
   Obtem todos as opcoes de aposta de uma determinada partida.
   Necessario filtro.
   Retorna um Json com todos os mercados.
   """
   def obtemTodosMercadosDasPartidas(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listMarketCatalogue/", json_req=json_req)
      
   """
   Apenas coleta todos os codigos de mercados existentes
   """
   def obtemTodosTiposDeMercados(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listMarketTypes/", json_req=json_req)

   """
   Retorna todas as odds de um grupo de mercados.
   Necessario api_key, sessionToken e o filtro.
   Retorna um Json com todas as odds dos mercados.
   """
   def obtemOddsDosMercados(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listMarketBook/", json_req=json_req)
 
   """
   Efetua uma aposta na BetFair
   Precisa de um marketId (Under/Over 1.5 Goals, por exemplo) e selecionId (Under 1.5 Goals, por exemplo).
   """ 
   def aposta(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "placeOrders/", json_req=json_req)
   
   """
   Consulta todas as apostas correspondidas. 
   Retorna um Json.
   """
   def consultaApostasEfetuadas(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listCurrentOrders/", json_req=json_req)

   """
   Consulta o que aconteceu com a aposta, depois que o evento acabou. 
   """
   def consultaResultadoApostas(self, json_req='{"filter":{ }}'):
      return self.APIRest(metodo = "listMarketBook/", json_req=json_req)