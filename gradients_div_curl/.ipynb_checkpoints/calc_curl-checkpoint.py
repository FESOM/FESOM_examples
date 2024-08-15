from pyfesom2 import load_mesh, tonodes
import os
import xarray as xr
import numpy as np
import shutil
import random
import string
import sys

from dask.distributed import Client
from dask import delayed, compute
import gc

##### define all the functions

def generate_random_string(length):
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits  # You can add more characters if needed
    # Use random.choices to generate a list of random characters
    random_characters = random.choices(characters, k=length)
    # Join the characters into a string
    random_string = ''.join(random_characters)
    return random_string

@delayed
def process_timestep(u_slice, v_slice, ddx, ddy, elems, mesh, output_file):
    # Compute the curl for the given timestep
    dv_dx = (ddx * v_slice[elems]).sum(dim='n3') #gradient-x on mesh
    du_dy = (ddy * u_slice[elems]).sum(dim='n3') #gradient-y on mesh
    curl = dv_dx - du_dy
    curl = tonodes(curl,mesh) #interpolate to nodes
    
    # Create a DataArray with the computed curl for this timestep
    curl_da = xr.DataArray(curl, dims=['nod2'], name='curl') 
    curl_da = curl_da.assign_coords(u_slice.coords)
    curl_da = curl_da.expand_dims('time') #add a time dimension (size 1), so that files can be loaded with open_mfdataset
    curl_da.to_netcdf(output_file)

def main():
    #inputs
    year=int(sys.argv[1]) #which year from input
    depth=float(sys.argv[2]) #which depth from input
    
    #paths
    mesh_path = '/path_to_mesh/'
    data_path = '/path_to_data/'
    out_path = '/path_for_output/'
    tmp_path = out_path+'tmp_'+str(year)+'/'
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    os.mkdir(tmp_path)
    #chunk size in time?
    time_chunk = 1
    #chunk size in space?
    nod2_chunk = 11538465


    #spawn a parallel cluster
    n_cores = 10
    mem_lim = str(int(100*np.floor(960/n_cores)))+'MB' #96GB total memory, set to MB (96000), divide by number of cores, then round to next 100
    dask_dir = '/some_temporary_path/'+generate_random_string(10)
    if os.path.exists(dask_dir):
        shutil.rmtree(dask_dir)
    if 'client' in locals() or 'client' in globals():
        client.close()
    client = Client(local_directory=dask_dir,n_workers=n_cores, threads_per_worker=1,memory_limit=mem_lim)
    client.amm.start()


    #fesom.mesh.diag.nc contains the dx/dy operators (basically just vectors of the same size as u/v)
    diag = xr.open_dataset((mesh_path+'fesom.mesh.diag.nc'))
    ddx = diag['gradient_sca_x'].astype('float32')
    ddy = diag['gradient_sca_y'].astype('float32')
    ###### for old FESOM2 versions 
    elems = (diag['elements']-1).T.astype('int')  #element indices are saved in Fortran format, starting from 1 instead of 0
    elems = elems[:, [0, 2, 1]] #element indices are in the wrong order from Fortran!!!!!!
    ###### for new FESOM2 versions
    # elems = (diag['elements']-1).astype('int')
    
    mesh = load_mesh(mesh_path)

    #load u/v data
    iz = np.argmin(np.abs(diag.nz1.values+depth)) #find the closest level in the model, depth in diag.nz1 is negative, that is why I use +depth
    unod = xr.open_dataset((data_path+'unod.fesom.' + str(year) + '.nc'),chunks={'time':time_chunk,'nod2':nod2_chunk})['unod'].astype('float32').isel(nz1=iz).drop_vars('nz1')
    vnod = xr.open_dataset((data_path+'vnod.fesom.' + str(year) + '.nc'),chunks={'time':time_chunk,'nod2':nod2_chunk})['vnod'].astype('float32').isel(nz1=iz).drop_vars('nz1')
    depth_used = abs(diag.nz1.values[iz])
    #persist arrays that are needed again
    delayed_tasks = []
    ddx = ddx.persist()
    ddy = ddy.persist()
    elems = elems.persist()


    #run delayed functions -> manual chunking in time still necessary, because dask is stupid and otherwise garbage piles up
    total_time_steps = len(unod.time)
    chunk_size = 10  # Adjust based on memory limits
    
    for chunk_start in range(0, total_time_steps, chunk_size):
        chunk_end = min(chunk_start + chunk_size, total_time_steps)
        delayed_tasks = []
        for ii in range(chunk_start, chunk_end):
            output_file = tmp_path+'curl_on_nodes_timestep_'+str(ii).zfill(3)+'.nc'
            u_slice = unod.isel(time=ii)
            v_slice = vnod.isel(time=ii)
            delayed_task = process_timestep(u_slice, v_slice, ddx, ddy, elems, mesh, output_file)
            delayed_tasks.append(delayed_task)
        
        # Compute results for the current chunk
        results = compute(*delayed_tasks)
        # Explicitly release memory
        del delayed_tasks, results, u_slice, v_slice
        gc.collect()

    #load files from the tmp-directory and make one big file
    curl_da = xr.open_mfdataset(tmp_path+'curl_on_nodes_timestep_*.nc',chunks={'time':time_chunk},parallel=True)['curl'].astype('float32')
    output_file = out_path+'/curl.fesom.'+str(year)+'_'+str(depth_used)+'m.nc'
    curl_da.to_netcdf(output_file)

    #delete the tmp-directory with all the temporary files
    shutil.rmtree(tmp_path)

    client.close()
        
if __name__ == '__main__':
    main()
