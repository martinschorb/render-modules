import argschema
from bigfeta import bigfeta

from rendermodules.solver.schemas import BigFetaSchema, BigFetaOutputSchema

montage_example = {
   "first_section": 442,
   "last_section": 450,
   "solve_type": "montage",
   "close_stack": "True",
   "transformation": "affine",
   "start_from_file": "",
   "output_mode": "stack",
   "output_json":"/g/emcf/schorb/solve.json",
   "input_stack": {
       "owner": "test",
       "project": "RENDERmodule_TEST",
       "name":"test2_mipmap",
       "host": "pc-emcf-16",
       "port": 8080,
       "mongo_host": "pc-emcf-16",
       "mongo_port": 27017,
       "client_scripts": "/g/emcf/software/render/render-ws-java-client/"
                "src/main/scripts",
       "collection_type": "stack",
       "db_interface": "mongo"
   },
   "pointmatch": {
       "owner": "test",
       "name": "test2_mipmap_2D",
       "host": "pc-emcf-16",
       "port": 8080,
       "mongo_host": "pc-emcf-16",
       "mongo_port": 27017,
       "client_scripts": "/g/emcf/software/render/render-ws-java-client/"
                "src/main/scripts",
       "collection_type": "pointmatch",
       "db_interface": "mongo"
   },
   "output_stack": {
       "owner": "test",
       "project": "RENDERmodule_TEST",
       "name": "2D_montage_results",
       "host": "pc-emcf-16",
       "port": 8080,
       "mongo_host": "pc-emcf-16",
       "mongo_port": 27017,
       "client_scripts": "/g/emcf/software/render/render-ws-java-client/"
                "src/main/scripts",
       "collection_type": "stack",
       "db_interface": "render"
   },
   "hdf5_options": {
       "output_dir": "/g/emcf/schorb/",
       "chunks_per_file": 256
   },
   "matrix_assembly": {
       "depth": 2,
       "montage_pt_weight": 1.0,
       "cross_pt_weight": 0.5,
       "npts_min": 5,
       "npts_max": 500,
       "inverse_dz":"True"
   },
   "regularization": {
       "default_lambda": 1.0e3,
       "translation_factor": 1.0e-5
   }
}


class Solve_stack(argschema.ArgSchemaParser):
    default_schema = BigFetaSchema
    default_output_schema = BigFetaOutputSchema

    def run(self):
        self.module = bigfeta.BigFeta(input_data=self.args, args=[])
        self.module.run()
        self.output(
            {"stack": self.args['output_stack']['name'][0]})


if __name__ == "__main__":
    module = Solve_stack(input_data=montage_example)
    module.run()
