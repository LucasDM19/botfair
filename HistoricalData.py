import logging
import betfairlightweight
import os

"""
Historic is the API endpoint that can be used to
download data betfair provide.

https://historicdata.betfair.com/#/apidocs
"""

def arrumaDiretorio(caminho=None, lista_pastas=None):
   for idx_pasta in range(len(lista_pastas)):
      can = os.path.join(caminho, *lista_pastas[0:idx_pasta+1] )
      if( os.path.isdir(can) ):
         print(can, "Existe")
      else:
         print(can, "N Existe")
         os.mkdir(can) # Crio o diretorio

# setup logging
logging.basicConfig(level=logging.INFO)  # change to DEBUG to see log all updates

# create trading instance
trading = betfairlightweight.APIClient("LucasDM19","C$RHWN2wZq8hwEVg!D4q", app_key="vWAjTJ4soKq4y2kP", certs='d:/python/codes/botfair/')

# login
trading.login()

# get my data
my_data = trading.historic.get_my_data()
for i in my_data:
    print(i)

# get collection options (allows filtering)
collection_options = trading.historic.get_collection_options(
    "Soccer", "Basic Plan", 1, 1, 2017, 31, 1, 2017
)
print(collection_options)

# get advance basket data size
basket_size = trading.historic.get_data_size(
    "Soccer", "Basic Plan", 1, 1, 2017, 31, 1, 2017 # Horse Racing
)
print(basket_size) # {'totalSizeMB': 200, 'fileCount': 121397}

# get file list
file_list = trading.historic.get_file_list(
    "Soccer",
    "Basic Plan",
    from_day=1,
    from_month=1,
    from_year=2017,
    to_day=31,
    to_month=1,
    to_year=2017,
    market_types_collection=["OVER_UNDER_15", "OVER_UNDER_25", "OVER_UNDER_35", "OVER_UNDER_45", "OVER_UNDER_55", "OVER_UNDER_65", "OVER_UNDER_75", "OVER_UNDER_85"],
    countries_collection=[], #"GB", "IE"
    file_type_collection=["M", "E"], # Market ou Event
)
print(file_list)

# download the files
for file in file_list:
    print(file) # /xds_nfs/hdfs_supreme/BASIC/2017/Jan/1/28061114/1.128919106.bz2
    dirs = file.split('/')[3:] # ['BASIC', '2017', 'Jan', '1', '28061114', '1.128919106.bz2']
    dir2 = dirs[:-1]
    arrumaDiretorio(caminho=os.path.join("D:/", "users", "Lucas", "Downloads", "betfair_data", "data_futebol"), lista_pastas=dir2) # Me certifico de que todas as pastas existam
    caminho = os.path.join("D:/", "users", "Lucas", "Downloads", "betfair_data", "data_futebol", *dir2 ) # * https://stackoverflow.com/questions/14826888/python-os-path-join-on-a-list/14826889
    download = trading.historic.download_file(file_path=file, store_directory=caminho)
    print(download)