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
    "stack": "groupshare_client_script_test",
    "overwrite_zlayer": True,
    "pool_size": 4,
    "close_stack": True,
    "z_index": 1
}


class GenerateSBEMImageTileSpecs(StackOutputModule):
    default_schema = GenerateSBEMTileSpecsParameters
    default_output_schema = GenerateEMTileSpecsOutput

    def ts_from_imgdata(self, imgdata, imgprefix, x, y,
                        minint=0, maxint=255, maskUrl=None,
                        width=3840, height=3840, z=None, sectionId=None,
                        scopeId=None, cameraId=None, pixelsize=None):
        tileId = self.tileId_from_basename(imgdata['img_path'])
        sectionId = (self.sectionId_from_z(z) if sectionId is None
                     else sectionId)
        raw_tforms = [renderapi.transform.AffineModel(B0=x, B1=y)]

        imageUrl = uri_utils.uri_join(imgprefix, imgdata['img_path'])

        # imageUrl = pathlib.Path(
        #     os.path.abspath(os.path.join(
        #         imgdir, imgdata['img_path']))).as_uri()
        # if maskUrl is not None:
        #         maskUrl = pathlib.Path(maskUrl).as_uri()

        ip = renderapi.image_pyramid.ImagePyramid()
        ip[0] = renderapi.image_pyramid.MipMap(imageUrl=imageUrl,
                                               maskUrl=maskUrl)
        return renderapi.tilespec.TileSpec(
            tileId=tileId, z=z,
            width=width, height=height,
            minint=minint, maxint=maxint,
            tforms=raw_tforms,
            imagePyramid=ip,
            sectionId=sectionId, scopeId=scopeId, cameraId=cameraId,
            imageCol=imgdata['img_meta']['raster_pos'][0],
            imageRow=imgdata['img_meta']['raster_pos'][1],
            stageX=imgdata['img_meta']['stage_pos'][0],
            stageY=imgdata['img_meta']['stage_pos'][1],
            rotation=imgdata['img_meta']['angle'], pixelsize=pixelsize)

    def ts_from_SBEMtile(self,line,pxs):
        tile = bdv.str2dict(line[line.find('{'):])

   # 2) The translation matrix to position the object in space (lower left corner)
        mat_t = np.concatenate((np.eye(3),[[tile['glob_x']],[tile['glob_y']],[tile['glob_z']]]),axis=1)
        mat_t = np.concatenate((mat_t,[[0,0,0,1]]))

        f1 = os.path.realpath(tile['filename'])

        # fbase = os.path.splitext(os.path.basename(f1))[0]

        # tilespecdir = os.path.join('processed','tilespec')

        filepath= groupsharepath(f1)


        # #print tilespecdir
        # if not os.path.isdir(tilespecdir):
        #     os.makedirs(tilespecdir)

        # downdir = os.path.join("processed","downsamp_images")
        # #print "This is the Down Sampled Directory: %s"%downdir

        # if not os.path.exists(downdir):
        #     os.makedirs(downdir)

        

        ip = renderapi.image_pyramid.ImagePyramid()
        ip[0] = renderapi.image_pyramid.MipMap(imageUrl='file://' + filepath)

        # mipmap0 = MipMapLevel(level=0,imageUrl='file://' + filepath)
        # mipmaplevels=[mipmap0]
        # filename = tile['tileid']

        # for i in range(1,4):
        #     scUrl = 'file://' + os.path.join(downdir1,fbase) + '_mip0%d.jpg'%i
        #     mml = MipMapLevel(level=i,imageUrl=scUrl)
        #     mipmaplevels.append(mml)

        tform = renderapi.transform.AffineModel(M00=1,
                                 M01=0,
                                 M10=0,
                                 M11=1,
                                 B0=tile['glob_x']/10,
                                 B1=tile['glob_y']/10)

        # tilespeclist.append(TileSpec(tileId=tile['tileid'],
        #                      frameId = tile['tileid'][:tile['tileid'].find('.')],
        #                      z=tile['glob_z'],
        #                      width=tile['tile_width'],
        #                      height=tile['tile_height'],
        #                      mipMapLevels=mipmaplevels,
        #                      tforms=[tform],
        #                      minint=minval,
        #                      maxint=maxval,
        #                      layout= layout))
        ts = renderapi.tilespec.TileSpec(
            tileId=tile['tileid'],
            imagePyramid=ip,
            z=tile['glob_z'],
            width=tile['tile_width'],
            height=tile['tile_height'],
            minint=0, maxint=255,
            tforms=[tform],
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

        return f1,downdir,ts


    def ts_from_sbemimage (self,imgdir):

        os.chdir(imgdir)

        # mipmap_args = []
        # tilespecpaths = []


        if not os.path.exists('meta'): print('Change to proper directory!');exit()


        mfile0 = os.path.join('meta','logs','imagelist_')

        mfiles = glob.glob(mfile0+'*')


        for mfile in mfiles:

            # with open(mfile) as mf: ml = mf.read().splitlines()

            mdfile = os.path.join('meta','logs','metadata'+mfile[mfile.rfind('_'):])

            with open(mdfile) as mdf: mdl = mdf.read().splitlines()

            conffile = os.path.join('meta','logs','config'+mfile[mfile.rfind('_'):])

            with open(conffile) as cf: cl = cf.read().splitlines()

            config = parse_adoc(cl)


            pxs = float(config['grab_frame_pixel_size'][0])#/1000  # in um
            z_thick = float(config['slice_thickness'][0])#/1000  # in um


             # generate the individual transformation matrices
             # 1)  The scale and rotation information form the map item
            mat = np.diag((pxs,pxs,z_thick))

            mat_s = np.concatenate((mat,[[0],[0],[0]]),axis=1)
            mat_s = np.concatenate((mat_s,[[0,0,0,1]]))

            tspecs=[]
            # z=0

            for line in mdl:
                if line.startswith('TILE: '):

                    f1,downdir,tilespeclist = self.ts_from_SBEMtile(line,pxs)

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
