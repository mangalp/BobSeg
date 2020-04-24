import cv2
import numpy as np
import matplotlib.pyplot as plt

from skimage.feature import peak_local_max

from scipy.ndimage.filters import gaussian_filter
from scipy.ndimage import median_filter


from scipy.spatial import distance_matrix
from interpolation_methods import *
from scipy.signal import convolve2d


def localmax_TM( flow_channel,w_med=3,sig_gau=0.5,min_dist=3,ws=9,wl=19,korel_tresh=0):
    
     flows = []
    for i in range(len(flow_channel.shape[0])):
    
        I1=flow_channel[i]
        I2=flow_channel[i+1]


        I1=median_filter(I1,w_med)
        I1=gaussian_filter(I1,sig_gau)
        I2=median_filter(I2,w_med)
        I2=gaussian_filter(I2,sig_gau)

        I_peaks=I1.copy()
        I_peaks[I_peaks<0.02]=0.02


        cents=peak_local_max(I_peaks, min_distance=min_dist)
        num_p=np.shape(cents)[0]


        result1x=[]
        result1y=[]
        result2x=[]
        result2y=[]

        wsr=int(np.round((ws-1)/2))
        wlr=int(np.round((wl-1)/2))

        for i in range(num_p):
            posx=int(np.round(cents[i,0]))
            posy=int(np.round(cents[i,1]))

            ###do not use border points
            if posx-wlr<0 or posx+wlr+1>=np.shape(I1)[0] or posy-wlr<0 or posy+wlr+1>=np.shape(I1)[1]:
                continue


            window_s=I1[posx-wsr:posx+wsr+1,posy-wsr:posy+wsr+1]
            window_l=I2[posx-wlr:posx+wlr+1,posy-wlr:posy+wlr+1]

            window_s=np.rot90(window_s,2)-np.mean(window_s)
            signal=convolve2d(window_l, window_s, mode='same')


            ###remove borders
            signal[:wsr,:]=0
            signal[-wsr:,:]=0
            signal[:,:wsr]=0
            signal[:,-wsr:]=0

            if signal.max()>korel_tresh:
                ind=np.argwhere(signal.max() == signal)
                x_tmp=ind[0,0]+posx-wlr
                y_tmp=ind[0,1]+posy-wlr

                result1x.append([posx])
                result1y.append([posy])
                result2x.append([x_tmp])
                result2y.append([y_tmp])

        result1x=np.array(result1x)
        result1y=np.array(result1y)
        result2x=np.array(result2x)
        result2y=np.array(result2y)

        pos_s=np.stack((result1y,result1x),axis=1)[:,:,0]
        pos_t=np.stack((result2y,result2x),axis=1)[:,:,0]


        flow=kNN_interpolated_flow( flow_channel,pos_s,pos_t)
        #     flow=guided_hornshunk_flow( flow_channel,pos_s,pos_t)

        I1=I1*6
        I1[I1>1]=1
#         plt.figure()
#         plt.imshow(I1)
#         plt.plot(result1y,result1x,'r.')
        #     a=fydsfhysdfghgd
    
        flows.append(np.transpose(flow))
        print ('.', end="")
    print (' ...done!')
    return flows