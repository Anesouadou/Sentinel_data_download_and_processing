import os
import sys
import shutil 
import numpy as np

import rasterio as rio
from rasterio import features
from rasterio.plot import show

import geopandas as gpd
import matplotlib.pyplot as plt

from PIL import Image, ImageDraw
from shapely.geometry import Polygon
from bs4 import  BeautifulSoup

import logging
import copy

import argparse

#######################  DEFINE ARGUMENTS ########################################################

parser = argparse.ArgumentParser()

parser.add_argument('--nodata','-nd',
                    help = 'the percentage threshold of the maximum size nodata in the image',
                    required = True,
                    type = float,
                    default = 0.8)
                    
parser.add_argument('--valid','-val',
                    help = 'the theshold of percentage of valid data in a raster',
                    metavar='',
                    type=float,
                    required = True,
                    default=0.25)

parser.add_argument('--norm','-N',
                   help = 'the normalization options 1: 2:',
                   metavar='',
                   type = int,
                   required = True)

parser.add_argument('--source','-s',
                    help = 'type of image to be turned in to npy/png: 1C or 2A',
                    metavar='',
                    required = True)
                    
parser.add_argument('--log',
                    help = 'text file that stores the status of each image',
                    default = 'tif2norm.log')         

args = parser.parse_args()

#####################    GET ARGUMENTS   ######################################################

nodata_thresh        = args.nodata
valid_data_threshold = args.valid 
norm_opt             = args.norm
source               = args.source

if source == '1C':
    folder_in = 'images_files_1C'
elif source == '2A':
    folder_in = 'images_files_2A'
    
fileout = open(args.log,'w')

fileout.write('No data percentage is: {} \n'.format(nodata_thresh*100))
fileout.write('valid data percentage is: {} \n'.format(valid_data_threshold*100))

########################   FUNCTIONS   ########################################################

# compute metrics values
def compute_metrics(band):
    min1    = np.min(band[np.nonzero(band)])

    max1          = np.max(band[np.nonzero(band)])
    mean1         = np.mean(band[np.nonzero(band)])
    std_div1      = np.std(band[np.nonzero(band)])
    Q1            = np.quantile(band[np.nonzero(band)],0.25)
    Q3            = np.quantile(band[np.nonzero(band)],0.75)
    percentile_1  = np.quantile(band[np.nonzero(band)],0.01)
    percentile_99 = np.quantile(band[np.nonzero(band)],0.99)
        
    IQR     = Q3 - Q1
    com_max = Q3 + (1.5*IQR)
    
    return min1,max1,mean1,std_div1,Q1,Q3,IQR,com_max,percentile_1,percentile_99

# normalize
def normalize_global(band,metrics,range_global,opt):
    min1,max1,mean1,std_div1,Q1,Q3,IQR,com_max,percentile1,percentile99 = metrics
    
    if opt == 1:
        print('signle band is normalized based on globlal min {} and boxplot computed max {} WITHOUT nodata'.format(min1,com_max))
        band_new      = band - min1 + 1
        band_clipped  = np.clip(band_new,0,com_max)
        band_norm     = np.divide(band_clipped,range_global)
        
    elif opt == 2:
        print('signle band is normalized based on global percentile-1 {} and percentile-99 {} computed WITH nodata'.format(percentile1,percentile99))
        
        band_bottom   = copy.copy(band)
        band_bottom[(band_bottom>0) & (band_bottom<percentile1)] = percentile1
        
        band_new      = band_bottom - percentile1 + 1
        band_clipped  = np.clip(band_new,0,percentile99)
        band_norm     = np.divide(band_clipped,range_global)
        
    else:
        print('the selected option {} does not exist normalization process will be terminated'.format(opt))
        sys.exit()
        
    band_norm_255 = band_norm*255
    band_norm_255_uint8   = band_norm_255.astype(np.uint8)  
    
    return band_norm,band_norm_255_uint8

