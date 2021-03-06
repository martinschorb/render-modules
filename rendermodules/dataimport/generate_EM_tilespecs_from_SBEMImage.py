#!/usr/bin/env python
"""
create tilespecs from SBEMImage dataset
"""

import os
import numpy as np
import renderapi
from rendermodules.module.render_module import StackOutputModule

from rendermodules.dataimport.schemas import (GenerateEMTileSpecsOutput,
                                              GenerateSBEMTileSpecsParameters)

from rendermodules.utilities.EMBL_file_utils import groupsharepath

import time

import numpy as np
import glob
import bdv_tools as bdv
from pyEM import parse_adoc

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
    "image_directory": "/g/emcf/common/for_martin/SBEMdata/platy_20-05-27",
    "stack": "test_resolution",
    "overwrite_zlayer": True,
    "pool_size": 4,
    "close_stack": True,
    "z_index": 1,
    "output_stackVersion":{
        "stackResolutionX":10.1
        }
}


class GenerateSBEMImageTileSpecs(StackOutputModule):
    default_schema = GenerateSBEMTileSpecsParameters
    default_output_schema = GenerateEMTileSpecsOutput

    def rotmatrix(self,angle):
        th = np.radians(angle)
        c, s = np.cos(th), np.sin(th)
        M = np.array(((c, -s), (s, c)))
        return M

    def ts_from_SBEMtile(self,line,pxs,rotation):
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


        xpos=float(tile['glob_x'])/pxs
        ypos=float(tile['glob_y'])/pxs
        M = self.rotmatrix(rotation)

        pos = np.dot(M.T,[xpos,ypos])

        tf_trans = renderapi.transform.AffineModel(
                                 B0=pos[0],
                                 B1=pos[1])



        # tf_rot = renderapi.transform.AffineModel(
        #                           M00=M[0,0],
        #                           M01=M[0,1],
        #                           M10=M[1,0],
        #                           M11=M[1,1])

        print("Processing tile "+tile['tileid']+" metadata for Render.")


        ts = renderapi.tilespec.TileSpec(
            tileId=tile['tileid'],
            imagePyramid=ip,
            z=tile['slice_counter'],#tile['glob_z'],
            width=tile['tile_width'],
            height=tile['tile_height'],
            minint=0, maxint=255,
            tforms=[tf_trans],#,tf_rot],
            # imagePyramid=ip,
            sectionId=tile['slice_counter'],
            scopeId='3View',
            cameraId='3View',
            # imageCol=imgdata['img_meta']['raster_pos'][0],
            # imageRow=imgdata['img_meta']['raster_pos'][1],
            stageX = pos[0],
            stageY = pos[1],
            rotation = rotation,
            pixelsize = pxs)

        # json_file = os.path.realpath(os.path.join(tilespecdir,outputProject+'_'+outputOwner+'_'+outputStack+'_%04d.json'%z))
        # fd=open(json_file, "w")
        # renderapi.utils.renderdump(tilespeclist,fd,sort_keys=True, indent=4, separators=(',', ': '))
        # fd.close()

        return f1,ts


    def ts_from_sbemimage (self,imgdir):

        os.chdir(imgdir)


        timestamp = time.localtime()
        if not os.path.exists('conv_log'):os.makedirs('conv_log')
        log_name = '_{}{:02d}{:02d}-{:02d}{:02d}'.format(timestamp.tm_year,timestamp.tm_mon,timestamp.tm_mday,timestamp.tm_hour,timestamp.tm_min)


        # mipmap_args = []
        # tilespecpaths = []
        logfile = os.path.join(imgdir,'conv_log','Render_convert'+log_name+'.log')

        if not os.path.exists('meta'): raise  FileNotFoundError('Change to proper directory!')

        mfile0 = os.path.join('meta','logs','imagelist_')

        mfiles = glob.glob(mfile0+'*')

        tspecs=[]
        allspecs = []
        curr_res = -1
        curr_rot = -1
        stack_idx = 0

        for mfile in mfiles:

            stackname = self.args.get("output_stack")

            # with open(mfile) as mf: ml = mf.read().splitlines()
            acq_suffix = mfile[mfile.rfind('_'):]

            mdfile = os.path.join('meta','logs','metadata'+acq_suffix)

            with open(mdfile) as mdf: mdl = mdf.read().splitlines()

            conffile = os.path.join('meta','logs','config'+acq_suffix)

            with open(conffile) as cf: cl = cf.read().splitlines()

            config = parse_adoc(cl[:cl.index('[overviews]')])


            pxs = float(config['pixel_size'][0].strip('[],'))#/1000  # in um

            z_thick = float(config['slice_thickness'][0])#/1000  # in um

            resolution = [pxs,pxs,z_thick]
            rotation = float(config['rotation'][0].strip('[],'))

            if not curr_res == -1:
                if not resolution==curr_res:
                    stack_idx += 1
                    allspecs.append([stackname,tspecs,curr_res])
                    stackname += '_' + '%02d' %stack_idx
                    tspecs=[]
                elif not rotation==curr_rot:
                    stack_idx += 1
                    allspecs.append([stackname,tspecs,curr_res])
                    stackname += '_' + '%02d' % stack_idx
                    tspecs=[]

            curr_res = resolution
            curr_rot = rotation

            for line in mdl:
                if line.startswith('TILE: '):

                    f1,tilespeclist = self.ts_from_SBEMtile(line,pxs,rotation)

                    if os.path.exists(f1):
                        tspecs.append(tilespeclist)
                    else:
                        fnf_error = 'ERROR: File '+f1+' does not exist'
                        print(fnf_error)
                        with open(logfile,'w') as log: log.writelines(fnf_error)


        allspecs.append([stackname,tspecs,resolution])

        return allspecs #,mipmap_args

    def run(self):
        # with open(self.args['metafile'], 'r') as f:
        #     meta = json.load(f)

        imgdir = self.args.get('image_directory')


        # print(imgdir)

        allspecs = self.ts_from_sbemimage(imgdir)

        # create stack and fill resolution parameters

        for specs in allspecs:

            resolution=specs[2]

            self.args["output_stackVersion"]["stackResolutionX"]=resolution[0]
            self.args["output_stackVersion"]["stackResolutionY"]=resolution[1]
            self.args["output_stackVersion"]["stackResolutionZ"]=resolution[2]

            self.args["output_stack"] = specs[0]


            self.output_tilespecs_to_stack(specs[1])

# I don know what this does... so leave it out
        # try:
        #     self.output({'stack': self.output_stack})
        # except AttributeError as e:
        #     self.logger.error(e)


if __name__ == "__main__":
    mod = GenerateSBEMImageTileSpecs(input_data=example_input)
    mod.run()
