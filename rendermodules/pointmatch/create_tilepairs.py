
import json
import os
import subprocess
import renderapi
from rendermodules.module.render_module import RenderModule
from rendermodules.pointmatch.schemas import TilePairClientParameters, TilePairClientOutputParameters

if __name__ == "__main__" and __package__ is None:
    __package__ = "rendermodules.pointmatch.create_tilepairs"


example = {
    "render": {
        "host": "pc-emcf-16.embl.de",
        "port": 8080,
        "owner": "test",
        "project": "RENDERmodule_TEST",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/"
            "src/main/scripts")},
    "minZ":442,
    "maxZ":450,
    "zNeighborDistance":1,
    "stack":"test2_mipmap",
    "xyNeighborFactor": 0.9,
    "excludeCornerNeighbors":"true",
    "excludeSameLayerNeighbors":"false",
    "excludeCompletelyObscuredTiles":"true",
    "output_dir":"/g/emcf/schorb/",
    "output_json":"/g/emcf/schorb/tiles.json",
}



class TilePairClientModule(RenderModule):
    default_schema = TilePairClientParameters
    default_output_schema = TilePairClientOutputParameters
    client_class = 'org.janelia.render.client.TilePairClient'
    client_script_name = 'run_ws_client.sh'

    def run(self):
        zvalues = self.render.run(
            renderapi.stack.get_z_values_for_stack, self.args['stack'])

        if self.args['minZ'] is not None:
            self.args['minZ'] = self.args['minZ'] if self.args['minZ'] > min(zvalues) else min(zvalues)
        else:
            self.args['minZ'] = min(zvalues)
            
        if self.args['maxZ'] is not None:
            self.args['maxZ'] = self.args['maxZ'] if self.args['maxZ'] < max(zvalues) else max(zvalues)
        else: 
            self.args['maxZ'] = max(zvalues)

        tilepairJsonFile = "tile_pairs_%s_z_%d_to_%d_dist_%d.json"%(self.args['stack'], self.args['minZ'], self.args['maxZ'], self.args['zNeighborDistance'])
        tilepairJsonFile = os.path.join(
                                self.args['output_dir'],
                                tilepairJsonFile)

        tilepairs = self.render.run(
                        renderapi.client.tilePairClient,
                        self.args['stack'],
                        self.args['minZ'],
                        self.args['maxZ'],
                        outjson=tilepairJsonFile,
                        basestack=self.args['baseStack'],
                        xyNeighborFactor=self.args['xyNeighborFactor'],
                        zNeighborDistance=self.args['zNeighborDistance'],
                        excludeCornerNeighbors=self.args['excludeCornerNeighbors'],
                        excludeSameLayerNeighbors=self.args['excludeSameLayerNeighbors'],
                        excludeCompletelyObscuredTiles=self.args['excludeCompletelyObscuredTiles'])

        self.output({'tile_pair_file':tilepairJsonFile})
        

if __name__ == "__main__":
    module = TilePairClientModule(input_data=example)
    #module = TilePairClientModule(schema_type=TilePairClientParameters)
    module.run()
