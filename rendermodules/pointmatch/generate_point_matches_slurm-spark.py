import json
import os
import subprocess
# from urlparse import urlparse
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from argschema.fields import Bool, Float, Int, Nested, Str, InputDir
from argschema.schemas import DefaultSchema
import marshmallow as mm
import renderapi
from rendermodules.module.render_module import RenderModule, RenderModuleException
from rendermodules.module.render_module import SlurmSparkModule
from rendermodules.pointmatch.schemas import PointMatchClientParametersSlurmSpark,PointMatchClientOutputSchema

if __name__ == "__main__" and __package__ is None:
    __package__ = "rendermodules.pointmatch.generate_point_matches_spark"

example = {
    "render": {
        "host": "pc-emcf-16.embl.de",
        "port": 8080,
        "owner": "SBEM_test"},
    "sparkhome": "/g/emcf/software/spark-3.0.0-bin-hadoop3.2",
    "logdir": "/g/emcf/schorb/test",
    "jarfile": "/g/emcf/software/render/render-ws-spark-client/target/render-ws-spark-client-2.3.1-SNAPSHOT-standalone.jar",
    "className":"org.janelia.render.client.spark.SIFTPointMatchClient",
    "collection": "test2_mipmap_1",
    "pairJson": "/g/emcf/schorb/tile_pairs_test2_mipmap_z_442_to_450_dist_1.json",
    "SIFTfdSize": 8,
    "SIFTsteps": 3,
    "matchMaxEpsilon": 20.0,
    "maxFeatureCacheGb": 1,
    "SIFTminScale": 0.38,
    "SIFTmaxScale": 0.82,
    "renderScale": 0.3,
    "matchRod": 0.9,
    "matchMinInlierRatio": 0.0,
    "matchMinNumInliers": 8,
    "matchMaxNumInliers": 200
}


def get_host_port_dict_from_url(url):
    p = urlparse(url)
    return {'host': '{}://{}'.format(p.scheme, p.hostname),
            'port': p.port}

class PointMatchClientModuleSlurmSpark(SlurmSparkModule):
    default_schema = PointMatchClientParametersSlurmSpark
    default_output_schema = PointMatchClientOutputSchema

    @classmethod
    def get_pointmatch_args(cls, baseDataUrl=None, owner=None,
                            collection=None, pairJson=None, SIFTfdSize=None,
                            SIFTminScale=None, SIFTmaxScale=None,
                            SIFTsteps=None, matchRod=None,
                            matchModelType=None, matchIterations=None,
                            matchMaxEpsilon=None, matchMinInlierRatio=None,
                            matchMinNumInliers=None, matchMaxNumInliers=None,
                            matchMaxTrust=None, maxFeatureCacheGb=None,
                            clipWidth=None, clipHeight=None, renderScale=None,
                            renderWithFilter=None, renderWithoutMask=None,
                            renderFullScaleWidth=None,
                            renderFullScaleHeight=None, fillWithNoise=None,
                            rootFeatureDirectory=None,
                            renderFilterListName=None,
                            requireStoredFeatures=None,
                            matchFilter=None,
                            **kwargs):
        get_cmd_opt = cls.get_cmd_opt
        cmd = (
            get_cmd_opt(baseDataUrl, '--baseDataUrl') +
            get_cmd_opt(owner, '--owner') +
            get_cmd_opt(collection, '--collection') +
            get_cmd_opt(pairJson, '--pairJson') +
            get_cmd_opt(SIFTfdSize, '--SIFTfdSize') +
            get_cmd_opt(SIFTminScale, '--SIFTminScale') +
            get_cmd_opt(SIFTmaxScale, '--SIFTmaxScale') +
            get_cmd_opt(SIFTsteps, '--SIFTsteps') +
            get_cmd_opt(matchRod, '--matchRod') +
            get_cmd_opt(matchModelType, '--matchModelType') +
            get_cmd_opt(matchIterations, '--matchIterations') +
            get_cmd_opt(matchMaxEpsilon, '--matchMaxEpsilon') +
            get_cmd_opt(matchFilter, '--matchFilter') +
            get_cmd_opt(matchMinInlierRatio, '--matchMinInlierRatio') +
            get_cmd_opt(matchMinNumInliers, '--matchMinNumInliers') +
            get_cmd_opt(matchMaxNumInliers, '--matchMaxNumInliers') +
            get_cmd_opt(matchMaxTrust, '--matchMaxTrust') +
            get_cmd_opt(maxFeatureCacheGb, '--maxFeatureCacheGb') +
            get_cmd_opt(clipWidth, '--clipWidth') +
            get_cmd_opt(clipHeight, '--clipHeight') +
            get_cmd_opt(renderScale, '--renderScale') +
            get_cmd_opt(renderWithFilter, '--renderWithFilter') +
            get_cmd_opt(renderWithoutMask, '--renderWithoutMask') +
            get_cmd_opt(renderFullScaleWidth, '--renderFullScaleWidth') +
            get_cmd_opt(renderFullScaleHeight, '--renderFullScaleHeight') +
            get_cmd_opt(fillWithNoise, '--fillWithNoise') +
            get_cmd_opt(renderFilterListName, '--renderFilterListName') +
            get_cmd_opt(rootFeatureDirectory, '--rootFeatureDirectory') +
            cls.get_flag_cmd(requireStoredFeatures, '--requireStoredFeatures'))
        return cmd

    @classmethod
    def get_args(cls, **kwargs):
        return cls.sanitize_cmd(cls.get_pointmatch_args(**kwargs))


    def run(self):
        r = self.run_spark_command()
      



if __name__ == "__main__":
    module = PointMatchClientModuleSlurmSpark(input_data=example)
    #module = PointMatchClientModuleSpark(schema_type=PointMatchClientParameters)
    module.run()
