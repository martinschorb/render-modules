import json
import os
import subprocess
from argschema.fields import Bool, Float, Int, Nested, Str, InputDir
from argschema.schemas import DefaultSchema
import marshmallow as mm
import renderapi
from rendermodules.module.render_module import RenderModule
from rendermodules.pointmatch.schemas import PointMatchClientParametersSpark

if __name__ == "__main__" and __package__ is None:
    __package__ = "rendermodules.pointmatch.generate_point_matches_spark"

example = {
    "render": {
        "host": "http://em-131fs",
        "port": 8080,
        "owner": "gayathri",
        "project": "MM2",
        "client_scripts": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/render_20170613/render-ws-java-client/src/main/scripts"
    },
    "sparkhome": "/allen/programs/celltypes/workgroups/em-connectomics/ImageProcessing/utils/spark/",
    "masterUrl":"spark://10.128.124.100:7077",
    "logdir": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/scratch/sparkLogs/",
    "jarfile": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/render_20170613/render-ws-spark-client/target/render-ws-spark-client-0.3.0-SNAPSHOT-standalone.jar",
    "className":"org.janelia.render.client.spark.SIFTPointMatchClient",
    "baseDataUrl":"http://em-131fs:8080/render-ws/v1",
    "owner": "gayathri_MM2",
    "collection": "mm2_rough_align_test",
    "pairJson": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/scratch/rough/tilePairs/tile_pairs_mm2_montage_scape_test_z_1015_to_1035_dist_5.json",
    "SIFTfdSize": 8,
    "SIFTsteps": 3,
    "matchMaxEpsilon": 20.0,
    "maxFeatureCacheGb": 15,
    "SIFTminScale": 0.38,
    "SIFTmaxScale": 0.82,
    "renderScale": 0.3,
    "matchRod": 0.9,
    "matchMinInlierRatio": 0.0,
    "matchMinNumInliers": 8,
    "matchMaxNumInliers": 200
}

class PointMatchClientModuleSpark(RenderModule):
    def __init__(self, schema_type=None, *args, **kwargs):
        if schema_type is None:
            schema_type = PointMatchClientParametersSpark
        super(PointMatchClientModuleSpark, self).__init__(
            schema_type=schema_type, *args, **kwargs)

    def run(self):
        # prepare sift parameters
        sift_params = " --SIFTFdSize {}".format(self.args['SIFTfdSize'])
        sift_params + sift_params + " --SIFTsteps {}".format(self.args['SIFTsteps'])
        sift_params = sift_params + " --matchMaxEpsilon {}".format(self.args['matchMaxEpsilon'])
        sift_params = sift_params + " --maxFeatureCacheGb {}".format(self.args['maxFeatureCacheGb'])
        sift_params = sift_params + " --SIFTminScale {}".format(self.args['SIFTminScale'])
        sift_params = sift_params + " --SIFTmaxScale {}".format(self.args['SIFTmaxScale'])
        sift_params = sift_params + " --renderScale {}".format(self.args['renderScale'])
        sift_params = sift_params + " --matchRod {}".format(self.args['matchRod'])
        sift_params = sift_params + " --matchMinInlierRatio {}".format(self.args['matchMinInlierRatio'])
        sift_params = sift_params + " --matchMinNumInliers {}".format(self.args['matchMinNumInliers'])
        sift_params = sift_params + " --matchMaxNumInliers {}".format(self.args['matchMaxNumInliers'])

        sparksubmit = os.path.join(self.args['sparkhome'], 'bin', 'spark-submit')

        # prepare the spark submit command
        cmd = "{} --master {}".format(sparksubmit, self.args['masterUrl'])
        cmd = cmd + " --executor-memory {}".format(self.args['memory'])
        cmd = cmd + " --class {} {}".format(self.args['className'], self.args['jarfile'])
        cmd = cmd + " --baseDataUrl {}".format(self.args['baseDataUrl'])
        cmd = cmd + " --owner {}".format(self.args['owner'])
        cmd = cmd + " --collection {}".format(self.args['collection'])
        cmd = cmd + " --pairJson {}".format(self.args['pairJson'])

        cmd_to_submit = cmd + sift_params

        os.system(cmd)

if __name__ == "__main__":
    module = PointMatchClientModuleSpark(input_data=example)
    #module = PointMatchClientModuleSpark(schema_type=PointMatchClientParameters)
    module.run()
