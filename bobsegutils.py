from __future__ import print_function

import time
import copy
import math
import numpy as np
from skimage.filters import gaussian
import cv2 

import matplotlib.pyplot as plt
import pylab as pl

from tifffile import imread, imsave
import pickle

from netsurface2d import NetSurf2d
from netsurface2dt import NetSurf2dt
from data3d import Data3d

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from scipy.interpolate import griddata

from scipy.stats.stats import pearsonr
from scipy.stats.stats import kendalltau

from shapely import geometry

import bresenham as bham



def compute_flow( flowchannel ):
    '''Computes the Farnaback dense flow for the given moview
    '''
    flows = []
    prvs = flowchannel[0]
    for f in range(flowchannel.shape[0]):
        nxt = flowchannel[f]
#         flow = cv2.calcOpticalFlowFarneback(prev=prvs,
#                                             next=nxt,
#                                             flow=None,
#                                             pyr_scale=0.5,
#                                             levels=3,
#                                             winsize=5,
#                                             iterations=15,
#                                             poly_n=5,
#                                             poly_sigma=1.5,
#                                             flags=1)
        flow = cv2.calcOpticalFlowFarneback(prev=prvs,
                                            next=nxt,
                                            flow=None,
                                            pyr_scale=0.5, 
                                            levels=1,
                                            winsize=10,
                                            iterations=2,
                                            poly_n=5, 
                                            poly_sigma=1.1, 
                                            flags=0)
        flows.append(flow)
        prvs = nxt
        print ('.', end="")
    print (' ...done!')
    return flows

def split_flow_components( flows ):
    ''' Receives flow results as computed by 'compute_flow' and returns 
        a tupel of x and y components of this flow results.
    '''
    flow_x = np.moveaxis(np.swapaxes(flows,0,3)[0],-1,0)
    flow_y = np.moveaxis(np.swapaxes(flows,0,3)[1],-1,0)
    return flow_x, flow_y

def flow_sum(flow_comp, interval):
    ''' This function computes the sum over a specified time interval 
        of the given flow component (as returned by 'split_flow_components'). 
        For example, if the time interval is 5, it computes the average over 
        a window of +5 and -5 for times where this window exists. 
        For times where one of the window isn't fully available, only the 
        availabe sub-window is used instead.
    '''
    sum_flow = np.zeros_like(flow_comp)
    
    limit = len(flow_comp) - interval
    for i in range(len(flow_comp)):
        if (i < interval):
            sum_flow[i] = np.sum(flow_comp[:i+interval+1], axis=0)
        elif (i > limit):
            sum_flow[i] = np.sum(flow_comp[i-interval:], axis=0)
        else:
            sum_flow[i] = np.sum(flow_comp[i-interval:i+interval+1], axis=0)
    return sum_flow

def flow_average(flow_comp, interval):
    ''' This function computes the average over a specified time interval 
        of the given flow component (as returned by 'split_flow_components'). 
        For example, if the time interval is 5, it computes the average over 
        a window of +5 and -5 for times where this window exists. 
        For times where one of the window isn't fully available, only the 
        availabe sub-window is used instead.
    '''
    avg_flow = np.zeros_like(flow_comp)
    
    limit = len(flow_comp) - interval
    for i in range(len(flow_comp)):
        if (i < interval):
            avg_flow[i] = np.average(flow_comp[:i+interval+1], axis=0)
        elif (i > limit):
            avg_flow[i] = np.average(flow_comp[i-interval:], axis=0)
        else:
            avg_flow[i] = np.average(flow_comp[i-interval:i+interval+1], axis=0)
    return avg_flow

def flow_merge_frames(flow_comp, count):
    ''' This function computes the average over junks of 'count' many 
        frames and hence returns len(flow_comp)/count many merged (averaged)
        frames.
    '''
    assert len(flow_comp)%count == 0
    
    newshape = flow_comp.shape
    newshape = (len(flow_comp)/count, newshape[1], newshape[2])
    merged_flow_frames = np.zeros(newshape)
    
    for i in range(newshape[0]):
        merged_flow_frames[i] = np.sum(flow_comp[i*count:(i+1)*count], axis=0)
    return merged_flow_frames

def get_projected_length(a, b):
    ''' Projects one vector onto another and returns the projected length.
        a - the vector to project, given as (x,y)-tuple.
        b - the vector to project onto, given as (x,y)-tuple.
    '''
    len_b = math.sqrt(b[0]**2+b[1]**2)
    return (a[0]*b[0] + a[1]*b[1])/len_b

def euclid_dist(x,y):
    '''Computes euclidean distance between two points 
    '''
    distance = ((y[0]-x[0])**2+(y[1]-x[1])**2)**.5
    return distance

def neighbors(curr_pos):
    '''Finds neighbors of the point 'curr_pos' in a 8-neighborhood grid. Each point is a neighbor of itself too.
    '''
    neighbor = [(curr_pos[0], curr_pos[1]), (curr_pos[0]-1, curr_pos[1]), (curr_pos[0], curr_pos[1]-1), (curr_pos[0]+1, curr_pos[1]), (curr_pos[0], curr_pos[1]+1), (curr_pos[0]-1, curr_pos[1]+1), (curr_pos[0]+1, curr_pos[1]+1),(curr_pos[0]-1, curr_pos[1]-1), (curr_pos[0]+1, curr_pos[1]-1)]
    return neighbor

def pixel_pos(neighbor, neigh_flow_x, neigh_flow_y, sub_pix_pos):
    '''Finds interpolated flows at possibly sub-pixel loactions
    '''
    evaluate_at = (sub_pix_pos)
    result_x = griddata(neighbor, neigh_flow_x, evaluate_at, method = 'cubic')
    result_y = griddata(neighbor, neigh_flow_y, evaluate_at, method = 'cubic')
    
    return result_x, result_y

def neighbor_flow(neighbor,f, avg_flow_x, avg_flow_y):
    '''Finds the flow at neighbors
    '''
    l = len(neighbor)
    neigh_flow_x = [None]*l
    neigh_flow_y = [None]*l
    for i in range(l):
        neigh_flow_x[i] = avg_flow_x[f,neighbor[i][1], neighbor[i][0]]
        neigh_flow_y[i] = avg_flow_y[f,neighbor[i][1], neighbor[i][0]]
    return neigh_flow_x, neigh_flow_y

def update_pos(img_myo, f, avg_flow_x, avg_flow_y):
    '''Returns updated position after interpolation
    '''
    grid_x = int(img_myo[0])
    grid_y = int(img_myo[1])
    neighbor = neighbors((grid_x,grid_y))
    neigh_flow_x, neigh_flow_y = neighbor_flow(neighbor,f, avg_flow_x, avg_flow_y)
    result_x, result_y = pixel_pos(neighbor, neigh_flow_x, neigh_flow_y, img_myo)
    new_pos_x = img_myo[0]+result_x
    new_pos_y = img_myo[1]+result_y
    seed_img_myo=(new_pos_x, new_pos_y)
    
    return seed_img_myo