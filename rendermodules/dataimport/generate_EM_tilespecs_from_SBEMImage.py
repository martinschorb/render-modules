#!/usr/bin/env python
"""
create tilespecs from SBEMImage dataset
"""

import os
import numpy
import renderapi
from rendermodules.module.render_module import StackOutputModule

from rendermodules.dataimport.schemas import (GenerateEMTileSpecsOutput,
                                              GenerateSBEMTileSpecsParameters)

from rendermodules.utilities.EMBL_file_utils import groupsharepath

import numpy as np
import glob
import bdv_tools as bdv
from pyEM import parse_adoc

from rendermodules.utilities import uri_utils


example_input = {
    "render": {
        "host": "pc-emcf-16.embl.de",
        "port": 8080,
        "owner": "test",
        "project": "RENDERmodule_TEST",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/"
            "src/main/scripts")},
    "image_directory": "/g/emcf/common/for_martin/SBEMdata/platy_20-05-27",
    "stack": "test2",
    "overwrite_zlayer": True,
    "pool_size": 4,
    "close_stack": True,
    "z_index": 1
}


class GenerateSBEMImageTileSpecs(StackOutputModule):
    default_schema = GenerateSBEMTileSpecsParameters
    default_output_schema = GenerateEMTileSpecsOutput


    def ts_from_SBEMtile(self,line,pxs):
        tile = bdv.str2dict(line[line.find('{'):])
        
        # curr_posid = [int(tile['tileid'].split('.')[0]),int(tile['tileid'].split('.')[1])]
        # curr_pos = tilepos[posid.index(str(curr_posid[0])+'.'+str(curr_posid[1]))]

   # 2) The translation matrix to position the object in space (lower left corner)
        # mat_t = np.concatenate((np.eye(3),[[tile['glob_x']],[tile['glob_y']],[tile['glob_z']]]),axis=1)
        # mat_t = np.concatenate((mat_t,[[0,0,0,1]]))

        f1 = os.path.realpath(tile['filename'])

        filepath= groupsharepath(f1)        

        ip = renderapi.image_pyramid.ImagePyramid()
        ip[0] = renderapi.image_pyramid.MipMap(imageUrl='file://' + filepath)        

        tf_trans = renderapi.transform.AffineModel(
                                 B0=tile['glob_x'],
                                 B1=tile['glob_y'])
        
        tf_scale = renderapi.transform.AffineModel(
                                 M00=pxs,
                                 M11=pxs)

        
        
        ts = renderapi.tilespec.TileSpec(
            tileId=tile['tileid'],
            imagePyramid=ip,
            z=tile['slice_counter'],#tile['glob_z'],
            width=tile['tile_width'],
            height=tile['tile_height'],
            minint=0, maxint=255,
            tforms=[tf_scale,tf_trans],
            # imagePyramid=ip,
            sectionId=tile['slice_counter'],
            scopeId='3View',
            cameraId='3View',
            # imageCol=imgdata['img_meta']['raster_pos'][0],
            # imageRow=imgdata['img_meta']['raster_pos'][1],
            stageX = tile['glob_x']/10,
            stageY = tile['glob_y']/10,
            rotation = 0.0,
            pixelsize = pxs)

        # json_file = os.path.realpath(os.path.join(tilespecdir,outputProject+'_'+outputOwner+'_'+outputStack+'_%04d.json'%z))
        # fd=open(json_file, "w")
        # renderapi.utils.renderdump(tilespeclist,fd,sort_keys=True, indent=4, separators=(',', ': '))
        # fd.close()

        return f1,ts


    def ts_from_sbemimage (self,imgdir):

        os.chdir(imgdir)

        # mipmap_args = []
        # tilespecpaths = []


        if not os.path.exists('meta'): print('Change to proper directory!');exit()


        mfile0 = os.path.join('meta','logs','imagelist_')

        mfiles = glob.glob(mfile0+'*')


        for mfile in mfiles:

            # with open(mfile) as mf: ml = mf.read().splitlines()
            acq_suffix = mfile[mfile.rfind('_'):]

            mdfile = os.path.join('meta','logs','metadata'+acq_suffix)

            with open(mdfile) as mdf: mdl = mdf.read().splitlines()

            conffile = os.path.join('meta','logs','config'+acq_suffix)

            with open(conffile) as cf: cl = cf.read().splitlines()

            config = parse_adoc(cl)
            
            # tileposfile = os.path.join('meta','logs','tilepos'+acq_suffix)
            
            # with open(tileposfile) as tpf: tilepos0 = tpf.read().splitlines()
            
            # tilepos = []
            # posid = []
            
            # for tile in tilepos0: 
            #     tilepos.append(tile.split(';')[1:]) 
            #     posid.append(tile.split(';')[0])


            pxs = float(config['grab_frame_pixel_size'][0])#/1000  # in um
            z_thick = float(config['slice_thickness'][0])#/1000  # in um

            # generate the individual transformation matrices
            # 1)  The scale and rotation information form the map item
            # mat = np.diag((pxs,pxs,z_thick))

            # mat_s = np.concatenate((mat,[[0],[0],[0]]),axis=1)
            # mat_s = np.concatenate((mat_s,[[0,0,0,1]]))

            tspecs=[]
            # z=0

            for line in mdl:
                if line.startswith('TILE: '):

                    f1,tilespeclist = self.ts_from_SBEMtile(line,pxs)

                    # mipmap_args.append((f1,os.path.realpath(downdir)))
                    tspecs.append(tilespeclist)

        return tspecs #,mipmap_args


    def run(self):
        # with open(self.args['metafile'], 'r') as f:
        #     meta = json.load(f)

        imgdir = self.args.get('image_directory')

        print(imgdir)

        tspecs = self.ts_from_sbemimage(imgdir)
                    # imgdir,
                    # img_coords[img['img_path']][0] - minX,
                    # img_coords[img['img_path']][1] - minY,
                    # minint=self.args['minimum_intensity'],
                    # maxint=self.args['maximum_intensity'],
                    # width=roidata['camera_info']['width'],
                    # height=roidata['camera_info']['height'],
                    # z=self.zValues[0], sectionId=self.args.get('sectionId'),
                    # scopeId=roidata['temca_id'],
                    # cameraId=roidata['camera_info']['camera_id'],
                    # pixelsize=pixelsize,
                    # maskUrl=self.args['maskUrl_uri']) for img in imgdata]

        self.output_tilespecs_to_stack(tspecs)

# I don know what this does... so leave it out
        # try:
        #     self.output({'stack': self.output_stack})
        # except AttributeError as e:
        #     self.logger.error(e)


if __name__ == "__main__":
    mod = GenerateSBEMImageTileSpecs(input_data=example_input)
    mod.run()
