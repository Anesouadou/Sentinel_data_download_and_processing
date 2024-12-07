#!/usr/bin/env python
# coding: utf-8
'''
This python code uses files and folders generated from the download operation to extract Sentinel2 images to:
    unzip image files and place then in a new folder called PRODUCT_unzip
    create a text file image_file_list_1C.txt that contains list of type 1C images 
    create the folder image_files_1C
    move images type 1C from unzipped folder to image_files_1C folder 
    create a text file image_file_list_2A.txt that contains list of type 2A images 
    create the folder image_files_2A
    move images type 2A from unzipped folder to image_files_2A folder 
'''

# Written by Anes Ouadou

import zipfile
import os
import sys
import shutil


# # read product_list
folder_list = os.listdir('PRODUCT/')
'''
file1       = open("product_list","r")
folder_list = file1.readlines()
file1.close()
'''
folder_list = list(map(str.strip,folder_list))
print(folder_list)

# # Filter the list to keep image file names only


img_folder_list = []
for idx in list(range(len(folder_list))):
    img_folder_list.append(folder_list[idx])
    

# # Filter the list again to remove zero files 


img_folder_list_non_zero = []
fileout = open("images_file_list.txt","w")

for img_file in img_folder_list:
    # check if file is zero
    if os.stat("PRODUCT/"+img_file).st_size == 0:
        print(img_file+" is empty")
        continue
    else:
        test_zip = zipfile.is_zipfile('PRODUCT/'+img_file)
        if test_zip:
            img_folder_list_non_zero.append(img_file)
            fileout.write(img_file+"\n")
        else:
            print(' {} is a bad zip file'.format(img_file))

fileout.close()   


# # Unzip compressed files


for img_zip in img_folder_list_non_zero:
    path_to_zip_file   = "PRODUCT/"+img_zip
    path_to_unzip_file = "PRODUCT_unzip/"+img_zip
    if os.path.isfile(path_to_unzip_file):
        continue
    else:
        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
            zip_ref.extractall('PRODUCT_unzip/')


# # create separate lists for 1C and 2A

image_file_list_1C = []
fileout1 = open("images_files_list_1C.txt","w")

image_file_list_2A = []
fileout2 = open("images_files_list_2A.txt","w")

for file_name in img_folder_list_non_zero:
    
    if file_name[8:10] == '1C':
        image_file_list_1C.append(file_name)
        fileout1.write(file_name+"\n")
    
    elif file_name[8:10] == '2A':
        image_file_list_2A.append(file_name)
        fileout2.write(file_name+"\n")

fileout1.close()
fileout2.close()


# # Create new folder to move img_files to


if os.path.isdir("images_files_1C"):
    print("folder already exists")
else:
    os.mkdir("images_files_1C")
    
if os.path.isdir("images_files_2A"):
    print("folder already exists")
else:
    os.mkdir("images_files_2A")


# # move img_files to newly created folder

# ## Sentinel2-1C 


for img_unzip_temp in image_file_list_1C:
    img_unzip = img_unzip_temp.split('.')[0]   
    
    path_to_unzip_file = "PRODUCT_unzip/"+img_unzip+".SAFE/GRANULE/"
    arr = os.listdir(path_to_unzip_file)
    path_to_unzip_file_new = path_to_unzip_file+arr[0]+"/IMG_DATA"
    
    # copy operation
    
    dest_path = "images_files_1C/"+img_unzip+"/"
    
    shutil.copytree(path_to_unzip_file_new, dest_path)
    

# ## Sentinel2-2A


for img_unzip_temp in image_file_list_2A:
    img_unzip = img_unzip_temp.split('.')[0]

    path_to_unzip_file = "PRODUCT_unzip/"+img_unzip+".SAFE/GRANULE/"
    print(' this is the file we are copying',path_to_unzip_file)
    arr = os.listdir(path_to_unzip_file)
    
    path_to_unzip_file_IMG = path_to_unzip_file+arr[0]+"/IMG_DATA/R10m"
    path_to_unzip_file_QI  = path_to_unzip_file+arr[0]+"/QI_DATA"

    # copy operation
    
    dest_path1 = "images_files_2A/"+img_unzip+"/R10m"
    dest_path2 = "images_files_2A/"+img_unzip+"/QI_DATA"
    
    shutil.copytree(path_to_unzip_file_IMG, dest_path1)
    shutil.copytree(path_to_unzip_file_QI, dest_path2)

