'''
This python code uses the script dhusget.sh provided by copernicus program to download Sentinel data
This code requires three arguments to run properly:
    username : The username created by the user when registering to copernicus service
    password : The password created by the user when registering to copernicus service
    YAML_file: The file that contains all options necessary to download sentinel data 
    
This code will genrate the files/folders that are supposed to be generated when dhusget script. These files may include:
    product_list(F)
    MANIFEST(D)
    PRODUCT(D)
    logs(D)
    failed_MD5_check_list.txt(F)
    offline_product_list.txt(F)
    file.xml(F)
    file.csv(F)
    log.txt(F)
'''

# Written by Anes Ouadou


import subprocess
import yaml

import os
import sys


#%% command line as a list
command_line = []
command_line.append('./dhusget.sh')

#%% define variables

#LOGIN OPTIONS:
link = 'https://scihub.copernicus.eu/dhus'
try:
    username = sys.argv[1] 
except Exception:
    print("username not supplied")
    sys.exit()
    
try: 
    password = sys.argv[2] 
except Exception:
    print("password not supplied")
    sys.exit()
    
command_line.append('-d')
command_line.append(link)

command_line.append('-u')
command_line.append(username)

command_line.append('-p')
command_line.append(password)

#print(command_line)

#%% read YAML file
try:
    yaml_file = sys.argv[3] 
except Exception:
    print('yaml file not supplied')
    sys.exit()
    
with open(yaml_file) as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    sentinel_opt = yaml.load(file, Loader=yaml.FullLoader)

    #print(sentinel_opt)

options = list(sentinel_opt.keys())

print("options offered are: ",format(options))

#SEARCH QUERY OPTIONS:
'''
mission_name          -m
instrument_name       -i
time_in_hours         -t
ingestion_date_FROM   -s
ingestion_date_TO     -e
sensing_date_FROM     -S
sensing_date_TO       -E
file                  -f
coordinates           -c 
product_type          -T
free_OpenSearch_query -F
'''
#mission_name
if 'mission_name' in options:
    mission_name_opt = sentinel_opt['mission_name']
    command_line.append('-m')
    command_line.append(mission_name_opt)
else:
    mission = 'Sentinel-2'

#instrument_name
if 'instrument_name' in options:
    instrument_name_opt = sentinel_opt['instrument_name']
    command_line.append('-i')
    command_line.append(instrument_name)

#time_in_hours    
if 'time_in_hours' in options:
    time_in_hours_opt = sentinel_opt['time_in_hours']
    command_line.append('-t')
    command_line.append(time_in_hours_opt)

# ingestion_date_FROM
if 'ingestion_date_FROM' in options:
    time_in_hours_opt = sentinel_opt['ingestion_date_FROM']
    command_line.append('-s')
    command_line.append(time_in_hours_opt)

#ingestion_date_TO
if 'ingestion_date_TO' in options:
    ingestion_date_TO_opt = sentinel_opt['ingestion_date_TO']
    command_line.append('-e')
    command_line.append(ingestion_date_TO_opt)

# sensing_date_FROM
if 'sensing_date_FROM' in options:
    time_in_hours_opt = sentinel_opt['sensing_date_FROM']
    command_line.append('-S')
    command_line.append(time_in_hours_opt)

#sensing_date_TO
if 'sensing_date_TO' in options:
    sensing_date_TO_opt = sentinel_opt['sensing_date_TO']
    command_line.append('-E')
    command_line.append(sensing_date_TO_opt)

# file
if 'file' in options:
    file_opt = sentinel_opt['file']
    command_line.append('-f')
    command_line.append(file_opt)

# coordinates
if 'coordinates' in options:
    coordinates_opt = sentinel_opt['coordinates']
    command_line.append('-c')
    command_line.append(coordinates_opt)

# product_type
if 'product_type' in options:
    product_type_opt = sentinel_opt['product_type']
    command_line.append('-T')
    command_line.append(product_type_opt)
    
# free_OpenSearch_query
if 'free_OpenSearch_query' in options:
    free_OpenSearch_query_opt = sentinel_opt['free_OpenSearch_query']
    command_line.append('-F')
    command_line.append(free_OpenSearch_query_opt)


#SEARCH RESULT OPTIONS:
'''
results -l
page    -P
XMLfile -q
CSVfile -C
'''

#results -l
if 'results' in options:
    results_opt = sentinel_opt['results']
    command_line.append('-l')
    command_line.append(results_opt)

#page    -P
if 'page' in options:
    page_opt = sentinel_opt['page']
    command_line.append('-P')
    command_line.append(page_opt)

#XMLfile -q
if 'XMLfile' in options:
    free_OpenSearch_query_opt = sentinel_opt['XMLfile']
    command_line.append('-q')
    if free_OpenSearch_query_opt != None:
        command_line.append(free_OpenSearch_query_opt)

#CSVfile -C
if 'CSVfile' in options:
    CSVfile_opt = sentinel_opt['CSVfile']
    command_line.append('-C')
    if CSVfile_opt != None:
        command_line.append(free_OpenSearch_query_opt)

#DOWNLOAD OPTIONS:
'''
download_option         -o
path                    -O  
wget_retries            -N 
MD5_file                -R
remove_MD5              -D
file_format             -r
lock_folder             -L 
concurrent_downloads    -n
offline_product_wait    -w  
offline_product_retries -W         
'''        
#download_option         -o
if 'download_option' in options:
    download_option_opt = sentinel_opt['download_option']
    command_line.append('-o')
    command_line.append(download_option_opt)

#path                    -O  
if 'path' in options:
    path_opt = sentinel_opt['path']
    command_line.append('-O')
    command_line.append(path_opt)

#wget_retries            -N 
if 'wget_retries' in options:
    wget_retries_opt = sentinel_opt['wget_retries']
    command_line.append('-N')
    command_line.append(wget_retries_opt)

#MD5_file                -R
if 'MD5_file' in options:
    MD5_file_opt = sentinel_opt['MD5_file']
    command_line.append('-R')
    if MD5_file_opt != None:
        command_line.append(free_OpenSearch_query_opt)

#remove_MD5              -D
if 'remove_MD5' in options:
    command_line.append('-D')

#file_format             -r
if 'file_format' in options:
    file_format_opt = sentinel_opt['file_format']
    command_line.append('-r')
    if file_format_opt != None:
        command_line.append(free_OpenSearch_query_opt)

#lock_folder             -L 
if 'lock_folder' in options:
    lock_folder_opt = sentinel_opt['lock_folder']
    command_line.append('-L')
    command_line.append(lock_folder_opt)

#concurrent_downloads    -n
if 'concurrent_downloads' in options:
    concurrent_downloads_opt = sentinel_opt['concurrent_downloads']
    command_line.append('-n')
    if concurrent_downloads_opt != None:
        command_line.append(concurrent_downloads_opt)

#offline_product_wait    -w  
if 'offline_product_wait' in options:
    offline_product_wait_opt = sentinel_opt['offline_product_wait']
    command_line.append('-w')
    command_line.append(offline_product_wait_opt)

#offline_product_retries -W          
if 'offline_product_retries' in options:
    offline_product_retries_opt = sentinel_opt['offline_product_retries']
    command_line.append('-W')
    command_line.append(offline_product_retries_opt)


# command execution

print(command_line)

with open('log.txt', 'w') as f:
    p1 = subprocess.run(command_line,stdout=f,text=True)

print(p1.args)
print(p1.stdout)
