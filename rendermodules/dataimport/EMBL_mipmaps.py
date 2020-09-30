import renderapi
import os
from rendermodules.dataimport.generate_mipmaps import get_filepath_from_tilespec

from rendermodules.module.render_module import StackInputModule, RenderModuleException
from rendermodules.module.schemas import InputStackParameters
                              


from rendermodules.dataimport.schemas import (
    GenerateMipMapsParameters, GenerateMipMapsOutput)

if __name__ == "__main__" and __package__ is None:
    __package__ = "rendermodules.dataimport.generate_mipmaps"

example = {
    "render": {
        "host": "pc-emcf-16.embl.de",
        "port": 8080,
        "owner": "test",
        "project": "RENDERmodule_TEST",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/"
            "src/main/scripts")},
    "method": "PIL",
    "input_stack": "TEST_IMPORT_FROM_SBEMIMAGE",
    "convert_to_8bit": "False",
    "method": "PIL",
    "imgformat": "tif",
    "levels": 6,
    "force_redo": "True",
    "z":0
}




class EMBLMipMaps(StackInputModule):
    default_schema = InputStackParameters
    default_output_schema = InputStackParameters

    def run(self):
        self.logger.debug('Mipmap paramter generation')
        
        tilespecs = self.render.run(renderapi.tilespec.get_tile_specs_from_stack,
                               self.args['input_stack'])

        ts = tilespecs[0]
        
        file0 = get_filepath_from_tilespec(ts)
        
        mainpath,tile0 = os.path.s(file0)
        
        print(file0)



if __name__ == "__main__":
    mod = EMBLMipMaps(input_data=example)
    #mod = GenerateMipMaps(schema_type=GenerateMipMapsParameters)
    mod.run()
