Point Matches
=================

## [create_tilepairs.py](create_tilepairs.py)<a name="tilepairs"></a>

Create pair-wise associations between neighboring tiles (in 2D or 3D).

input json:
```JSON
{
    "required": [        
        "stack",
        "output_dir"
    ],
    "type": "object",
    "properties": {
      "render": {
          "required": [
              "client_scripts",
              "host",
              "owner",
              "port",
              "project"
          ],
          "type": "object",
          "properties": {
              "project": {
                  "type": "string",
                  "description": "render default project"
              },
              "host": {
                  "type": "string",
                  "description": "render host"
              },
              "memGB": {
                  "default": "5G",
                  "type": "string",
                  "description": "string describing java heap memory (default 5G)"
              },
              "owner": {
                  "type": "string",
                  "description": "render default owner"
              },
              "port": {
                  "type": "integer",
                  "description": "render post integer",
                  "format": "int32"
              },
              "client_scripts": {
                  "type": "string",
                  "description": "path to render client scripts"
              }
          }
      },
      "stack": {
          "type": "string",
          "description": "input stack to which tilepairs need to be generated"
      },
      "baseStack": {
          "type": "string",
          "description":"Base stack"
      },
      "minZ": {
          "type": "integer",
          "description": "z min for generating tilepairs",
          "format": "int32"
      },
      "maxZ": {
          "type": "integer",
          "description": "z max for generating tilepairs",
          "format": "int32"
      },
      "xyNeighborFactor":{
        "type": "number",
        "default":0.9,
        "description":"Multiply this by max(width, height) of each tile to determine radius for locating neighbor tiles"
      },
      "zNeighborDistance": {
          "type": "integer",
          "default":2,
          "description":"Look for neighbor tiles with z values less than or equal to this distance from the current tile's z value"
      },
      "excludeCornerNeighbors": {
        "default": true,
        "type": "boolean",
        "description":"Exclude neighbor tiles whose center x and y is outside the source tile's x and y range respectively"
      },
      "excludeSameLayerNeighbors": {
        "default": false,
        "type": "boolean",
        "description": "Exclude neighbor tiles in the same layer (z) as the source tile"
      },
      "excludeCompletelyObscuredTiles": {
        "default": false,
        "type": "boolean",
        "description": "Exclude tiles that are completely obscured by reacquired tiles"
      },
      "output_dir": {
          "type": "string",
          "description":"Output directory path to save the tilepair json file"
      },
      "memGB": {
          "default": "6G",
          "type": "string",
          "description":"Memory for the java client to run"
      }
    }
  }
```


output json:
```JSON
{
    "required": [
        "tile_pair_file"
    ],
    "type": "object",
    "properties": {
        "tile_pair_file": {
          "type": "string",
          "description": "location of json file with tile pair inputs"
        }
    }
}

```


## [generate_point_matches_opencv.py](generate_point_matches_opencv.py)<a name="pm_opencv"></a>

Create pair-wise associations between neighboring tiles (in 2D or 3D).

input json:
<!-- ```JSON
{
    "required": [      
    ],
    "type": "object",
    "properties": { -->

```      


ndiv = Int(
      required=False,
      default=8,
      missing=8,
      description="one tile per tile pair subdivided into "
      "ndiv x ndiv for easier homography finding")
  matchMax = Int(
      required=False,
      default=1000,
      missing=1000,
      description="per tile pair limit, randomly "
      "chosen after SIFT and RANSAC")
  downsample_scale = Float(
      required=False,
      default=0.3,
      missing=0.3,
      description="passed to cv2.resize(fx=, fy=)")
  SIFT_nfeature = Int(
      required=False,
      default=20000,
      missing=20000,
      description="passed to cv2.xfeatures2d.SIFT_create(nfeatures=)")
  SIFT_noctave = Int(
      required=False,
      default=3,
      missing=3,
      description="passed to cv2.xfeatures2d.SIFT_create(nOctaveLayers=)")
  SIFT_sigma = Float(
      required=False,
      default=1.5,
      missing=1.5,
      description="passed to cv2.xfeatures2d.SIFT_create(sigma=)")
  RANSAC_outlier = Float(
      required=False,
      default=5.0,
      missing=5.0,
      description="passed to cv2."
      "findHomography(src, dst, cv2.RANSAC, outlier)")
  FLANN_ntree = Int(
      required=False,
      default=5,
      missing=5,
      description="passed to cv2.FlannBasedMatcher()")
  FLANN_ncheck = Int(
      required=False,
      default=50,
      missing=50,
      description="passed to cv2.FlannBasedMatcher()")
  ratio_of_dist = Float(
      required=False,
      default=0.7,
      missing=0.7,
      description="ratio in Lowe's ratio test")
  CLAHE_grid = Int(
      required=False,
      default=None,
      missing=None,
      description="tileGridSize for cv2 CLAHE")
  CLAHE_clip = Float(
      required=False,
      default=None,
      missing=None,
      description="clipLimit for cv2 CLAHE")
  pairJson = Str(
      required=False,
      description="full path of tilepair json")
  input_stack = Str(
      required=False,
      description="Name of raw input lens data stack")
  match_collection = Str(
      required=False,
      description="name of point match collection")
  ncpus = Int(
      required=False,
      default=-1,
      missing=-1,
      description="number of CPUs to use")
```

output:
```
collectionId = Nested(
          CollectionId,
          required=True,
          description="collection identifying details")
  pairCount = Int(
      required=True,
      description="number of tile pairs in collection")
```
