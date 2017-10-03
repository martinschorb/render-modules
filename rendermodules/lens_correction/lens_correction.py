#!/usr/bin/env python
import os
import subprocess
import tempfile
import shutil
from argschema import ArgSchema, ArgSchemaParser
from argschema.fields import Bool, Float, Int, Nested, Str, InputFile
from argschema.schemas import DefaultSchema
from rendermodules.module.render_module import (
    RenderModuleException, ArgSchemaModule)

example_input = {
    "manifest_path": "/allen/programs/celltypes/workgroups/em-connectomics/samk/lc_test_data/Wij_Set_594451332/594089217_594451332/_trackem_20170502174048_295434_5LC_0064_01_20170502174047_reference_0_.txt",
    "project_path": "/allen/programs/celltypes/workgroups/em-connectomics/samk/lc_test_data/Wij_Set_594451332/594089217_594451332/",
    "fiji_path": "/allen/programs/celltypes/workgroups/em-connectomics/samk/Fiji.app/ImageJ-linux64",
    "grid_size": 3,
    "heap_size": 20,
    "outfile": "test_LC.json",
    "processing_directory": None,
    "SIFT_params": {
        "initialSigma": 1.6,
        "steps": 3,
        "minOctaveSize": 800,
        "maxOctaveSize": 1200,
        "fdSize": 4,
        "fdBins": 8
    },
    "align_params": {
        "rod": 0.92,
        "maxEpsilon": 5.0,
        "minInlierRatio": 0.0,
        "minNumInliers": 5,
        "expectedModelIndex": 1,
        "multipleHypotheses": True,
        "rejectIdentity": True,
        "identityTolerance": 5.0,
        "tilesAreInPlace": True,
        "desiredModelIndex": 0,
        "regularize": False,
        "maxIterationsOptimize": 2000,
        "maxPlateauWidthOptimize": 200,
        "dimension": 5,
        "lambdaVal": 0.01,
        "clearTransform": True,
        "visualize": False
    }
}


class SIFTParameters(DefaultSchema):
    initialSigma = Float(
        required=True,
        description="initial sigma value for SIFT's gaussian blur, in pixels")
    steps = Int(
        required=True,
        description='steps per SIFT scale octave')
    minOctaveSize = Int(
        required=True,
        description='minimum image size used for SIFT octave, in pixels')
    maxOctaveSize = Int(
        required=True,
        description='maximum image size used for SIFT octave, in pixels')
    fdSize = Int(
        required=True,
        description='SIFT feature descriptor size')
    fdBins = Int(
        required=True,
        description='SIFT feature descriptor orientation bins')


class AlignmentParameters(DefaultSchema):
    rod = Float(
        required=True,
        description='ratio of distances for matching SIFT features')
    maxEpsilon = Float(
        required=True,
        description='maximum acceptable epsilon for RANSAC filtering')
    minInlierRatio = Float(
        required=True,
        description='minimum inlier ratio for RANSAC filtering')
    minNumInliers = Int(
        required=True,
        description='minimum number of inliers for RANSAC filtering')
    expectedModelIndex = Int(
        required=True,
        description=('expected model for RANSAC filtering, 0=Translation, '
                     '1="Rigid", 2="Similarity", 3="Affine"'))
    multipleHypotheses = Bool(
        required=True,
        description=('Utilize RANSAC filtering which allows '
                     'fitting multiple hypothesis models'))
    rejectIdentity = Bool(
        required=True,
        description=('Reject Identity model (constant background) '
                     'up to a tolerance defined by identityTolerance'))
    identityTolerance = Float(
        required=True,
        description='Tolerance to which Identity should rejected, in pixels')
    tilesAreInPlace = Bool(
        required=True,
        description=('Whether tile inputs to TrakEM2 are in place to be '
                     'compared only to neighboring tiles.'))
    desiredModelIndex = Int(
        required=True,
        description=('Affine homography model which optimization will '
                     'try to fit, 0="Translation", 1="Rigid", '
                     '2="Similarity", 3="Affine"'))
    # TODO no input for regularizer model, defaults to Rigid regularization
    regularize = Bool(
        required=True,
        description=('Whether to regularize the desired model with '
                     'the regularizer model by lambda'))
    maxIterationsOptimize = Int(
        required=True,
        description='Max number of iterations for optimizer')
    maxPlateauWidthOptimize = Int(
        required=True,
        description='Maximum plateau width for optimizer')
    dimension = Int(
        required=True,
        description=('Dimension of polynomial kernel to fit '
                     'for distortion model'))
    lambdaVal = Float(
        required=True,
        description=('Lambda parameter by which the regularizer model '
                     'affects fitting of the desired model'))
    clearTransform = Bool(
        required=True,
        description=('Whether to remove transforms from tiles '
                     'before SIFT matching.  Not recommended'))
    visualize = Bool(
        required=True,
        description=('Whether to have TrakEM2 visualize the lens '
                     'correction transform.  Not recommended when '
                     'running through xvfb'))


