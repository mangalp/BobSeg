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

from shapely import geometry
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from descartes.patch import PolygonPatch

from scipy.interpolate import griddata

from scipy.stats.stats import pearsonr
from scipy.stats.stats import kendalltau

import bresenham as bham
# from pyflow import pyflow



def compute_flow( flowchannel ):
    '''Computes the Farnaback dense flow for the given moview
    '''
    flows = []
    prvs = flowchannel[0]
    
   
    for f in range(flowchannel.shape[0]-1):
        nxt = flowchannel[f+1]
    
#         flow = cv2.calcOpticalFlowFarneback(prev=prvs,
#                                             next=nxt,
#                                             flow=None,
#                                             pyr_scale=0.5, 
#                                             levels=1,
#                                             winsize=5, #15?
#                                             iterations=2,
#                                             poly_n=5, 
#                                             poly_sigma=1.1, 
#                                             flags=0)
        
        flow = cv2.calcOpticalFlowFarneback(prev=prvs,
                                            next=nxt,
                                            flow=None,
                                            pyr_scale=0.5, 
                                            levels=2,
                                            winsize=7, #15?
                                            iterations=1,
                                            poly_n=3, 
                                            poly_sigma=1.4, 
                                            flags=0)
      
        flows.append(flow)
        prvs = nxt
        print ('.', end="")
    print (' ...done!')
    return flows

def compute_TVLflow( flowchannel ):
    '''Computes the DualTVL1 dense flow for the given moview
    '''
    flows = []
    previous = flowchannel[0]
    prvs = previous.astype(np.float32)
   
    for f in range(flowchannel.shape[0]):
        neext = flowchannel[f]
        nxt = neext.astype(np.float32)
        
        optical_flow = cv2.createOptFlow_DualTVL1()
        
        #optical_flow.setuseInitialFlow(True)
        flow = optical_flow.calc(prvs, nxt, None)
      
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
    newshape = (int(len(flow_comp)/count), newshape[1], newshape[2])
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

def sanity_check_loaded_data(figsize, memchannel, flowchannel, segchannel):
    pl.rcParams['figure.figsize'] = figsize
    fig = plt.figure()
    fig.suptitle('image channels and gradientimage for t=0 and t=-1', fontsize=16)
    ax = fig.add_subplot(231)
    ax.imshow(memchannel[0], plt.get_cmap('gray'))
    ax = fig.add_subplot(232)
    ax.imshow(flowchannel[0], plt.get_cmap('gray'))
    ax = fig.add_subplot(233)
    ax.imshow(segchannel[0], plt.get_cmap('gray'))
    ax = fig.add_subplot(234)
    ax.imshow(memchannel[-1], plt.get_cmap('gray'))
    ax = fig.add_subplot(235)
    ax.imshow(flowchannel[-1], plt.get_cmap('gray'))
    ax = fig.add_subplot(236)
    ax.imshow(segchannel[-1], plt.get_cmap('gray'))
    fig.tight_layout()
    return fig
    
def sanity_check_segmentation( figsize, data, memchannel, segchannel, sample_size=5 ):
    pl.rcParams['figure.figsize'] = figsize
    figs=[]
    for frame in range(1,len(data.images),int(len(data.images)/sample_size)):
        fig = plt.figure()
        ax = plt.subplot(131)
        data.plot_minmax( frame, ax, memchannel )
        ax = plt.subplot(132)
        ax.set_title('independent')
        data.plot_result( frame, ax, segchannel )    
        ax = plt.subplot(133)
        ax.set_title('2dt')
        data.plot_2dt_result( frame, ax, segchannel )
        fig.tight_layout()
        figs.append(fig)
    return figs
        
def sanity_check_flow(figsize, somechannel, flow_x, flow_y):
    pl.rcParams['figure.figsize'] = figsize
    fig = plt.figure()
    
    total_avg_flow_x = np.average(flow_x, axis=0)
    total_avg_flow_y = np.average(flow_y, axis=0)

    y,x = np.mgrid[0:somechannel.shape[1]:1, 0:somechannel.shape[2]:1]
    skip = (slice(None, None, 10), slice(None, None, 10))

    ax = plt.subplot(221)
    ax.set_title('average flow')
    ax.imshow(somechannel[int(len(somechannel)/2)])#, plt.get_cmap('gray'))
    ax.quiver(x[skip],y[skip],total_avg_flow_x[skip],-total_avg_flow_y[skip], color='w', scale=np.max(somechannel.shape)/8.)

    ax = plt.subplot(222)
    ax.set_title('first frame')
    ax.imshow(somechannel[0])#, plt.get_cmap('gray'))
    ax.quiver(x[skip],y[skip],flow_x[0][skip],-flow_y[0][skip], color='w', scale=np.max(somechannel.shape)/2.)

    ax = plt.subplot(223)
    ax.set_title('middlemost frame')
    ax.imshow(somechannel[int(len(somechannel)/2)])#, plt.get_cmap('gray'))
    ax.quiver(x[skip],y[skip],flow_x[int(len(somechannel)/2)][skip],-flow_y[int(len(somechannel)/2)][skip], color='w', scale=np.max(somechannel.shape)/2.)

    ax = plt.subplot(224)
    ax.set_title('last frame')
    ax.imshow(somechannel[-1])#, plt.get_cmap('gray'))
    ax.quiver(x[skip],y[skip],flow_x[-1][skip],-flow_y[-1][skip], color='w', scale=np.max(somechannel.shape)/2.)

    fig.tight_layout()
    #fig.savefig('test.pdf',dpi=300)
    return fig

