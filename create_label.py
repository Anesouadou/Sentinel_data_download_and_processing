import os
import sys
import numpy as np
import matplotlib.pyplot as plt

import rasterio as rio
from rasterio import features

import pandas as pd
import geopandas as gpd

from shapely.geometry import Point
from geopandas.tools import sjoin, overlay

import geojson
import json
from shapely.geometry import Polygon
from PIL import Image, ImageDraw
import copy
import argparse

#######################  DEFINE ARGUMENTS ########################################################

parser = argparse.ArgumentParser()

parser.add_argument('--poly','-p',
                    help = 'list of polygons as shp file or geojson file',
                    metavar='',
                    required = True)
                   
parser.add_argument('--log',
                    help = 'text file that stores the status of each image',
                    default = 'create_label.log')         

args = parser.parse_args()

#####################    GET ARGUMENTS   ######################################################

polygon_list = args.poly 

fileout = open(args.log,'w')

folder_img_jp2 = 'images_files_2A'
folder_img_npy = 'images_npy'
folder_img_tci = 'TCI_npy'

cloud_cover    = 'cloud_mask_npy'

print('#########  Read polygon ############')

polygon_truth = gpd.read_file(polygon_list)


fileout.write('the length of geometry: '.format(len(polygon_truth['geometry'])))


print('#########  Create necessary folders if they are not already created ############')

if os.path.isdir("labels_npy"): # store created labels as npy
    print("folder already exists")
else:
    os.mkdir("labels_npy")

if os.path.isdir("labels_npy_raw"): # store created labels as npy
    print("folder already exists")
else:
    os.mkdir("labels_npy_raw")
    
if os.path.isdir("figures"): # to store images as png
    print("folder already exists")
else:
    os.mkdir("figures")
    
if os.path.isdir("figures/labels_png"): # store created labels as png
    print("folder already exists")
else:
    os.mkdir("figures/labels_png")

if os.path.isdir("figures/labels_png_raw"): # store created labels as png
    print("folder already exists")
else:
    os.mkdir("figures/labels_png_raw")
    
if os.path.isdir("figures/labels_solid_images_png"): # plot label as solid polygon on top of input image
    print("folder already exists")
else:
    os.mkdir("figures/labels_solid_images_png")
    
if os.path.isdir("figures/labels_solid_tci_png"): # plot label as solid polygon on top of tci image
    print("folder already exists")
else:
    os.mkdir("figures/labels_solid_tci_png")

print('#########  Read image list from source folder ############')

image_list = os.listdir(folder_img_jp2)
image_list = list(map(str.strip,image_list))

img_poly_list = []

print("\n")
print('#########  Start label creation ... ############')
    

for img in image_list:
    elem = img.split('_')
    
    band_list = os.listdir(folder_img_jp2+'/'+img+'/R10m')
    band1 = band_list[0]
    name = band1.split('_')
    
    image_jp2       = '{}/{}/R10m/{}_{}_TCI_{}'.format(folder_img_jp2,img,name[0],name[1],name[3])
    img_tci_name    = '{}/{}_TCI.npy'.format(folder_img_tci,img)
    img_npy_name    = '{}/{}_10m.npy'.format(folder_img_npy,img)
    cloud_mask_name = '{}/{}_'.format(cloud_cover,img)
    
    print("\n")
    print('Processing: {}'.format(image_jp2))
    print('            {}'.format(img_tci_name))
    print('            {}'.format(img_npy_name))
    print('            {}'.format(cloud_mask_name))
    
    fileout.write("\n")
    fileout.write('Processing: {}'.format(image_jp2))
    fileout.write('            {}'.format(img_tci_name))
    fileout.write('            {}'.format(img_npy_name))
    fileout.write('            {}'.format(cloud_mask_name))
    
    img_rio   = rio.open(image_jp2)
    image_tci = np.load(img_tci_name)
    image_npy = np.load(img_npy_name)
    cloud_mask = np.load(cloud_mask_name)
    
    print(img_rio.crs)
    fileout.write(img_rio.crs)
    
    crs_ref = img_rio.crs
    
    if polygon_truth.crs != crs_ref:
        fileout.write('     polygon crs is not {}'.format(crs_ref))
        fileout.write('     converting polygon crs to {}'.format(crs_ref))
        burn_truth = polygon_truth.to_crs(crs_ref)
        
    else:
        print('     polygon crs is {}'.format(crs_ref))
        burn_truth = copy.copy(polygon_truth)

    fileout.write('{}'.format(burn_truth.crs))

    mask_label_raw = features.rasterize(burn_truth['geometry'],
                                   out_shape = img_rio.shape,
                                   fill = 0,
                                   out = None,
                                   transform = img_rio.transform,
                                   all_touched = False,
                                   default_value = 1,
                                   dtype = None)       
    
    if np.sum(mask_label_raw) == 0:
        fileout.write('     there are no burned areas in this raster')
        continue
    else:
        np.save('labels_npy_raw/{}_R10m_label_solid.npy'.format(img),mask_label_raw)
        plt.figure(figsize = (25,25))
        plt.imshow(mask_label_raw)
        plt.savefig('figures/labels_png_raw/{}_R10m_labelraw.png'.format(img))
        plt.close()

        plt.figure(figsize = (25,25))
        plt.imshow(image_npy)
        plt.imshow(labels_png_raw, alpha=0.3)
        plt.savefig('figures/labels_solid_images_png/{}_R10m_label.png'.format(img))
        plt.close()

        plt.figure(figsize = (25,25))
        plt.imshow(image_tci)
        plt.imshow(labels_png_raw, alpha=0.3)
        plt.savefig('figures/labels_solid_tci_png/{}_R10m_label.png'.format(img))
        plt.close()
        
        # reverse cloud mask:
        cloud_mask_reverse = cloud_mask * -1
        cloud_mask_reverse = cloud_mask_reverse + 1            
            
        mask_label  = np.multiply(mask_label_raw,cloud_mask_reverse)
        
        np.save('labels_npy_raw/{}_R10m_label_solid.npy'.format(img),mask_label)
        
        np.save('labels_npy/{}_R10m_label.npy'.format(img),mask_label)
        plt.figure(figsize = (25,25))
        plt.imshow(mask_label)
        plt.savefig('figures/labels_png/{}_R10m_label.png'.format(img))
        plt.close()

fileout.close()

