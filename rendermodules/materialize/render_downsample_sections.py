import os
import renderapi
from ..module.render_module import RenderModule
from argschema.fields import OutputDir, InputFile, OutputDir, Str, Float, Int, Boolean
from functools import partial
import glob
import numpy as np


if __name__ == "__main__" and __package__ is None:
    __package__ = "rendermodules.materialize.render_section_at_scale"


example = {
    "render": {
        "host": "http://em-131fs",
        "port": 8998,
        "owner": "gayathri",
        "project": "MM2",
        "client_scripts": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/render_20170613/render-ws-java-client/src/main/scripts"
    },
    "input_stack": "mm2_acquire_8bit_reimage_Montage",
    "image_directory": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/scratch",
    "imgformat":"png",
    "scale": 0.01,
    "minZ": 1015,
    "maxZ": 1020
}



class RenderSectionAtScale(RenderModule):
    def __init__(self, schema_type=None, *args, **kwargs):
        if schema_type is None:
            schema_type = RenderSectionAtScaleParameters
        super(RenderSectionAtScale, self).__init__(
            schema_type=schema_type, *args, **kwargs)

    def run(self):
        zvalues = self.render.run(
            renderapi.stack.get_z_values_for_stack,
            self.args['input_stack'])

        if self.args['minZ'] == -1 || self.args['maxZ'] == -1:
            self.args['minZ'] = min(zvalues)
            self.args['maxZ'] = max(zvalues)
        elif self.args['minZ'] > self.args['maxZ']:
            self.logger.error('Invalid Z range')
        else:
            zvalues = zvalues[(zvalues >= self.args['minZ']) & (zvalues <= self.args['maxZ'])]

        if len(zvalues) == 0:
            self.logger.error('No valid zvalues found in stack for given range {} - {}'.format(self.args['minZ'], self.arfs['maxZ']))

        self.render.run(renderapi.client.renderSectionClient,
                        self.args['input_stack'],
                        self.args['image_directory'],
                        zvalues,
                        scale=str(self.args['scale']),
                        format=self.args['imgformat'],
                        doFilter=self.args['doFilter'],
                        fillWithNoise=self.args['fillWithNoise'])

if __name__ == "__main__":
    mod = RenderSectionAtScale(input_data=example)
    mod.run()
