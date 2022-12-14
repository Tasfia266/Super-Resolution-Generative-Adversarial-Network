# -*- coding: utf-8 -*-
"""srgan1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1EEJK9LRQp0259T4dX7f_Z1KYGexT3TA7
"""

import os 
import cv2 
import numpy as np 
import matplotlib.pyplot as plt 
from keras.models import Sequential 
from keras import layers, Model 
from sklearn.model_selection import train_test_split

from google.colab import drive 
drive.mount ('/content/drive')

from keras import Model 
from keras.layers import Conv2D, PReLU, BatchNormalization, Flatten 
from keras.layers import UpSampling2D, LeakyReLU, Dense, Input, add

# Residual blocks for building generator 
def res_block (ip): 
  res_model= Conv2D (64, (3,3), padding='same')(ip) 
  res_model= BatchNormalization (momentum=0.5) (res_model) 
  res_model= PReLU (shared_axes= [1,2]) (res_model) 

  res_model= Conv2D (64, (3,3), padding='same') (res_model) 
  res_model= BatchNormalization (momentum=0.5) (res_model) 
  return add ([ip, res_model])

def upscale_block (ip): 
  up_model= Conv2D (256, (3,3), padding='same') (ip) 
  up_model= UpSampling2D (size=2) (up_model) 
  up_model= PReLU (shared_axes=[1,2]) (up_model)
  return up_model

#generator model 
def create_gen (gen_ip, num_res_block): 
  layers= Conv2D (64, (9,9), padding='same')(gen_ip) 
  layers= PReLU (shared_axes= [1,2])(layers) 

  temp= layers 

  for i in range (num_res_block): 
    layers= res_block (layers) 

  layers= Conv2D (64, (3,3), padding='same')(layers) 
  layers= BatchNormalization (momentum=0.5) (layers) 
  layers= add([layers, temp]) 

  layers= upscale_block (layers) 
  layers= upscale_block (layers) 

  op= Conv2D (3, (9,9), padding= 'same') (layers) 
  return Model (inputs=gen_ip, outputs=op)

#descriminator block 
def descriminator_block (ip, filters, strides=1, bn=True): 
  disc_model= Conv2D (filters, (3,3), strides=strides, padding='same') (ip) 
  if bn: 
    disc_model= BatchNormalization (momentum=0.8) (disc_model) 
  disc_model= LeakyReLU (alpha=0.2)(disc_model) 
  
  return disc_model

#descriminator. binary classifier
def create_disc (disc_ip): 
  df=64 

  d1= descriminator_block (disc_ip, df, bn=False) 
  d2= descriminator_block (d1, df, strides=2) 
  d3= descriminator_block(d2, df*2) 
  d4= descriminator_block (d3, df*2, strides=2) 
  d5= descriminator_block (d4, df*4) 
  d6= descriminator_block (d5, df*4, strides=2) 
  d7= descriminator_block (d6, df*8) 
  d8= descriminator_block (d7, df*8, strides=2) 
  
  d8_5= Flatten () (d8) 
  d9= Dense (df*16) (d8_5) 
  d10= LeakyReLU (alpha=0.2)(d9)
  validity= Dense (1, activation='sigmoid')(d10)

  return Model (disc_ip, validity)

#VGG19 
#We need vgg19 for the feature map from convoultional layers. We will build a pre-trained vgg model to extract feature map at the third block of the model.

from tensorflow.keras.applications import VGG19

def build_vgg (hr_shape): 
  vgg= VGG19 (weights='imagenet', include_top=False, input_shape=hr_shape)
  return Model (inputs=vgg.inputs, outputs= vgg.layers[10].output)

def combined_model (gen_model, disc_model, vgg, lr_ip, hr_ip): 
  gen_img= gen_model (lr_ip) 
  gen_features= vgg (gen_img) 
  disc_model.trainable=False 
  validity= disc_model (gen_img) 
  return Model (inputs= [lr_ip, hr_ip], outputs= [validity, gen_features])

# There are two losses. 1. adversarial loss and 2. content loss (vgg loss). For adversarial, it is binary-crossentropy. And for content loss the 
# mean sqaured error between feature map representation from reconstructed image and reference image from VGG19.

lr_list= os.listdir ('/content/drive/MyDrive/Data/LR')

lr_images= [] 
for img in lr_list: 
  img_lr= cv2.imread ('/content/drive/MyDrive/Data/LR/'+ img) 
  img_lr= cv2.cvtColor (img_lr, cv2.COLOR_BGR2RGB) #opencv reads in BGR. we convert it in RGB for display purposes.
  lr_images.append (img_lr)

hr_list= os.listdir ('/content/drive/MyDrive/Data/HR')

hr_images=[] 
for img in hr_list: 
  img_hr= cv2.imread ('/content/drive/MyDrive/Data/HR/'+img) 
  img_hr= cv2.cvtColor (img_hr, cv2.COLOR_BGR2RGB)
  hr_images.append (img_hr)

