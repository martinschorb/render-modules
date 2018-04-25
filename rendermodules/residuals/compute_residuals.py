import os
import sys
import numpy as np
import time
import renderapi
import json
import itertools as it
from functools import partial
import requests


def compute_residuals_within_group(render, stack, matchCollectionOwner, matchCollection, z, min_points=1):
    session = requests.session()
    # get the sectionID which is the group ID in point match collection
    groupId = render.run(renderapi.stack.get_sectionId_for_z, stack, z, session=session)

    # get matches within the group for this section
    allmatches = render.run(
                    renderapi.pointmatch.get_matches_within_group,
                    matchCollection,
                    groupId,
                    owner=matchCollectionOwner,
                    session=session)

    # get the tilespecs to extract the transformations
    tilespecs = render.run(renderapi.tilespec.get_tile_specs_from_z, stack, z, session=session)
    tforms = {ts.tileId:ts.tforms for ts in tilespecs}

    transformed_pts = np.zeros((1,2))
    tile_residuals = {key: np.empty((0,1)) for key in tforms.keys()}
    tile_rmse = {key: np.empty((0,1)) for key in tforms.keys()}
    pt_match_positions = {key: np.empty((0,2)) for key in tforms.keys()}

    statistics = {}
    for i, match in enumerate(allmatches):
        pts_p = np.array(match['matches']['p'])
        pts_q = np.array(match['matches']['q'])

        if pts_p.shape[1] < min_points:
            continue

        if ((match['pId'] in tforms.keys()) and (match['qId'] in tforms.keys())):
            t_p = (tforms[match['pId']])[-1].tform(pts_p.T)
            t_q = (tforms[match['qId']])[-1].tform(pts_q.T)

            # find the mean spatial location of the point matches
            # needed for seam detection
            positions = [[(a[0]+b[0])/2, (a[1]+b[1])/2] for a,b in zip(t_p, t_q)]

            # tile based residual
            all_pts = np.concatenate([t_p, t_q], axis=1)

            # sqrt of residuals (this divided by len(all_pts) before sqrt will give RMSE)
            res = np.sqrt(np.sum(np.power(all_pts[:,0:2]-all_pts[:,2:4],2),axis=1))
            rmse = np.sqrt((np.sum(np.power(all_pts[:,0:2]-all_pts[:,2:4],2),axis=1))/len(all_pts))

            tile_residuals[match['pId']] = np.append(tile_residuals[match['pId']], res)
            tile_rmse[match['pId']] = np.append(tile_rmse[match['pId']], rmse)
            pt_match_positions[match['pId']] = np.append(pt_match_positions[match['pId']], positions, axis=0)

    # remove empty entries from these dicts
    empty_keys = [k for k in tile_residuals if tile_residuals[k].size == 0]
    for k in empty_keys:
        tile_residuals.pop(k)
        tile_rmse.pop(k)
        pt_match_positions.pop(k)
    

    statistics['tile_rmse'] = tile_rmse
    statistics['z'] = z
    statistics['tile_residuals'] = tile_residuals
    statistics['pt_match_positions'] = pt_match_positions

    session.close()
    
    return statistics
