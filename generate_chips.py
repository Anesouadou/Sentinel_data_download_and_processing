import os
import sys
import numpy as np
import time
import copy
from PIL import Image
import matplotlib.pyplot as plt

import argparse

#######################  DEFINE ARGUMENTS ########################################################

parser = argparse.ArgumentParser()

parser.add_argument('--csize','-s',
                    help = 'dimension of the chips to be generated, the size is ssumed to be square',
                    metavar='',
                    type=int,
                    default=256,
                    required = True)
 
parser.add_argument('--cratio','-r',
                    help = 'the overlap ratio between two consecutive chips',
                    metavar='',
                    type=float,
                    default=0.25,
                    required = True)
                    
parser.add_argument('--log',
                    help = 'text file that stores the status of each image',
                    default = 'generate_chips.log')         

args = parser.parse_args()

#####################    GET ARGUMENTS   ######################################################

chip_size         = args.csize 
chip_overlap_rate = args.cratio

fileout = open(args.log,'w')



chip_overlap = round(chip_size*chip_overlap_rate)
chip_range   = chip_size - chip_overlap

top = int(0.9*(chip_size*chip_size))
bottom = int(0.05*(chip_size*chip_size))

folder_img_npy  =  'images_npy'
folder_lab_npy  =  'labels_npy'
folder_img_tci  =  'TCI_npy'


# Create necessary folders
print('####### Create necessary folders #############')

if os.path.isdir('chips_images'): # save chips generated from normalized images 
    print('folder already exists')
else:
    os.mkdir('chips_images')

if os.path.isdir('chips_labels'): # save chips generated from normalized labels
    print('folder already exists')
else:
    os.mkdir('chips_labels')

if os.path.isdir('chips_tcis'): # save chips generated from normalized labels
    print('folder already exists')
else:
    os.mkdir('chips_tcis')
    
if os.path.isdir('figures'): # this folder most probably exists but just in case
    print('folder already exists')
else:
    os.mkdir('figures')

if os.path.isdir('figures/chips'): # folder to hold all chips sub-folders 
    print('folder already exists')
else:
    os.mkdir('figures/chips')

if os.path.isdir('figures/chips/images'): # chips from input normalized image
    print('folder already exists')
else:
    os.mkdir('figures/chips/images')

if os.path.isdir('figures/chips/labels'): # chips from label array
    print('folder already exists')
else:
    os.mkdir('figures/chips/labels')

if os.path.isdir('figures/chips/tci'): # chips from tci image 
    print('folder already exists')
else:
    os.mkdir('figures/chips/tci')

if os.path.isdir('figures/chips/images_labels'): # chips from tci image 
    print('folder already exists')
else:
    os.mkdir('figures/chips/images_labels')

if os.path.isdir('figures/chips/tci_labels'): # chips from tci image 
    print('folder already exists')
else:
    os.mkdir('figures/chips/tci_labels')


label_list = os.listdir(folder_lab_npy)
label_list = list(map(str.strip,label_list))

for label_name in list(label_list):
    
    elem       = label_name.split('_')

    name       = elem[0]+"_"+elem[1]+"_"+elem[2]+"_"+elem[3]+"_"+elem[4]+"_"+elem[5]+"_"+elem[6]
    
    image_name = folder_img_npy+'/'+name+"_10m.npy"
    TCI_name   = folder_img_tci+'/'+name+"_TCI.npy"
    label_name = folder_lab_npy+'/'+label_name
    
    fileout.write('image file name: {}'.format(image_name))
    fileout.write('label file name: {}'.format(label_name))
    fileout.write('tci file name: {}'.format(TCI_name))

    image = np.load(image_name)
    tci   = np.load(TCI_name)
    label = np.load(label_name)
    
    dims = label.shape
    
    row_len = dims[0]
    col_len = dims[1]

    #print('dimensions {}'.format(dims))
    row_min = 0
    row_max = 0
    row_idx = 0
    index   = 0

    while row_max < row_len:
        col_min = 0
        col_max = 0
        col_idx = 0

        row_min = row_idx * chip_range
        row_max = row_min + chip_size

        if row_max > row_len:
            row_max = copy.copy(row_len)
            row_min = row_len - chip_size
        
        while col_max < col_len:
            
            col_min = col_idx * chip_range
            col_max = col_min + chip_size

            if col_max > col_len:
                col_max = copy.copy(col_len)
                col_min = col_len - chip_size

            chip_img = image[row_min:row_max,col_min:col_max,:]
            chip_img = chip_img.astype('float32')

            chip_lab = label[row_min:row_max,col_min:col_max]
            chip_lab = chip_lab.astype('float32')
            
            chip_TCI = tci[row_min:row_max,col_min:col_max,:]
            
            chip_sum = np.sum(chip_lab)

            if chip_sum > 0 and  chip_sum < top:
                if np.sum(chip_img) > 0:
                    # save chips as npy
                    np.save("chips_images/"+name+"_img_"+str(row_idx)+"_"+str(col_idx)+".npy",chip_img)
                    np.save("chips_labels/"+name+"_lab_"+str(row_idx)+"_"+str(col_idx)+".npy",chip_lab)           
                    np.save("chips_tcis/"+name+"_TCI_"+str(row_idx)+"_"+str(col_idx)+".npy",chip_TCI)

                    # save chips as png
                    im1 = Image.fromarray((chip_img*255).astype(np.uint8))
                    im1.save('figures/chips/images/'+name+"_img_"+str(row_idx)+"_"+str(col_idx)+'.png')

                    im2 = Image.fromarray((chip_lab*255).astype(np.uint8))
                    im2.save('figures/chips/labels/'+name+"_lab_"+str(row_idx)+"_"+str(col_idx)+'.png')
                    
                    #im3 = Image.fromarray((chip_TCI*255).astype(np.uint8))
                    im3 = Image.fromarray(chip_TCI)
                    im3.save('figures/chips/tci/'+name+"_TCI_"+str(row_idx)+"_"+str(col_idx)+'.png')

                    # overlay label on image chip
                    plt.figure(figsize = (25,25))
                    plt.imshow(chip_img)
                    plt.imshow(chip_lab,alpha=0.3)
                    plt.savefig('figures/images_labels/{}_R10m_label.png'.format(img))
                    plt.close()
                    
                    # overlay label on TCI chip
                    plt.figure(figsize = (25,25))
                    plt.imshow(chip_TCI)
                    plt.imshow(chip_lab,alpha=0.3)
                    plt.savefig('figures/tci_labels/{}_R10m_label.png'.format(img))
                    plt.close()
                    
            col_idx = col_idx + 1

        row_idx = row_idx + 1

fileout.close()
