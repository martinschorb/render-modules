import renderapi
import os
from rendermodules.dataimport.generate_mipmaps import get_filepath_from_tilespec,GenerateMipMaps

from rendermodules.module.render_module import StackInputModule
from rendermodules.dataimport.schemas import GenerateMipMapsParameters
                              

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
    "input_stack": "TEST_IMPORT_FROM_SBEMIMAGE",
    "method": "PIL",    
    "convert_to_8bit": "False", # IMPORTANT!!! True will create black images when original data is 8bit (SBEMImage)
    "imgformat": "tif",
    "levels": 4,
    "force_redo": "True",
    "z":0,
    "pool_size":16,
    "output_prefix":"", # required field, will be unset and auto-generated in this script
}




class EMBLMipMaps(StackInputModule):
    default_schema = GenerateMipMapsParameters
    default_output_schema = GenerateMipMapsParameters

    def run(self):
        self.logger.debug('Mipmap paramter generation')
        
        tilespecs = self.render.run(renderapi.tilespec.get_tile_specs_from_stack,
                               self.args['input_stack'])

        ts = tilespecs[0]
    
        file0 = get_filepath_from_tilespec(ts)
        
        prefix = os.path.splitext(os.path.basename(file0))[0]
        
        # SBEMImage:        
        if "/tiles/" in file0:
            rootpath = file0[:file0.rfind("/tiles/")]
        else:
            rootpath = file0[:file0.rfind("/")]

        downdir = os.path.join(rootpath,"processed","mipmaps")
        
        # print(prefix)
        
        params = self.args
        del params["output_prefix"]
        params["output_dir"]=downdir
       
        
        # z=0 --> process entire stack
        
        
        if params["z"] == 0:
            stackbounds = renderapi.stack.get_stack_bounds(params["input_stack"],render=self.render)
            del(params["z"])
            del(params["zValues"])
                        
            params["minZ"] = stackbounds["minZ"]
            params["maxZ"] = stackbounds["maxZ"]
        
        
        mipmaps = GenerateMipMaps(input_data=params)
        mipmaps.run()
        
        # #print "This is the Down Sampled Directory: %s"%downdir

        # if not os.path.exists(downdir):
        #     os.makedirs(downdir)



if __name__ == "__main__":
    mod = EMBLMipMaps(input_data=example)
    #mod = GenerateMipMaps(schema_type=GenerateMipMapsParameters)
    mod.run()
