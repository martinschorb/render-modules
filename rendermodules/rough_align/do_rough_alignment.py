import json
import os
import renderapi
from ..module.render_module import RenderModule
from rendermodules.rough_align.schemas import SolveRoughAlignmentParameters
from marshmallow import ValidationError
from functools import partial
import numpy as np
import tempfile


if __name__ == "__main__" and __package__ is None:
    __package__ = "rendermodules.rough_align.do_rough_alignment"


example = {
    "render": {
        "host": "http://em-131fs",
        "port": 8080,
        "owner": "gayathri",
        "project": "MM2",
        "client_scripts": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/render_latest/render-ws-java-client/src/main/scripts"
    },
    "input_lowres_stack": {
        "stack": "mm2_acquire_8bit_reimage_postVOXA_TEMCA2_DS_Montage",
        "owner": "gayathri",
        "project": "MM2"
    },
    "output_lowres_stack": {
        "stack": "mm2_acquire_8bit_reimage_postVOXA_TEMCA2_DS_Rough_Scaled",
        "owner": "gayathri",
        "project": "MM2"
    },
    "point_match_collection": {
        "owner": "gayathri_MM2",
        "match_collection": "mm2_acquire_8bit_reimage_postVOXA_TEMCA2_Rough",
        "scale": 1.0
    },
    "solver_options": {
        "min_tiles": 20,
        "degree": 1,
        "outlier_lambda": 100,
        "solver": "backslash",
        "matrix_only": 0,
        "distribute_A": 1,
        "dir_scratch": "/allen/aibs/pipeline/image_processing/volume_assembly/scratch",
        "min_points": 20,
        "max_points": 100,
        "nbrs": 3,
        "xs_weight": 1,
        "stvec_flag": 1,
        "distributed": 0,
        "lambda_value": 1000,
        "edge_lambda": 1000,
        "use_peg": 0,
        "complete": 1,
        "disableValidation": 1,
        "apply_scaling": 1,
        "scale_fac": 1.0,
        "translation_only": 0,
        "translate_to_origin": 1,
        "verbose": 0,
        "debug": 0
    },
    "solver_executable":"/allen/aibs/pipeline/image_processing/volume_assembly/EM_aligner/matlab_compiled/do_rough_alignment",
    "minz": 1021,
    "maxz": 1100
}

'''
example = {
    "render": {
        "host": "http://ibs-forrestc-ux1",
        "port": 8080,
        "owner": "1_ribbon_expts",
        "project": "M335503_RIC4_Ai139_LRW",
        "client_scripts": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/render_20170613/render-ws-java-client/src/main/scripts"
    },
    "input_lowres_stack": {
        "stack": "TESTGAYATHRI_DownsampledDAPI",
        "owner": "1_ribbon_expts",
        "project": "M335503_RIC4_Ai139_LRW"
    },
    "output_lowres_stack": {
        "stack": "TESTGAYATHRI_Stitched_DAPI_1_Lowres_RoughAligned",
        "owner": "1_ribbon_expts",
        "project": "M335503_RIC4_Ai139_LRW"
    },
    "point_match_collection": {
        "owner": "1_ribbon_expts",
        "match_collection": "M335503_RIC4_Ai139_LRW_DAPI_1_lowres_round1",
        "scale": 1.0
    },
    "solver_options": {
        "min_tiles": 5,
        "degree": 1,
        "outlier_lambda": 100,
        "solver": "backslash",
        "matrix_only": 0,
        "distribute_A": 1,
        "dir_scratch": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/scratch",
        "min_points": 20,
        "max_points": 100,
        "nbrs": 10,
        "xs_weight": 0.5,
        "stvec_flag": 1,
        "distributed": 0,
        "lambda_value": 1000,
        "edge_lambda": 1000,
        "use_peg": 0,
        "complete": 1,
        "disableValidation": 1,
        "apply_scaling": 1,
        "scale_fac": 20.0,
        "translation_only": 0,
        "translate_to_origin": 1,
        "verbose": 1,
        "debug": 0
    },
    "solver_executable":"/allen/aibs/shared/image_processing/volume_assembly/EM_aligner/matlab_compiled/do_rough_alignment",
    "minz": 0,
    "maxz": 15
}
'''


class SolveRoughAlignmentModule(RenderModule):
    def __init__(self, schema_type=None, *args, **kwargs):
        if schema_type is None:
            schema_type = SolveRoughAlignmentParameters
        super(SolveRoughAlignmentModule, self).__init__(
            schema_type=schema_type,
            *args,
            **kwargs)

        # Khaled's solver doesn't like extra parameters in the input json file
        # Assigning the solver_executable to a different variable and removing it from args
        self.solver_executable = self.args['solver_executable']
        self.args.pop('solver_executable', None)

    def run(self):
        # generate a temporary json to feed in to the solver
        tempjson = tempfile.NamedTemporaryFile(
            suffix=".json",
            mode="w",
            delete=False)
        tempjson.close()

        with open(tempjson.name, 'w') as f:
            json.dump(self.args, f, indent=4)
            f.close()

        # create the command to run
        # this code assumes that matlab environment is setup in the server for the user
        # add this to your profile
        # Note that MCRROOT is the matlab compiler runtime's root folder
        '''
            LD_LIBRARY_PATH=.:${MCRROOT}/runtime/glnxa64 ;
            LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/bin/glnxa64 ;
            LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/sys/os/glnxa64;
            LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/sys/opengl/lib/glnxa64;
        '''

        if "MCRROOT" not in os.environ:
            raise ValidationError("MCRROOT not set")

        env = os.environ.get('LD_LIBRARY_PATH')
        mcrroot = os.environ.get('MCRROOT')
        path1 = os.path.join(mcrroot, 'runtime/glnxa64')
        path2 = os.path.join(mcrroot, 'bin/glnxa64')
        path3 = os.path.join(mcrroot, 'sys/os/glnxa64')
        path4 = os.path.join(mcrroot, 'sys/opengl/lib/glnxa64')

        if path1 not in env:
            os.environ['LD_LIBRARY_PATH'] += os.pathsep + path1
        if path2 not in env:
            os.environ['LD_LIBRARY_PATH'] += os.pathsep + path2
        if path3 not in env:
            os.environ['LD_LIBRARY_PATH'] += os.pathsep + path3
        if path4 not in env:
            os.environ['LD_LIBRARY_PATH'] += os.pathsep + path4


        cmd = "%s %s"%(self.solver_executable, tempjson.name)
        os.system(cmd)

        '''
        if os.path.isfile(self.solver_executable) and os.access(self.solver_executable, os.X_OK):
            cmd_to_qsub = "%s %s"%(self.solver_executable, tempjson.name)

        #generate pbs file
            temppbs = tempfile.NamedTemporaryFile(
                suffix=".pbs",
                mode="w",
                delete=False)
            temppbs.close()

            with open(temppbs.name, 'w') as f:
                f.write('#PBS -l mem=60g\n')
                f.write('#PBS -l walltime=00:00:20\n')
                f.write('#PBS -l ncpus=1\n')
                f.write('#PBS -N Montage\n')
                f.write('#PBS -r n\n')
                f.write('#PBS -m n\n')
                f.write('#PBS -q emconnectome\n')
                f.write('%s\n'%(cmd_to_qsub))
            f.close()

            qsub_cmd = 'qsub %s'%(temppbs.name)
            subprocess.call(qsub_cmd)
        '''

if __name__ == "__main__":
    mod = SolveRoughAlignmentModule(input_data=example)
    #module = SolveRoughAlignmentModule(schema_type=SolveMontageSectionParameters)
    mod.run()