lr_images= np.array (lr_images) 
hr_images= np.array (hr_images)

lr_images.shape, hr_images.shape

#view few images 
import random 
import numpy as np
img_number= random.randint (0, len (lr_images)-1) 
plt.figure (figsize= (12,6)) 
plt.subplot (121) 
plt.imshow(lr_images[img_number])
plt.subplot (122) 
plt.imshow (hr_images[img_number])
plt.show ()

#scale values 
lr_images= lr_images/255 
hr_images= hr_images/255

#split to train and test 
lr_train, lr_test, hr_train, hr_test= train_test_split (lr_images, hr_images, test_size=0.33, random_state=42)

hr_shape= (hr_train.shape[1], hr_train.shape[2], hr_train.shape[3]) 
lr_shape= (lr_train.shape[1], lr_train.shape[2], lr_train.shape[3])

lr_ip= Input(shape=lr_shape) 
hr_ip= Input (shape= hr_shape)

generator= create_gen (lr_ip, num_res_block=16)
generator.summary ()

discriminator= create_disc (hr_ip) 
discriminator.compile (loss= 'binary_crossentropy', optimizer= 'adam', metrics= ['accuracy']) 
discriminator.summary ()

vgg= build_vgg ((384, 384, 3)) 
vgg.summary ()

vgg.trainable= False 
gan_model= combined_model (generator, discriminator, vgg, lr_ip, hr_ip)
gan_model.compile (loss= ['binary_crossentropy', 'mse'], loss_weights= [1e-3,1], optimizer='adam')

gan_model.summary ()

#create a list of images of low resolution and high resolution in batches 
# A batch of images would be fatched during training

batch_size= 1 
train_lr_batches=[] 
train_hr_batches=[] 
for it in range (int (hr_train.shape[0]/batch_size)): 
  start_index= it*batch_size 
  end_index= start_index+ batch_size 
  train_hr_batches.append (hr_train[start_index:end_index]) 
  train_lr_batches.append (lr_train[start_index:end_index])

epochs=200
for i in range (epochs): 
  fake_label= np.zeros ((batch_size,1)) #assign 0 to all generated images
  real_label= np.ones ((batch_size,1)) #assign 1 to all real images 
  #create empty list to populate all generator and discriminator losses 
  g_losses=[] 
  d_losses=[] 
  for b in range (len (train_hr_batches)): 
    lr_images= train_lr_batches[b] 
    hr_images= train_hr_batches[b] 

    fake_images= generator. predict_on_batch (lr_images) 
    #train the discriminator on fake and real HR images 
    discriminator.trainable= True 
    d_loss_gen= discriminator.train_on_batch (fake_images, fake_label) 
    d_loss_real= discriminator.train_on_batch (hr_images, real_label) 

    #now train the generator 
    discriminator.trainable= False 
    #averaging the discriminator loss 
    d_loss= 0.5*np.add (d_loss_gen, d_loss_real) 
    #Extract Vgg features, to be used towards calculating loss 
    image_features= vgg.predict (hr_images) 
    #train the generator via gan. we have 2 losses. 1: adversarial loss 2: content loss 
    g_loss, _, _= gan_model.train_on_batch ([lr_images, hr_images], [real_label, image_features]) 
    #Save losses to a list 
    d_losses.append (d_loss) 
    g_losses.append (g_loss) 

  g_losses= np.array (g_losses) 
  d_losses= np.array (d_losses) 
  #Calculate average losses for generator and discriminator 
  g_loss= np.sum (g_losses, axis=0) / len (g_losses) 
  d_loss= np.sum (d_losses, axis=0) / len (d_losses) 

  #report the progress during training 
  print ('epoch:', i+1, 'g_loss', g_loss, 'd_loss', d_loss) 

  if (i+1)%100==0:
    generator.save ('gan_e'+str (i+1)+'.h5')
     #save the generator after 10 epochs

#Testing 
from keras.models import load_model 
from numpy.random import randint

generator= load_model ('/content/gan_e100.h5', compile= False)

[x1,x2]= [lr_test, hr_test]

#Select random exmaple 
ix= randint (0, len (x1), 1) 
src_image, tar_image= x1[ix], x2[ix]

#Generate images from source 
gen_image= generator.predict (src_image)

#plot all three images 
plt.figure (figsize= (16,8)) 
plt.subplot (231) 
plt.title ('Low resolution image') 
plt.imshow (src_image[0, :, :, :]) 
plt.subplot (232) 
plt.title ('Super Resolution') 
plt.imshow (gen_image[0, :, :, :]) 
plt.subplot (233) 
plt.title ('Original high resolution image') 
plt.imshow (tar_image[0, :, :, :])
plt.show ()

