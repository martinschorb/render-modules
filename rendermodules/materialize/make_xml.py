import argschema
from rendermodules.materialize.schemas import MakeXMLParameters, MakeXMLOutput
from pybdv.metadata import write_xml_metadata, write_h5_metadata, write_n5_metadata, validate_attributes
# import sys



example = {
    "path": "Secs_1015_1099_5_reflections_mml6_montage",
    "scale_factors": 3 * [[2, 2, 2]],
    "resolution": [0.05, 0.015, 0.015],
    "unit": 'micrometer'
}


class MakeXML(argschema.schemas.DefaultSchema):
    default_schema = MakeXMLParameters
    default_output_schema = MakeXMLOutput



    def make_render_xml(path, scale_factors , resolution, unit):
        
        if path.endswith('n5'):
            xml_path = path.replace('.n5', '.xml')
            is_h5=False
        elif path.endswith('h5'):
            xml_path = path.replace('.h5', '.xml')
            is_h5=True
    
        attrs = {'channel': {'id': None}}
        attrs = validate_attributes(xml_path, attrs, setup_id=0,
                                    enforce_consistency=False)
        
        
        write_xml_metadata(xml_path, path, unit, resolution,
                           is_h5=is_h5,
                           setup_id=0, timepoint=0,
                           setup_name=None,
                           affine=None,
                           attributes=attrs,
                           overwrite=False,
                           overwrite_data=False,
                           enforce_consistency=False)
        
        if is_h5:
            write_h5_metadata(path, scale_factors, resolution, setup_id=0, timepoint=0, overwrite=True)
        else:
            write_n5_metadata(path, scale_factors, resolution, setup_id=0, timepoint=0, overwrite=True)
            
            
            

    def run(self):        
        self.make_render_xml(self.args['path'], self.args['scale_factors'] , self.args['resolution'], self.args['unit'])
        
        
        
if __name__ == "__main__":
    mod = MakeXML(input_data=example)
    mod.run()
 