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
            data = json.loads(url.read().decode('utf-8').replace("localStorage.stats=JSON.stringify(","").replace("}]);","}]") )
            #print(data)
            return(data)
      except AttributeError:
         url = urlopen( self.url )
         data = json.loads(url.read().decode('utf-8').replace("localStorage.stats=JSON.stringify(","").replace("}]);","}]") )
         return(data)
      except json.decoder.JSONDecodeError:
         #print("json provavelmente vazio!")
         return {}
         
   #Levenshtein distance in a recursive way (https://www.python-course.eu/levenshtein_distance.php)
   def LD(self, s, t):
      #from Levenshtein import distance #pip install python-Levenshtein
      #return distance(s, t)
      
      ''' From Wikipedia article; Iterative with two matrix rows. '''
      if s == t: return 0
      elif len(s) == 0: return len(t)
      elif len(t) == 0: return len(s)
      v0 = [None] * (len(t) + 1)
      v1 = [None] * (len(t) + 1)
      for i in range(len(v0)):
         v0[i] = i
      for i in range(len(s)):
         v1[0] = i + 1
         for j in range(len(t)):
             cost = 0 if s[i] == t[j] else 1
             v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
         for j in range(len(v0)):
             v0[j] = v1[j]
             
      return v1[len(t)]