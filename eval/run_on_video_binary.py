# Code to produce colored segmentation output in Pytorch for all cityscapes subsets
# Sept 2017
# Eduardo Romera
#######################

import numpy as np
import torch
import os
import importlib

from PIL import Image
from argparse import ArgumentParser

from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision.transforms import Compose, CenterCrop, Normalize, Resize
from torchvision.transforms import ToTensor, ToPILImage

from dataset import cityscapes
from erfnet import ERFNet
from transform import Relabel, ToLabel, Colorize_binary

import visdom

import numpy as np
import cv2
from torchvision import transforms
from PIL import Image
from matplotlib import pyplot as plt

NUM_CHANNELS = 3
NUM_CLASSES = 20

trans = transforms.ToTensor()

image_transform = ToPILImage()
input_transform_cityscapes = Compose([
    Resize((512,1024),Image.BILINEAR),
    ToTensor(),
    #Normalize([.485, .456, .406], [.229, .224, .225]),
])
target_transform_cityscapes = Compose([
    Resize((512,1024),Image.NEAREST),
    ToLabel(),
    Relabel(255, 19),   #ignore label to 19
])

cityscapes_trainIds2labelIds = Compose([
    Relabel(19, 255),
    Relabel(18, 33),
    Relabel(17, 32),
    Relabel(16, 31),
    Relabel(15, 28),
    Relabel(14, 27),
    Relabel(13, 26),
    Relabel(12, 25),
    Relabel(11, 24),
    Relabel(10, 23),
    Relabel(9, 22),
    Relabel(8, 21),
    Relabel(7, 20),
    Relabel(6, 19),
    Relabel(5, 17),
    Relabel(4, 13),
    Relabel(3, 12),
    Relabel(2, 11),
    Relabel(1, 8),
    Relabel(0, 7),
    Relabel(255, 0),
    ToPILImage(),
])

def main(args):

    modelpath = args.loadDir + args.loadModel
    weightspath = args.loadDir + args.loadWeights

    print ("Loading model: " + modelpath)
    print ("Loading weights: " + weightspath)

    #Import ERFNet model from the folder
    #Net = importlib.import_module(modelpath.replace("/", "."), "ERFNet")
    model = ERFNet(NUM_CLASSES)

    model = torch.nn.DataParallel(model)
    # if (not args.cpu):
    #     model = model.cuda()

    #model.load_state_dict(torch.load(args.state))
    #model.load_state_dict(torch.load(weightspath)) #not working if missing key

    fourcc = cv2.VideoWriter_fourcc(*'MP4V') # Save as video
    out = cv2.VideoWriter('output.mp4', fourcc, 20.0, (640,352))

    def load_my_state_dict(model, state_dict):  #custom function to load model when not all dict elements
        own_state = model.state_dict()
        for name, param in state_dict.items():
            if name not in own_state:
                 continue
            own_state[name].copy_(param)
        return model

    model = load_my_state_dict(model, torch.load(weightspath, map_location=torch.device('cpu')))
    print ("Model and weights LOADED successfully")

    model.eval()



    # loader = DataLoader(cityscapes(args.datadir, input_transform_cityscapes, target_transform_cityscapes, subset=args.subset),
    #     num_workers=args.num_workers, batch_size=args.batch_size, shuffle=False)

    # For visualizer:
    # must launch in other window "python3.6 -m visdom.server -port 8097"
    # and access localhost:8097 to see it
    # if (args.visualize):
    #     vis = visdom.Visdom()


    # for step, (images, labels, filename, filenameGt) in enumerate(loader):
    # cap = cv2.VideoCapture(0)
    cap = cv2.VideoCapture('project_video_trimmed.mp4')

    while(True):
        # Capture frame-by-frame
        ret, images = cap.read()
        # print(images.shape)

        images = trans(images)
        images = images.float()
        images = images.view((1, 3, 352, 640)) # vidoe


        # Our operations on the frame come here
        # if (not args.cpu):
        #     images = images.cuda()

        inputs = Variable(images)
        with torch.no_grad():
            outputs = model(inputs)


        label = outputs[0].max(0)[1].byte().cpu().data
        #label_cityscapes = cityscapes_trainIds2labelIds(label.unsqueeze(0))
        label_color = Colorize_binary()(label.unsqueeze(0))
        frame = label_color.numpy().transpose(1, 2, 0)

        # label_save = ToPILImage()(label_color)
        # label_save.save("result_1.png")

        # Display the resulting frame
        cv2.imshow('Segmented Image', frame)
        out.write(frame)  # To save video file

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()


    if (args.visualize):
        vis.image(label_color.numpy())
    print (step, filenameSave)



if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument('--state')

    parser.add_argument('--loadDir',default="../trained_models/")
    parser.add_argument('--loadWeights', default="erfnet_pretrained.pth")
    parser.add_argument('--loadModel', default="erfnet.py")
    parser.add_argument('--subset', default="val")  #can be val, test, train, demoSequence


    parser.add_argument('--num-workers', type=int, default=4)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--cpu', action='store_true')

    parser.add_argument('--visualize', action='store_true')
    main(parser.parse_args())