# print to logging file
def print_to_file(band1_metrics,band2_metrics,band3_metrics):

    logging.info('band1 Q2  original WITHOUT nodata: {} '.format(band1_metrics[0]))
    logging.info('band1 Q3  original WITHOUT nodata: {} '.format(band1_metrics[1]))
    logging.info('band1 max original WITHOUT nodata: {} '.format(band1_metrics[2]))
    
    logging.info('band2 Q2  original WITHOUT nodata: {} '.format(band2_metrics[0]))
    logging.info('band2 Q3  original WITHOUT nodata: {} '.format(band2_metrics[1]))
    logging.info('band2 max original WITHOUT nodata: {} '.format(band2_metrics[2]))
    
    logging.info('band3 Q2  original WITHOUT nodata: {} '.format(band3_metrics[0]))
    logging.info('band3 Q3  original WITHOUT nodata: {} '.format(band3_metrics[1]))
    logging.info('band3 max original WITHOUT nodata: {} '.format(band3_metrics[2]))

    return

# create necessary folder
fileout.write('creating necessary folders')

################################################
if os.path.isdir('TCI_npy'):
    fileout.write('folder already exists')
else:
    os.mkdir('TCI_npy')
    
if os.path.isdir("images_npy"):
    fileout.write("images_npy folder already exists")
else:
    os.mkdir("images_npy")

if os.path.isdir("cloud_mask_npy"):
    fileout.write("cloud_mask_npy folder already exists")
else:
    os.mkdir("cloud_mask_npy")

################################################        
if os.path.isdir("figures"):
    fileout.write("figures folder already exists")
else:
    os.mkdir("figures")

if os.path.isdir('figures/TCI_png'):
    fileout.write('folder already exists')
else:
    os.mkdir('figures/TCI_png')
    
if os.path.isdir("figures/images_png"):
    fileout.write("figures/images_png folder already exists")
else:
    os.mkdir("figures/images_png")

if os.path.isdir("figures/cloud_mask"):
    fileout.write("figures/cloud_mask folder already exists")
else:
    os.mkdir("figures/cloud_mask")

################################### Read images and information ###################################

images_list = os.listdir(folder_in)
images_list = list(map(str.strip,images_list))

images_to_drop = []
images_to_keep = []

fileout.write('Start image processing \n')

