#!/usr/bin/env python
"""
create tilespecs from SBEMImage dataset
"""

import os
import renderapi
from rendermodules.module.render_module import StackOutputModule

from rendermodules.dataimport.schemas import (GenerateEMTileSpecsOutput,
                                              GenerateSerialEMTileSpecsParameters)

from rendermodules.utilities.EMBL_file_utils import groupsharepath

import mrcfile as mrc
import time
from multiprocessing import Pool
import numpy as np
import glob
import bdv_tools as bdv
import pyEM as em
from skimage import io
from rendermodules.utilities import uri_utils


example_input = {
    "render": {
        "host": "pc-emcf-16.embl.de",
        "port": 8080,
        "owner": "SBEM",
        "project": "tests",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/"
            "src/main/scripts")},
    "adocfile": "/g/emcf/Oorschot/EMBL_Projects/Ikmi-Soham-Nematostella #5898/Data_Jeol_Montages/#5898_L2738_U1a/L2738_12Kb2.mrc.mdoc",
    "stack": "test_resolution",
    "overwrite_zlayer": True,
    "pool_size": 4,
    "close_stack": True,
    "z_index": 1,
    "flatfield_thresh": 0.042,
    "output_stackVersion":{
        "stackResolutionX":10.1        
        }
}


class GenerateSerialEMImageTileSpecs(StackOutputModule):
    default_schema = GenerateSerialEMTileSpecsParameters
    default_output_schema = GenerateEMTileSpecsOutput


    def ts_from_SerialEMtile(self,imfile,idx,ni,pxs,tilepx,k,a_head):
        
        if not self.args.get('flatfield_correct'):
            if imfile[0]=='tif':
                outfile = imfile[1]+str(idx).zfill(ni)+'.tif'
            elif imfile[0]=='mrc':
                a = self.get_tile(idx, ni)
                outfile = self.write_converted_tile(a,ni)
        else:
            a = self.get_tile(idx, ni)
            outfile = self.write_corrected_tile(a,ni,k) 
            
        tileid = os.path.splitext(imfile[1])[0]+'_'+str(idx).zfill(ni)   
            
        f1 = os.path.realpath(outfile)

        filepath= groupsharepath(f1)        

        ip = renderapi.image_pyramid.ImagePyramid()
        ip[0] = renderapi.image_pyramid.MipMap(imageUrl='file://' + filepath)        

        tf_trans = renderapi.transform.AffineModel(
                                 B0=float(tilepx[idx][0]),
                                 B1=float(tilepx[idx][1]))  
        
 
    
        print("Processing tile "+tileid+" metadata for Render.")
        
        
        ts = renderapi.tilespec.TileSpec(
            tileId=tileid,
            imagePyramid=ip,
            z=0,#tile['glob_z'],
            width=int(a_head[0]),
            height=int(a_head[1]),
            minint=0, maxint=65535,
            tforms=[tf_trans],
            # imagePyramid=ip,
            sectionId=0,
            scopeId='SerialEM',
            cameraId='SerialEM',
            # imageCol=imgdata['img_meta']['raster_pos'][0],
            # imageRow=imgdata['img_meta']['raster_pos'][1],
            stageX = float(tilepx[idx][0]),
            stageY = float(tilepx[idx][1]),
            rotation = 0.0,
            pixelsize = pxs)

        # json_file = os.path.realpath(os.path.join(tilespecdir,outputProject+'_'+outputOwner+'_'+outputStack+'_%04d.json'%z))
        # fd=open(json_file, "w")
        # renderapi.utils.renderdump(tilespeclist,fd,sort_keys=True, indent=4, separators=(',', ': '))
        # fd.close()

        return f1,ts


    def ts_from_serialem (self,adocfile):
        
        imgdir,adocname=os.path.split(adocfile)
        
        os.chdir(imgdir)
        
        base = os.path.splitext(adocname)[0]     

        timestamp = time.localtime()
        if not os.path.exists('conv_log'):os.makedirs('conv_log')
        log_name = '_{}{:02d}{:02d}-{:02d}{:02d}'.format(timestamp.tm_year,timestamp.tm_mon,timestamp.tm_mday,timestamp.tm_hour,timestamp.tm_min)
        
        # mipmap_args = []
        # tilespecpaths = []
        logfile = os.path.join(imgdir,'conv_log','Render_convert'+log_name+'.log')
        
        if self.args.get('flatfield_correct'):
            if not os.path.exists('corrected'):os.makedirs('corrected')
        
        adoc_l=em.loadtext(adocfile)
        
        idx = 0
        startidx = -1
        adoc = []
        
        # get header to find out if idoc (TIFF list) or mdoc (MRC)
        a_head = em.mdoc_item(adoc_l,'',header=True)        
        
        if 'ImageFile' in a_head.keys():
            # mdoc - MRC
            imfile = ['mrc',a_head['ImageFile'][0]]
            tilestr = '[ZValue'
            ni = len(str(len(adoc)))      
            if not self.args.get('flatfield_correct'):
                if not os.path.exists('converted'):os.makedirs('converted')      
        else:
            # idoc -list of tifs
            tilestr = '[Ima'
            imfile = ['tif',base]
            tile1 = adoc_l[11]
            tile1 = tile1.rstrip('.tif]')
            ni = 0                                    
            while tile1.endswith('0'):
                tile1=tile1[:-1]
                ni += 1            
            

                
        for idx in range(len(adoc_l)-1):   
            if adoc_l[idx].startswith(tilestr):
                if startidx > -1:
                    adoc.append(em.mdoc_item(adoc_l,adoc_l[startidx].strip('[]\n')))               
                startidx=idx
                
    
        
        #prepare coordinate list 
        tilepx = []
        
        for tile in adoc:
            if 'AlignedPieceCoordsVS' in tile:                   
                tilepx.append(tile['AlignedPieceCoordsVS'])
            else:
                tilepx.append(tile['AlignedPieceCoords'])
        

        pxs = float(a_head['PixelSpacing'][0])/10000 # in um
        
        if self.args.get('flatfield_correct'):            
            p=Pool(self.args.get('pool_size'))
                        
            emptyt_1=[]
            for idx in range(np.min([100,len(adoc)])):
                emptyt_1.append(p.apply_async(self.create_average_image, (idx, ni,)))
                emptyt_1.append(p.apply_async(self.create_average_image, (len(adoc)-idx, ni,)))
                
            emptytiles=[e.get() for e in emptyt_1]
            
            et=list(filter(lambda ims: isinstance(ims, np.ndarray), emptytiles))
            
            k=np.median(et,axis=0).astype(float)
            k=k/k.mean() 
            
        else:
            k=[]
        
        
        
        q=Pool(self.args.get('pool_size'))            
        p2=[]
        for idx in range(10):#len(adoc)):
            p2.append(q.apply_async(self.ts_from_SerialEMtile,(imfile,idx,ni,pxs,tilepx,k,a_head,)))
            
        
        tilefiles, tilespecs = ([pp.get() for pp in p2])
    
    
    def get_tile(imfile,idx,ni):
        if imfile[0]=='mrc':
            mrcf = mrc.mmap(imfile[1])
            im = mrcf[:,:,idx]
        else:
            im = io.imread(imfile[1]+str(idx).zfill(ni)+'.tif')            
        return im
    
    
    
    def create_average_image(self,idx,ni,imfile):         
        a=self.get_tile(imfile,idx,ni)
        if a.std() < (self.args.get('flatfield_thresh') * a.mean()):
            return a
         
    def write_converted_tile(self,a,ni):         
        outfile = 'converted/'+self.base+'.'+str(idx).zfill(ni)+'.tif'
        io.imsave(outfile, a)
        ts = self.ts_from_SerialEMtile()
        return outfile
        
    def write_corrected_tile(self,a,ni,k):       
        b=a.astype(float)/k
        outfile = 'corrected/'+self.base+'.'+str(idx).zfill(ni)+'_corr.tif'
        io.imsave(outfile, b.astype(a.dtype))
        return outfile
    


    def run(self):
        # with open(self.args['metafile'], 'r') as f:
        #     meta = json.load(f)

        adocfile = self.args.get('adocfile')
        
                      
        # print(imgdir)

        tspecs,resolution = self.ts_from_serialem(adocfile)
        
        # create stack and fill resolution parameters
        
        
        self.args["output_stackVersion"]["stackResolutionX"]=resolution[0]
        self.args["output_stackVersion"]["stackResolutionY"]=resolution[1]
        self.args["output_stackVersion"]["stackResolutionZ"]=resolution[2]       
       

        

        self.output_tilespecs_to_stack(tspecs)
                                       
# I don know what this does... so leave it out
        # try:
        #     self.output({'stack': self.output_stack})
        # except AttributeError as e:
        #     self.logger.error(e)


if __name__ == "__main__":
    mod = GenerateSBEMImageTileSpecs(input_data=example_input)
    mod.run()