def plot_coords(ax, poly, c, style='.-', alpha=.5):
    x, y = poly.xy
    ax.plot(x, y, style, color=c, alpha=alpha, zorder=1)
    
def plot_big_analysis(figsize,
                      objects,
                      data,
                      somechannel,
                      correlation_per_frame_per_object, 
                      slippage_per_frame_per_object, 
                      avg_membrane_contraction_per_frame_per_object, 
                      avg_center_flow_per_frame_per_object,
                      membrane_polygones_per_object,
                      membrane_movement_vectors_per_frame_per_object,
                      projected_mem_vecs_per_frame_per_object,
                      projected_avg_flows_per_frame_per_object,
                      annulus_inner_polygones_per_object,
                      annulus_middle_polygones_per_object,
                      annulus_outer_polygones_per_object,
                      annulus_avg_flow_vectors_per_frame_per_object,
                      show_projected=False):
    figs = []
    offset = 0
    stepsize = 2
    column_vectors = data.netsurfs[0][0].col_vectors # they are normalized to length 1

    pl.rcParams['figure.figsize'] = figsize
    
    fig = plt.figure()
    ax = plt.subplot(121)
    ax.set_title(data.object_names[0])
    ax.set_xlabel('time')
    ax.set_ylabel('movement / slippage')
    ax.plot(np.zeros_like(correlation_per_frame_per_object[0]), color='lightgray')
    # ax.plot(correlation_per_frame_per_object[0], color='gray', label='pearson r')
    ax.plot(slippage_per_frame_per_object[0], color='gray', label='slippage')
    ax.plot(avg_membrane_contraction_per_frame_per_object[0], color='#%02x%02x%02x'%(0,109,219), label='avg. mem')
    ax.plot(avg_center_flow_per_frame_per_object[0], color='#%02x%02x%02x'%(219,209,0), label='avg. flow')
    ax.legend( loc='lower right')
    ax = plt.subplot(122)
    ax.set_title(data.object_names[1])
    ax.set_xlabel('time')
    ax.set_ylabel('movement / slippage')
    ax.plot(np.zeros_like(correlation_per_frame_per_object[1]), color='lightgray')
    # ax.plot(correlation_per_frame_per_object[1], color='gray', label='pearson r')
    ax.plot(slippage_per_frame_per_object[1], color='gray', label='slippage')
    ax.plot(avg_membrane_contraction_per_frame_per_object[1], color='#%02x%02x%02x'%(0,109,219), label='avg. mem')
    ax.plot(avg_center_flow_per_frame_per_object[1], color='#%02x%02x%02x'%(219,209,0), label='avg. flow')
    ax.legend( loc='lower right')
    fig.tight_layout()
    figs.append(fig)

    for t in range(0,len(somechannel)-1,1):
        fig = plt.figure()
        ax = plt.subplot2grid((1, 3), (0, 0), colspan=2)
        ax2 = plt.subplot(233)
        ax3 = plt.subplot(236)

        ax.imshow(somechannel[t], plt.get_cmap('gray'))
        ax.text(25, 25, 't=%d'%t, fontsize=14, color='w')

        for obj in objects:
            # center points
            ax.plot(data.object_seedpoints[obj][t+1][0],data.object_seedpoints[obj][t+1][1], 'o', color='green')
            ax.plot(data.object_seedpoints[obj][t][0],data.object_seedpoints[obj][t][1], 'o', color='#%02x%02x%02x'%(0,109,219))

            # polygones (membrane and annulus)
            poly_membrane = geometry.Polygon(membrane_polygones_per_object[obj][t])
            poly_membrane_t2 = geometry.Polygon(membrane_polygones_per_object[obj][t+1])
            poly_annulus = geometry.Polygon(annulus_outer_polygones_per_object[obj][t], [annulus_inner_polygones_per_object[obj][t][::-1]])
            poly_annulus_middle = geometry.Polygon(annulus_middle_polygones_per_object[obj][t])

            plot_coords( ax, poly_membrane_t2.exterior, 'green', alpha=.5 )
            plot_coords( ax, poly_membrane.exterior, '#%02x%02x%02x'%(0,109,219) )

            patch_annulus = PolygonPatch(poly_annulus, facecolor='#%02x%02x%02x'%(219,209,0), edgecolor='orange', alpha=0.0625, zorder=2)
            ax.add_patch(patch_annulus)

            # membrane quivers
            mem_base_x = [p[0] for p in membrane_polygones_per_object[obj][t]]
            mem_base_y = [p[1] for p in membrane_polygones_per_object[obj][t]]
            if (show_projected):
                mem_vec = [column_vectors[i]*projected_mem_vecs_per_frame_per_object[obj][t][i] for i in range(len(column_vectors))]
                mem_vec_x = [v[0] for v in mem_vec]
                mem_vec_y = [-v[1] for v in mem_vec]
            else:
                mem_vec_x = [v[0] for v in membrane_movement_vectors_per_frame_per_object[obj][t]]
                mem_vec_y = [-v[1] for v in membrane_movement_vectors_per_frame_per_object[obj][t]]
            ax.quiver(mem_base_x, 
                      mem_base_y, 
                      mem_vec_x, 
                      mem_vec_y, 
                      width=0.0022, scale=np.max(somechannel.shape)/2., color='blue')

            # flow quivers
            flow_base_x = [p[0] for p in annulus_middle_polygones_per_object[obj][t]]
            flow_base_y = [p[1] for p in annulus_middle_polygones_per_object[obj][t]]
            if (show_projected):
                flow_vec = [column_vectors[i]*projected_avg_flows_per_frame_per_object[obj][t][i] for i in range(len(column_vectors))]
                flow_vec_x = [v[0] for v in flow_vec]
                flow_vec_y = [-v[1] for v in flow_vec]
            else:
                flow_vec_x = [v[0] for v in annulus_avg_flow_vectors_per_frame_per_object[obj][t]]
                flow_vec_y = [-v[1] for v in annulus_avg_flow_vectors_per_frame_per_object[obj][t]]
            ax.quiver(flow_base_x[offset::stepsize], 
                      flow_base_y[offset::stepsize], 
                      flow_vec_x[offset::stepsize], 
                      flow_vec_y[offset::stepsize], 
                      pivot='mid', width=0.0022, scale=np.max(somechannel.shape)/2., color='yellow')

        # LINEPLOT
        # ========
        ax2.set_title('Pearson r=%.5f'%correlation_per_frame_per_object[0][t])
        ax2.set_xlabel('segment')
        ax2.set_ylabel('movement')
        ax2.plot(np.zeros_like(projected_mem_vecs_per_frame_per_object[0][t]), color='lightgray')
        ax2.plot(projected_mem_vecs_per_frame_per_object[0][t], color='#%02x%02x%02x'%(0,109,219))
        ax2.plot(projected_avg_flows_per_frame_per_object[0][t], color='#%02x%02x%02x'%(219,209,0))

        ax3.set_title('Pearson r=%.5f'%correlation_per_frame_per_object[1][t])
        ax3.set_xlabel('segment')
        ax3.set_ylabel('movement')
        ax3.plot(np.zeros_like(projected_mem_vecs_per_frame_per_object[1][t]), color='lightgray')
        ax3.plot(projected_mem_vecs_per_frame_per_object[1][t], color='#%02x%02x%02x'%(0,109,219))
        ax3.plot(projected_avg_flows_per_frame_per_object[1][t], color='#%02x%02x%02x'%(219,209,0))

        fig.tight_layout()
        figs.append(fig)
    return figs

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

