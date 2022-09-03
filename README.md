# Super-Resolution-Generative-Adversarial-Network
The super resolution generative adversarial network converts low resolution images to high resolution image. The model consists of 2 blocks. 1. Discriminator and 2. Generator. The generator generates the high resolution images and the discriminator distinguishes between original high resolution images and generated images. ![generator_dis](https://user-images.githubusercontent.com/76652458/188276073-67470a6f-d406-4033-91ee-b816ea77c3ef.png)

For training, we can obtain the low resolution images by applying gaussian filter to high resolution images. One of the main contributions in super resolution gan is the perceptual 
loss function which typically consists of VGG based content loss and adversarial loss. VGG loss can be defined as the euclidean distance between feature representation of a 
constructed image and the feature map of reference images. And the adversarial loss is simply the binary-crossentropy loss. 

For training, first of all we have to download the dataset. Gan needs sufficient data and an extensive amount of time for training. Any banchmark dataset can be used. Here, for low resolution images, 
the image shape is 96x96x3 and for high resolution images, the image shape is 384x384x3. We have to resize the low and high resolution image and keep these in seperate directories. 
Then we have to load and scale the images in the range of [0,1].We can create a list of low and high resolution images in batches and a batch of images will be fatched during training. Here the model 
is trained on Google Colab with free GPU. Still, its better to have an external GPU for training the Gan model properly. 
# References 
1. https://medium.com/@ramyahrgowda/srgan-paper-explained-3d2d575d09ff
2. https://github.com/AnjanaGJoseph/Super-Resolution-GAN