for images in images_list:

    fileout.write('processing: {}\n'.format(images))
    
    # convert TCI jp2 to npy
    bands    = os.listdir(folder_in+'/'+images+'/R10m')
    elem     = bands[0].split('_')
    band_tci = elem[0]+'_'+elem[1]+'_TCI_10m.jp2'
     
    band_target = rio.open('{}/{}/R10m/{}'.format(folder_in,images,band_tci))
    
    band_1 = band_target.read(1)
    band_2 = band_target.read(2)
    band_3 = band_target.read(3)

    band_new_255 = np.stack((band_1,band_2,band_3),axis =2)
    band_new     = np.divide(band_new_255,255)
    np.save('TCI_npy/{}_TCI.npy'.format(images),band_new)
    
    Im = Image.fromarray(band_new_255)
    Im.save('figures/TCI_png/{}_TCI.png'.format(images))

    # check nodata percentage
    
    # Read Bands
    
    # input raster
    img_04 = rio.open('{}/{}/R10m/{}_{}_B04_{}'.format(folder_in,images,elem[0],elem[1],elem[3]))
    img_03 = rio.open('{}/{}/R10m/{}_{}_B03_{}'.format(folder_in,images,elem[0],elem[1],elem[3]))
    img_02 = rio.open('{}/{}/R10m/{}_{}_B02_{}'.format(folder_in,images,elem[0],elem[1],elem[3]))
        
    img_crs = img_04.crs

    band_04 = img_04.read() # B04 Red
    band_03 = img_03.read() # B03 Green
    band_02 = img_02.read() # B02 Blue
  
    total_pixels            = band_04.shape[1]*band_04.shape[2]
    band_no_data            = np.count_nonzero(band_04==0)
    band_no_data_percentage = np.count_nonzero(band_04==0)/total_pixels
    
    fileout.write('     no data percentage: {} \n'.format(band_no_data_percentage*100))
    
    if band_no_data_percentage > nodata_thresh:
        images_to_drop.append(images)
        fileout.write('     no data percentage in this image is higher than thrshold {}'.format(nodata_thresh))
        fileout.write('     this image will be dropped')
        continue
    
    else:
        
        # get gml file and create matrix with the masks
        gml_file = '{}/{}/QI_DATA/MSK_CLOUDS_B00.gml'.format(folder_in,images)
        with open(gml_file,'r') as page:
            gml = BeautifulSoup(page, "lxml")
        
        # Get crs
        crs_element = gml.find_all('gml:envelope') # element
        
        if len(crs_element) == 0:
            fileout.write('     there is no cloud in this raster')
            mask_reverse = np.ones((img_04.height,img_04.width))
            
        else:
            fileout.write('     building cloud mask')
            
            cloud_mask = Image.new('L', (img_04.height,img_04.width), 0) 
            
            crs_tag = crs_element[0] # tag
            b_name = crs_tag.get('srsname')
            crs_code = b_name.split(':')[-1]
            gml_crs = 'epsg:{}'.format(crs_code)
            
            # Get the polygons in a list
            boundary = gml.find_all('eop:maskfeature')
            
            polygon_list = []
            for poly_idx in list(range(len(boundary))):
                element = boundary[poly_idx]
                elem_polygon = element.find_all('gml:poslist')#,{'srsdimension':'2'})
                polygon_text  = elem_polygon[0].text
                polygon_coordiantes = polygon_text.split(' ')

                coordinates = []
                for cor_idx in list(range(int(len(polygon_coordiantes)/2))):
                    x_cor = float(polygon_coordiantes[2*cor_idx])
                    y_cor = float(polygon_coordiantes[(2*cor_idx)+1])
                    cor_pair = [x_cor,y_cor]
                    coordinates.append(cor_pair)
                                                            
                polygon = Polygon(coordinates)
                polygon_list.append(polygon)
            
            dict_poly = {'polygons':polygon_list}
            gdf = gpd.GeoDataFrame(dict_poly,crs=gml_crs,geometry='polygons')
                
            if gml_crs == img_crs:
                poly_inter = gdf['polygons']
            
            else:
                gdf_new    = gdf.to_crs(img_crs)
                poly_inter = gdf_new['polygons']
                
            # plot cloud masks into a square matrix 
            
            cloud_mask = features.rasterize(poly_inter,
                                            out_shape = img_04.shape,
                                            fill = 0,
                                            out = None,
                                            transform = img_04.transform,
                                            all_touched = False,
                                            dtype = None)
            '''                                
            for idx in list(range(len(poly_inter))):
                elem0 = poly_inter.iloc[idx]

                if elem0.geom_type == 'Polygon':
                    polygon_coor_geo = list(elem0.exterior.coords)

                    # convert polygon coordinates to indeces
                    polygon_coor_matrix = []

                    for cor in polygon_coor_geo:
                        cur_cor_idx = img_04.index(cor[0],cor[1])
                        polygon_coor_matrix.append((cur_cor_idx[1],cur_cor_idx[0]))

                    # create label matrix (npy)
                    ImageDraw.Draw(cloud_mask).polygon(polygon_coor_matrix, outline=1, fill=1)

                    # mask = np.array(cloud_mask)

                elif elem0.geom_type == 'MultiPolygon':
                    Mpoly_elem = elem0.geoms
                    for elem1 in Mpoly_elem:
                        polygon_coor_geo = list(elem1.exterior.coords)
                        
                        # convert polygon coordinates to indeces
                        polygon_coor_matrix = []
                        for cor in polygon_coor_geo:
                            cur_cor_idx = img_04.index(cor[0],cor[1])
                            polygon_coor_matrix.append((cur_cor_idx[1],cur_cor_idx[0]))

                        ImageDraw.Draw(cloud_mask).polygon(polygon_coor_matrix, outline=1, fill=1)
            '''
            mask_reverse = cloud_mask * -1
            mask_reverse = mask_reverse + 1            
            
            np.save('cloud_mask_npy/{}_CM.npy'.format(images),cloud_mask)
            
            mask_255 = cloud_mask * 255
            mask_255 = mask_255.astype(np.uint8)
            im = Image.fromarray(mask_255)
            im.save('figures/cloud_mask/{}_CW.png'.format(images))
            
        # update raster nodata to include cloud data
        
        band_04_update = band_04 * mask_reverse
        
        # compute percentage of valid data

        band_no_data_04  = np.count_nonzero(band_04_update==0)
        
        valid_data       = total_pixels - band_no_data_04
        valid_data_ratio = valid_data/total_pixels
        
        fileout.write('     total valid data {} which represent {:5.2f} %\n'.format(valid_data,valid_data_ratio*100))
            
        if valid_data_ratio < valid_data_threshold:
            fileout.write('     valid data percentage is {:5.2f} which is less than the threshold {:5.2f}% \n'.format(valid_data_ratio*100,valid_data_threshold*100))
            fileout.write('     image will be discarded\n')
            images_to_drop.append(images)
            continue
        
        else:
            images_to_keep.append(images)
            
            fileout.write('     valid data percentage is {:5.2f} which is more than the threshold {:5.2f}% \n'.format(valid_data_ratio*100,valid_data_threshold*100))
            fileout.write('     image will be normalized \n')
            
            # Compute metrics for each band
            fileout.write('     computing image metrics \n')
            
            band_04_metric1 = compute_metrics(band_04)
            min4_1,max4_1,mean4_1,std_div4_1,Q14_1,Q34_1,IQR4_1,com_max4_1,percentile14_1,percentile994_1 = band_04_metric1  

            band_03_metric1 = compute_metrics(band_03)
            min3_1,max3_1,mean3_1,std_div3_1,Q13_1,Q33_1,IQR3_1,com_max3_1,percentile13_1,percentile993_1 = band_03_metric1     

            band_02_metric1 = compute_metrics(band_02)
            min2_1,max2_1,mean2_1,std_div2_1,Q12_1,Q32_1,IQR2_1,com_max2_1,percentile12_1,percentile992_1 = band_02_metric1    

            range_global04 = percentile994_1 - percentile14_1
            range_global03 = percentile993_1 - percentile13_1
            range_global02 = percentile992_1 - percentile12_1
            
            range_global = max(range_global04,range_global03,range_global02)
            
            fileout.write('     normalizing band 04 \n')
            band_04_norm_npy,band_04_norm_png  = normalize_global(band_04,band_04_metric1,range_global,norm_opt)
            band_04_norm_npy = np.squeeze(band_04_norm_npy,axis=0)
            band_04_norm_png = np.squeeze(band_04_norm_png,axis=0)

            fileout.write('     normalizing band 03 \n')
            band_03_norm_npy,band_03_norm_png  = normalize_global(band_03,band_03_metric1,range_global,norm_opt)
            band_03_norm_npy = np.squeeze(band_03_norm_npy,axis=0)
            band_03_norm_png = np.squeeze(band_03_norm_png,axis=0)
            
            fileout.write('     normalizing band 02 \n')
            band_02_norm_npy,band_02_norm_png  = normalize_global(band_02,band_02_metric1,range_global,norm_opt)
            band_02_norm_npy = np.squeeze(band_02_norm_npy,axis=0)
            band_02_norm_png = np.squeeze(band_02_norm_png,axis=0)

            RGB_npy = np.stack([band_04_norm_npy,band_03_norm_npy,band_02_norm_npy],axis=2)            
            RGB_png = np.stack([band_04_norm_png,band_03_norm_png,band_02_norm_png],axis=2)
            
            RGB_org_png = Image.fromarray(RGB_png)
            
            # save normalized as png 
            fileout.write('     saving normalized image as png file \n')
            RGB_org_png.save('figures/images_png/{}_10m.png'.format(images))
            
            fileout.write('     saving normalized image as npy file \n')
            np.save('images_npy/{}_10m.npy'.format(images),RGB_npy)

fileout.close()
