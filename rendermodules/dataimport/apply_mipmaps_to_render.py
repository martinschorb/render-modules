#!/usr/bin/env python
import renderapi
import os
from rendermodules.module.render_module import StackTransitionModule
from functools import partial
from six.moves import urllib
from rendermodules.dataimport.schemas import (
    AddMipMapsToStackParameters, AddMipMapsToStackOutput)

from rendermodules.utilities import uri_utils


if __name__ == "__main__" and __package__ is None:
    __package__ = "rendermodules.dataimport.apply_mipmaps_to_render"

example = {
    "render": {
        "host": "pc-emcf-16.embl.de",
        "port": 8080,
        "owner": "test",
        "project": "RENDERmodule_TEST",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/"
            "src/main/scripts")},
    "input_stack": "test2",
    "output_stack": "test2_mipmap",
    "mipmap_prefix": "file:///g/emcf/common/for_martin/SBEMdata/platy_20-05-27/processed/mipmaps",
    "imgformat": "png",
    "close_stack": True,
    "levels": 4,
    "zstart": 442,
    "zend": 450,
    'pool_size':4,
    "output_json":"/g/emcf/software/render/test1.json"
}


def addMipMapsToRender(render, input_stack, mipmap_prefix, imgformat, levels, z):
    # tilespecPaths = []

    # tilespecs = render.run(renderapi.tilespec.get_tile_specs_from_z,
    #                        input_stack, z)
    resolvedtiles = render.run(
        renderapi.resolvedtiles.get_resolved_tiles_from_z,
        input_stack, z)

    for ts in resolvedtiles.tilespecs:
        mm1 = ts.ip[0]

        oldUrl = mm1.imageUrl
        filepath = urllib.parse.urlparse(oldUrl).path
        # filepath = urllib.parse.unquote(urllib.parse.urlparse(str(oldUrl)).path)

        # assumes that the mipmaps are stored in the way generated by the render's mipmap client
        # which adds the file extension in addition to the existing file extension from mipmap level 0
                
        # if imgformat is "png":
        #     imgf = ".png"
        # elif imgformat is "jpg":
        #     imgf = ".jpg"
        # else:
        #     imgf = ".tif"
        imgf = "."+imgformat.lstrip(".")    
            
        for i in range(1, levels+1):
            # scUrl = 'file:' + os.path.join(
            #     mipmap_dir, str(i), filepath.lstrip(os.sep)) + imgf
            scUrl = uri_utils.uri_join(
                mipmap_prefix, str(i), "{}{}".format(
                    os.path.basename(filepath), imgf))

            mm1 = renderapi.image_pyramid.MipMap(imageUrl=scUrl)
            ts.ip[i] = mm1
    return resolvedtiles
    # tilespecPaths.append(renderapi.utils.renderdump_temp(tilespecs))
    # return tilespecPaths


class AddMipMapsToStack(StackTransitionModule):
    default_schema = AddMipMapsToStackParameters
    default_output_schema = AddMipMapsToStackOutput

    def run(self):
        self.logger.debug('Applying mipmaps to stack')
        zvalues = self.get_overlapping_inputstack_zvalues()
        if len(zvalues) == 0:
            self.logger.error('No sections found for stack {}'.format(
                self.args['input_stack']))
        
        self.logger.debug("{}".format(zvalues))
        mypartial = partial(
            addMipMapsToRender, self.render, self.args['input_stack'],
            self.args['mipmap_prefix'], self.args['imgformat'],
            self.args['levels'])

        with renderapi.client.WithPool(self.args['pool_size']) as pool:
            #  tilespecs = [i for l in pool.map(mypartial, zvalues)
            #               for i in l]

            allresolved = pool.map(mypartial, zvalues)

        tilespecs = [i for l in (
            resolvedtiles.tilespecs for resolvedtiles in allresolved)
                     for i in l]
        identified_tforms = list({tform.transformId: tform for tform in (
            i for l in (resolvedtiles.transforms
                        for resolvedtiles in allresolved)
            for i in l)}.values())

        output_stack = (self.args['input_stack'] if
                        self.args['output_stack'] is None

                        else self.args['output_stack'])  
        
        input_params = renderapi.stack.get_full_stack_metadata(self.args['input_stack'],render=self.render)
                
        self.args["output_stackVersion"]=input_params['currentVersion']

        self.output_tilespecs_to_stack(tilespecs, output_stack,
                                       sharedTransforms=identified_tforms)

        missing_ts_zs = []
        for z in zvalues:
            job_success = self.validate_tilespecs(
                self.args['input_stack'], self.args['output_stack'], z)
            if not job_success:
                missing_ts_zs.append(z)
        self.output(
            {
                "output_stack": output_stack,
                "missing_tilespecs_zs": missing_ts_zs
            })


if __name__ == "__main__":
    mod = AddMipMapsToStack(input_data=example)
    # mod = AddMipMapsToStack(schema_type=AddMipMapsToStackParameters)
    mod.run()
