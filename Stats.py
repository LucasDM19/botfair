"""
Uma classe apenas para obter os dados do Json, com estatisticas.
"""
class SoccerStats():
   def __init__(self, url='http://foob.ar/resource.json'):
      self.url = url
   def getStats(self):
      try:
         from urllib.request import urlopen
      except ImportError:
         from urllib2 import urlopen
      import json 
      try:
         with urlopen( self.url ) as url:
            data = json.loads(url.read().decode())
            #print(data)
            return(data)
      except AttributeError:
         url = urlopen( self.url )
         data = json.loads(url.read().decode())
         return(data)