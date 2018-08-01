"""
Arquivo separado para testar o maximo possivel de casos do BotFair.
-Testar uma requicao com parametros insuficientes (DSC-0018 - Mandatory Not Defined) Link: http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/Additional+Information
"""

from unittest import TestCase
import unittest
from BotFair import *

# class ConfigFileTest(TestCase):
   # def setUp(self):
      # self.arquivo = ConfigFile()
      
   # def test_ValidFileLoad(self):
      # self.arquivo.algo = 0
      # self.arquivo.chama()
      
      # #Verifica se o arquivo foi carregado adequadamente
      # self.assertEqual( propriedade1, self.arquivo.propriedade1 )

class BasicTest(TestCase):
   def setUp(self):
      self.API_URL = ''
      
   def test_IsAPIURLUP(self):
      import urllib.request
      try:
         retorno = urllib.request.urlopen("http://www.stackoverflow.com").getcode()
      except urllib.error.HTTPError:
         print("ruim")
if __name__ == "__main__":
   unittest.main