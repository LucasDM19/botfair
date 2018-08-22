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
         
   #Levenshtein distance in a recursive way (https://www.python-course.eu/levenshtein_distance.php)
   def LD(self, s, t):
      if s == "":
         return len(t)
      if t == "":
         return len(s)
      if s[-1] == t[-1]:
         cost = 0
      else:
         cost = 1
      
      res = min([LD(s[:-1], t)+1,
               LD(s, t[:-1])+1, 
               LD(s[:-1], t[:-1]) + cost])
      return res