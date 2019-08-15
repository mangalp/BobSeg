import numpy as np
import bresenham as bham
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from tifffile import imsave
import bobsegutils as bsu

def sample_circle( n=18 ):
    '''
        Returns n many points on the unit circle (equally spaced).
    '''
    points = np.zeros([n,2])
    for i in range(n):
        angle = 2*np.math.pi * i/float(n)
        x = np.math.cos(angle)
        y = np.math.sin(angle)
        # print angle, x, y
        points[i] = [x,y]
        
    return points


def get_coords(obj_id, tot_time, num_columns, query_centroids, col_vectors, min_radius, max_radius, label_images_per_frame, queried_labels, Ea_background_border, Ep_background_border, bg_label):
    
    '''
        Returns coordinates of points on the columns for the queried object
    '''
    sampled_surface_coords = {} # stores surface coordinates (values) for desired objects at different time (keys)
    common_boundary_column = {} # stores columns belonging to Ea-Ep boundary
    background_boundary_column = {} # stores columns belonging to background-Ea/Ep boundary
   
    for t in range(tot_time):
        surface_coords_per_time = []
        surface_coords_per_column = []
        common_boundary_column_per_frame = []
        background_boundary_column_per_frame = []
        
        for i in range(num_columns):
            from_x = int(query_centroids[obj_id][t][1] + col_vectors[i,0]*min_radius[obj_id][0])
            from_y = int(query_centroids[obj_id][t][0] + col_vectors[i,1]*min_radius[obj_id][1])
            to_x = int(query_centroids[obj_id][t][1] + col_vectors[i,0]*max_radius[obj_id][0])
            to_y = int(query_centroids[obj_id][t][0] + col_vectors[i,1]*max_radius[obj_id][1])
         
            coords_per_column = bham.bresenhamline(np.array([[from_x, from_y]]), np.array([[to_x, to_y]]))
            num_pixels = len(coords_per_column)
            coords_per_column = coords_per_column.tolist()
            coords_per_column = [tuple(l) for l in coords_per_column]
            interior_coords = []
            for pt in (coords_per_column):
                if(label_images_per_frame[t][pt[1]][pt[0]] == queried_labels[obj_id][t]):
                    interior_coords.append(pt)
            
            if(interior_coords == []):
                print('Empty!, please recenter the centroid of cell ',obj_id ,' at times t >=', t)
            surface_coords_per_column.append(interior_coords[-1])

            if(obj_id == 0): #Ea
                for point in (coords_per_column): #For Ea, computing the columns which are shared with Ep
                    if(label_images_per_frame[t][point[1]][point[0]] == queried_labels[1][t]):   
                        common_boundary_column_per_frame.append(i)
                        break
                        
                    else:
                        continue
                        
                if(Ea_background_border): #For Ea, computing the columns which are shared with background
                    for point in (coords_per_column):
                        if(label_images_per_frame[t][point[1]][point[0]] == bg_label):   
                            background_boundary_column_per_frame.append(i)
                            break
                        
                        else:
                            continue
                
            if(obj_id == 1): #Ep 
                for point in (coords_per_column): #For Ep, computing the columns which are shared with Ea
                    if(label_images_per_frame[t][pt[1]][pt[0]] == queried_labels[0][t]):
                        common_boundary_column_per_frame.append(i)
                        break
                        
                    else:
                        continue
                        
                if(Ep_background_border): #For Ep, computing the columns which are shared with background
                    for point in (coords_per_column):
                        if(label_images_per_frame[t][point[1]][point[0]] == bg_label):   
                            background_boundary_column_per_frame.append(i)
                            break
                        
                        else:
                            continue        
                
        sampled_surface_coords[t] = surface_coords_per_column
        common_boundary_column[t] = common_boundary_column_per_frame
        background_boundary_column[t] = background_boundary_column_per_frame
        
    return sampled_surface_coords, common_boundary_column, background_boundary_column


def shrink_polygone(coords, center, shrinkage_factor):
    
    ''' returns coordinates of shrunk polygone
        coords: list of tuples
        shrinkage_factor: between 0 and 1; 1 being no shrinkage
    '''
    xs = [i[0] for i in coords]
    ys = [i[1] for i in coords]
    x_center = center[1]
    y_center = center[0]
    # shrink figure
    new_xs = [(i - x_center) * shrinkage_factor + x_center for i in xs]
    new_ys = [(i - y_center) * shrinkage_factor + y_center for i in ys]
    # create list of new coordinates
    new_coords = zip(new_xs, new_ys)
    new_coords = list(new_coords)
    return new_coords

def get_polygone_points( obj, frame, sampled_coords, query_centroids, scaling_factor=1.0 ):
    """
    scaling_factor: scales the polygone by the given factor, 1.0 by default. 
    calibration: 2-tupel of pixel size multipliers
    """
    unscaled_surface_coords = sampled_coords[obj][frame]
    center = query_centroids[obj][frame]
    surface_coords = shrink_polygone(unscaled_surface_coords, center, scaling_factor)
    return surface_coords

def get_annulus_bresenham_lines(inner_polygone, outer_polygone):
    annulus_bresenham_lines = []
    for i in range(len(inner_polygone)):
        points = bham.bresenhamline( np.array([inner_polygone[i]]),np.array([outer_polygone[i]]) )
        annulus_bresenham_lines.append(points)
    return annulus_bresenham_lines

def post_avg_flow_filter(x_comp, y_comp, one_column_vector, pixel_to_micron, delta_t):
    effective_comp = bsu.get_projected_length([x_comp, y_comp],one_column_vector)
    effective_comp_micron = effective_comp*pixel_to_micron
    effective_vel = effective_comp_micron/delta_t
    return effective_vel


