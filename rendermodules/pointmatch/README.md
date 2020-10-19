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