class LensCorrectionParameters(ArgSchema):
    manifest_path = InputFile(
        required=True,
        description='path to manifest file')
    project_path = Str(
        required=True,
        description='path to project directory')
    fiji_path = InputFile(
        required=True,
        description='path to FIJI')
    grid_size = Int(
        required=True,
        description=('maximum row and column to form square '
                     'subset of tiles starting from zero (based on filenames '
                     'which end in "\{row\}_\{column\}.tif")'))
    heap_size = Int(
        required=False,
        default=20,
        description="memory in GB to allocate to Java heap")
    outfile = Str(
        required=False,
        description=("File to which json output of lens correction "
                     "(leaf TransformSpec) is written"))
    processing_directory = Str(
        required=False,
        allow_none=True,
        description=("directory to which trakem2 processing "
                     "directory will be written "
                     "(will place in project_path directory if "
                     "unspecified or create temporary directory if None)"))
    SIFT_params = Nested(SIFTParameters)
    align_params = Nested(AlignmentParameters)


class LensCorrectionOutput(DefaultSchema):
    # TODO probably easier to output the resulting file via python
    output_json = Str(required=True,
                      description='path to file ')


class LensCorrectionException(RenderModuleException):
    pass


class LensCorrectionModule(ArgSchemaParser):
    default_schema = LensCorrectionParameters
    default_output_schema = LensCorrectionOutput

    bsh_basename = 'run_lens_correction.bsh'

    @property
    def default_bsh(self):
        bsh = os.path.join(
            os.path.dirname(__file__), self.bsh_basename)
        if not os.path.isfile(bsh):
            raise LensCorrectionException(
                'beanshell file {} does not exist'.format(bsh))
        elif not os.access(bsh, os.R_OK):
            raise LensCorrectionException(
                "beanshell file {} is not readable".format(bsh))
        return bsh

    def run(self, run_lc_bsh=None):
        run_lc_bsh = self.default_bsh if run_lc_bsh is None else run_lc_bsh
        outfn = self.args.get('outfile', os.path.abspath(os.path.join(
            self.args['project_path'], 'lens_correction.json')))

        delete_procdir = False
        procdir = self.args.get('processing_directory',
                                self.args['project_path'])
        if procdir is None:
            delete_procdir = True
            procdir = tempfile.mkdtemp()

        # command line argument for beanshell script
        bsh_call = [
            "xvfb-run",
            "-a",
            self.args['fiji_path'],
            "-Xms{}g".format(self.args['heap_size']),
            "-Xmx{}g".format(self.args['heap_size']), "-Xincgc",
            "-Dman=" + self.args['manifest_path'],
            "-Ddir=" + self.args['project_path'],
            "-Dgrid=" + str(self.args['grid_size']),
            "-Disig=" + str(self.args['SIFT_params']['initialSigma']),
            "-Dsteps=" + str(self.args['SIFT_params']['steps']),
            "-Dminos=" + str(self.args['SIFT_params']['minOctaveSize']),
            "-Dmaxos=" + str(self.args['SIFT_params']['maxOctaveSize']),
            "-Dfdsize=" + str(self.args['SIFT_params']['fdSize']),
            "-Dfdbins=" + str(self.args['SIFT_params']['fdBins']),
            "-Drod=" + str(self.args['align_params']['rod']),
            "-Dmaxe=" + str(self.args['align_params']['maxEpsilon']),
            "-Dmir=" + str(self.args['align_params']['minInlierRatio']),
            "-Dmni=" + str(self.args['align_params']['minNumInliers']),
            "-Demi=" + str(self.args['align_params']['expectedModelIndex']),
            "-Dmh=" + str(self.args['align_params']['multipleHypotheses']),
            "-Dri=" + str(self.args['align_params']['rejectIdentity']),
            "-Dit=" + str(self.args['align_params']['identityTolerance']),
            "-Dtaip=" + str(self.args['align_params']['tilesAreInPlace']),
            "-Ddmi=" + str(self.args['align_params']['desiredModelIndex']),
            "-Dreg=" + str(self.args['align_params']['regularize']),
            "-Dmio={}".format(
                self.args['align_params']['maxIterationsOptimize']),
            "-Dmpwo={}".format(
                self.args['align_params']['maxPlateauWidthOptimize']),
            "-Ddim=" + str(self.args['align_params']['dimension']),
            "-Dlam=" + str(self.args['align_params']['lambdaVal']),
            "-Dprocdir={}".format(procdir),
            "-Doutfn={}".format(outfn),
            "-Dctrans=" + str(self.args['align_params']['clearTransform']),
            "-Dvis=" + str(self.args['align_params']['visualize']),
            "--", "--no-splash",
            run_lc_bsh]

        ret=subprocess.call(bsh_call)
        self.logger.debug('bsh_cmd: {}'.format(bsh_call))
        self.logger.debug('ret_code: {}'.format(ret))
        
        if delete_procdir:
            shutil.rmtree(procdir)

        try:
            self.output({'output_json': outfn})
        except AttributeError as e:
            # output validation will need to wait for argschema PR
            self.logger.error(e)


if __name__ == '__main__':
    module = LensCorrectionModule(input_data=example_input)
    module.run()