import renderapi
import os
from pathos.multiprocessing import Pool
from functools import partial
from ..module.render_module import RenderModule, RenderParameters
import argschema
import marshmallow as mm

example_json={
    "render":{
            "host": "ibs-forrestc-ux1",
            "port": 8080,
            "owner": "NewOwner",
            "project": "H1706003_z150",
            "client_scripts": "/pipeline/render/render-ws-java-client/src/main/scripts"
        },
        "example":"my example parameters"
}

class TemplateParameters(RenderParameters):
    example = argschema.fields.Str(required=True,
        description='an example')
    default_val = argschema.fields.Str(required=False,default="a default value",
        description='an example with a default')

class TemplateOutputParameters(argschema.schemas.DefaultSchema):
    output_value = argschema.fields.Str(required=True,
                                        description= "an output of the module")

class TemplateModule(RenderModule):
    default_schema = TemplateParameters
    default_output_schema = TemplateOutputParameters
    def run(self):
        d = {
            "output_value":self.args['example']+self.args['default_val']
        }
        self.output(d)
        self.logger.error('this module does nothing useful')

if __name__ == "__main__":
    mod = TemplateModule(input_data= example_json)
    mod.run()