def subVector(vec1, vec2):
    """Makes a vector given two points using B-A given the coordinates of two points A and B
       Parameters: Two lists of vectors
       Returns a list
    """
    return [(vec2[0] - vec1[0], vec2[1] - vec1[1]) for vec1, vec2 in zip(vec1, vec2)] 

def unit_vector(vector):
    """ Returns the unit vector of the vector.  
    """
    return vector / np.linalg.norm(vector)
def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

def compute_coarse2fineFlow(flowchannel):
    '''Computes the Corse2Fine dense flow for the given movie
    '''
    flows = []
    previous = flowchannel[0]
    previous = previous[:, :, np.newaxis]
    prvs = previous.astype(np.double)
    
    alpha = 0.012
    ratio = 0.75
    minWidth = 20
    nOuterFPIterations = 7
    nInnerFPIterations = 1
    nSORIterations = 30
    colType = 1  # 0 or default:RGB, 1:GRAY (but pass gray image with shape (h,w,1))
    
    for f in range(flowchannel.shape[0]):
        neext = flowchannel[f]
        neext = neext[:,:,np.newaxis]
        nxt = neext.astype(np.double)
        
        # Flow Options:


        s = time.time()
        u, v, im2W = pyflow.coarse2fine_flow(
        prvs, nxt, alpha, ratio, minWidth, nOuterFPIterations, nInnerFPIterations,
        nSORIterations, colType)
        e = time.time()
        print('Time Taken: %.2f seconds for image of size (%d, %d, %d)' % (
    e - s, prvs.shape[0], prvs.shape[1], prvs.shape[2]))
        flow = np.concatenate((u[..., None], v[..., None]), axis=2)
#         np.save('examples/outFlow.npy', flow)

        flows.append(flow)
        prvs = nxt
        print ('.', end="")
    print (' ...done!')
    return flows


    
