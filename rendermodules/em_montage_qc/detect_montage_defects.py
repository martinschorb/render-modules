from functools import partial
from rtree import index as rindex
from scipy.spatial import cKDTree
import networkx as nx
import numpy as np
import renderapi
import time
import requests
from six import viewkeys
from rendermodules.residuals import compute_residuals as cr
from rendermodules.em_montage_qc.schemas import DetectMontageDefectsParameters, DetectMontageDefectsParametersOutput
from ..module.render_module import RenderModule, RenderModuleException
from rendermodules.em_montage_qc.plots import plot_section_maps


example = {
    "render":{
        "host": "http://em-131fs",
        "port": 8080,
        "owner": "danielk",
        "project": "Seams",
        "client_scripts": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/render_latest/render-ws-java-client/src/main/scripts"
    },
    "prestitched_stack": "2_sections_near_crack_fine_lam_1e3",
    "poststitched_stack": "2_sections_near_crack_fine_lam_1e3_omitted_auto",
    "match_collection": "NewPMS_combined_with_montage",
    "out_html_dir":"/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/scratch",
    "plot_sections":"True",
    "minZ": 1028,
    "maxZ": 1029,
    "pool_size": 20
}

'''
example = {
    "render":{
        "host": "http://em-131db",
        "port": 8080,
        "owner": "TEM",
        "project": "247488_8R",
        "client_scripts": "/allen/programs/celltypes/workgroups/em-connectomics/gayathrim/nc-em2/Janelia_Pipeline/render_latest/render-ws-java-client/src/main/scripts"
    },
    "prestitched_stack": "em_2d_montage_lc",
    "poststitched_stack": "em_2d_montage_solved_TEMCA2_1222_1260",
    "match_collection_owner": "TEM",
    "match_collection": "default_point_matches",
    "minZ": 1242,
    "maxZ": 1244,
    "residual_threshold":6,
    "neighbor_distance": 50,
    "min_cluster_size":20,
    "pool_size": 10
}
'''

def detect_seams(render, stack, match_collection, match_owner, z, residual_threshold=8, distance=60, min_cluster_size=15, tspecs=None):
    # seams will always be computed for montages using montage point matches
    # but the input stack can be either montage, rough, or fine
    # Compute residuals and other stats for this z
    stats = cr.compute_residuals_within_group(render, stack, match_owner, match_collection, z, tilespecs=tspecs)

    # get mean positions of the point matches as numpy array
    pt_match_positions = np.concatenate(stats['pt_match_positions'].values(), 0)
    # get the tile residuals
    tile_residuals = np.concatenate(stats['tile_residuals'].values())

    # threshold the points based on residuals
    new_pts = pt_match_positions[np.where(tile_residuals >= residual_threshold),:][0]

    # construct a KD Tree using these points
    tree = cKDTree(new_pts)
    # construct a networkx graph
    G = nx.Graph()
    # find the pairs of points within a distance to each other
    pairs = tree.query_pairs(r=distance)
    G.add_edges_from(pairs)
    # get the connected subraphs from G
    #Gc = nx.connected_component_subgraphs(G)
    Gc = nx.connected_components(G)
    # get the list of nodes in each component
    nodes = sorted(Gc, key=len, reverse=True)
    # filter nodes list with min_cluster_size
    fnodes = [list(nn) for nn in nodes if len(nn) > min_cluster_size]
    # get pts list for each filtered node list
    points_list = [new_pts[mm, :] for mm in fnodes]
    centroids = [[np.sum(pt[:,0])/len(pt), np.sum(pt[:,1])/len(pt)] for pt in points_list]
    return centroids

'''
def detect_seams_old(render, stack, match_collection, match_owner, z, residual_threshold=4, distance=60, min_cluster_size=7):
    # seams will always be computed for montages using montage point matches
    # but the input stack can be either montage, rough, or fine
    # Compute residuals and other stats for this z
    stats = cr.compute_residuals_within_group(render, stack, match_owner, match_collection, z)
    print(z)
    # get mean positions of the point matches as numpy array
    pt_match_positions = np.empty((0,2))
    for p in stats['pt_match_positions']:
        pt_match_positions = np.append(pt_match_positions, stats['pt_match_positions'][p], axis=0)
    # get the tile residuals
    tile_residuals = np.empty((0,1))
    for t in stats['tile_residuals']:
        tile_residuals = np.append(tile_residuals, stats['tile_residuals'][t])
    # threshold the points based on residuals
    new_pts = []
    new_residuals = []
    for p, tr in zip(pt_match_positions, tile_residuals):
        if tr >= residual_threshold:
            new_pts.append(p)

    new_pts = np.array(new_pts)
    # construct a KD Tree using these points
    tree = KDTree(new_pts)
    # construct a networkx graph
    G = nx.Graph()

    # iterate through each point to get its nearest neighbors within a distance
    for m, npt in enumerate(new_pts):
        idx = tree.query_ball_point(npt, r=distance)

        # add edge to G for each neighbor
        [G.add_edge(m, id) for id in idx]
    # get the connected subraphs from G
    # this is slower instead use nx.connected_components
    #Gc = nx.connected_component_subgraphs(G)
    Gc = sorted(nx.connected_components(G), key=len, reverse=True)
    Gs = [s for s in Gc if len(s) > min_cluster_size]
    # find the clusters that have more than specified number of nodes
    centroids = []
    for s in Gs:
        #if len(s.nodes()) > min_cluster_size:
        pts = new_pts[list(s),:]
        # get the centroid of these points that give the approximate location of the seam
        x_pts = pts[:,0]
        y_pts = pts[:,1]
        centroids.append([np.sum(x_pts)/len(pts), np.sum(y_pts)/len(pts)])

    return centroids
'''


def detect_disconnected_tiles(render, prestitched_stack, poststitched_stack,
                              z, pre_tilespecs=None, post_tilespecs=None):
    session = requests.session()
    # get the tilespecs for both prestitched_stack and poststitched_stack

    if pre_tilespecs is None:
        pre_tilespecs = render.run(
                            renderapi.tilespec.get_tile_specs_from_z,
                            prestitched_stack,
                            z,
                            session=session)
    if post_tilespecs is None:
        post_tilespecs = render.run(
                            renderapi.tilespec.get_tile_specs_from_z,
                            poststitched_stack,
                            z,
                            session=session)
    # pre tile_ids
    pre_tileIds = []
    pre_tileIds = [ts.tileId for ts in pre_tilespecs]
    # post tile_ids
    post_tileIds = []
    post_tileIds = [ts.tileId for ts in post_tilespecs]
    missing_tileIds = list(set(pre_tileIds) - set(post_tileIds))
    session.close()
    return missing_tileIds


def detect_stitching_gaps(render, prestitched_stack, poststitched_stack,
                          z, pre_tilespecs=None, tilespecs=None):
    session = requests.session()
    # setup an rtree to find overlapping tiles
    pre_ridx = rindex.Index()
    # setup a graph to store overlapping tiles
    G1 = nx.Graph()
    # get the tilespecs for both prestitched_stack and poststitched_stack
    if pre_tilespecs is None:
        pre_tilespecs = render.run(
                            renderapi.tilespec.get_tile_specs_from_z,
                            prestitched_stack,
                            z,
                            session=session)
    if tilespecs is None:
        tilespecs = render.run(
                            renderapi.tilespec.get_tile_specs_from_z,
                            poststitched_stack,
                            z,
                            session=session)
    # insert the prestitched_tilespecs into rtree with their bounding boxes to find overlaps
    for i, ts in enumerate(pre_tilespecs):
        pre_ridx.insert(i, ts.bbox)

    pre_tileIds = {}
    for i, ts in enumerate(pre_tilespecs):
        pre_tileIds[ts.tileId] = i
        nodes = list(pre_ridx.intersection(ts.bbox))
        nodes.remove(i)
        [G1.add_edge(i, node) for node in nodes]
    # G1 contains the prestitched_stack tile)s and the degree of each node representing
    # the number of tiles that overlap
    # This overlap count has to match in the poststitched_stack
    G2 = nx.Graph()
    post_ridx = rindex.Index()
    tileId_to_ts = {ts.tileId: ts for ts in tilespecs}
    shared_tileIds = viewkeys(tileId_to_ts) & viewkeys(pre_tileIds)
    [post_ridx.insert(pre_tileIds[tId], tileId_to_ts[tId].bbox) for tId in shared_tileIds]
    for ts in tilespecs:
        try:
            i = pre_tileIds[ts.tileId]
        except KeyError:
            continue
        # i = pre_tileIds[ts.tileId]
        nodes = list(post_ridx.intersection(ts.bbox))
        nodes.remove(i)
        [G2.add_edge(i, node) for node in nodes]
    # Now G1 and G2 have the same index for the same tileId
    # comparing the degree of each node pre and post stitching should reveal stitching gaps
    #tileIds = nx.get_node_attributes(G2, 'tileId')
    gap_tiles = []
    for n in G2.nodes():
        if G1.degree(n) > G2.degree(n):
            tileId = pre_tileIds.keys()[pre_tileIds.values().index(n)]
            gap_tiles.append(tileId)
    session.close()
    return gap_tiles


def get_pre_post_tspecs(render, prestitched_stack, poststitched_stack, z):
    session = requests.session()
    pre_tilespecs = render.run(
                        renderapi.tilespec.get_tile_specs_from_z,
                        prestitched_stack,
                        z,
                        session=session)
    post_tilespecs = render.run(
                        renderapi.tilespec.get_tile_specs_from_z,
                        poststitched_stack,
                        z,
                        session=session)
    session.close()
    return pre_tilespecs, post_tilespecs


def run_analysis(render, prestitched_stack, poststitched_stack, match_collection,
                 match_collection_owner, residual_threshold, neighbor_distance,
                 min_cluster_size, z):
    pre_tspecs, post_tspecs = get_pre_post_tspecs(
        render, prestitched_stack, poststitched_stack, z)
    disconnected_tiles = detect_disconnected_tiles(
        render, prestitched_stack, poststitched_stack, z, pre_tspecs,
        post_tspecs)
    gap_tiles = detect_stitching_gaps(
        render, prestitched_stack, poststitched_stack, z,
        pre_tspecs, post_tspecs)
    seam_centroids = detect_seams(
        render, poststitched_stack,  match_collection, match_collection_owner,
        z, residual_threshold=residual_threshold, distance=neighbor_distance,
        min_cluster_size=min_cluster_size, tspecs=post_tspecs)

    return disconnected_tiles, gap_tiles, seam_centroids


def detect_stitching_mistakes(render, prestitched_stack, poststitched_stack, match_collection, match_collection_owner, residual_threshold, neighbor_distance, min_cluster_size, zvalues, pool_size=20):
    mypartial0 = partial(
        run_analysis, render, prestitched_stack, poststitched_stack,
        match_collection, match_collection_owner, residual_threshold,
        neighbor_distance, min_cluster_size)
    # mypartial1 = partial(detect_disconnected_tiles,
    #                      render,
    #                      prestitched_stack,
    #                      poststitched_stack)
    # mypartial2 = partial(detect_stitching_gaps,
    #                      render,
    #                      prestitched_stack,
    #                      poststitched_stack)
    # mypartial3 = partial(detect_seams,
    #                      render,
    #                      poststitched_stack,
    #                      match_collection,
    #                      match_collection_owner,
    #                      residual_threshold=residual_threshold,
    #                      distance=neighbor_distance,
    #                      min_cluster_size=min_cluster_size)

    with renderapi.client.WithPool(pool_size) as pool:
        disconnected_tiles, gap_tiles, seam_centroids = zip(*pool.map(
            mypartial0, zvalues))
        # disconnected_tiles = pool.map(mypartial1, zvalues)
        # gap_tiles = pool.map(mypartial2, zvalues)
        # seam_centroids = pool.map(mypartial3, zvalues)
    #for z in zvalues:
    #    disconnected_tiles.append(detect_disconnected_tiles(render, prestitched_stack, poststitched_stack, z))
    #    gap_tiles.append(detect_stitching_gaps(render, prestitched_stack, poststitched_stack, z))
    #    seam_centroids.append(detect_seams(render, poststitched_stack, match_collection, match_collection_owner, z, distance=80))
    return disconnected_tiles, gap_tiles, seam_centroids


def check_status_of_stack(render, stack, zvalues):
    status = render.run(renderapi.stack.get_full_stack_metadata,
                        stack)
    new_stack = stack

    #if (status['state'].find('LOADING') >= 0):
    if status['state'] == 'LOADING':
        # clone the stack
        new_stack = "{}_zs{}_ze{}_t{}".format(stack,
                                           min(zvalues),
                                           max(zvalues),
                                           time.strftime("%m%d%y_%H%M%S"))
        renderapi.stack.clone_stack(stack,
                                    new_stack,
                                    zs=zvalues,
                                    render=render)

    return status['state'], new_stack


class DetectMontageDefectsModule(RenderModule):
    default_output_schema = DetectMontageDefectsParametersOutput
    default_schema = DetectMontageDefectsParameters
    def run(self):
        zvalues1 = self.render.run(renderapi.stack.get_z_values_for_stack,
                                self.args['poststitched_stack'])
        zrange = range(self.args['minZ'], self.args['maxZ']+1)
        zvalues = list(set(zvalues1).intersection(set(zrange)))
        if len(zvalues) == 0:
            raise RenderModuleException('No valid zvalues found in stack for given range {} - {}'.format(self.args['minZ'], self.args['maxZ']))

        # check if pre or post stitched stack is in LOADING state.
        # if so, clone them to new stacks
        status1, new_prestitched = check_status_of_stack(self.render,
                                                self.args['prestitched_stack'],
                                                zvalues)

        status2, new_poststitched = check_status_of_stack(self.render,
                                                 self.args['poststitched_stack'],
                                                 zvalues)
        disconnected_tiles, gap_tiles, seam_centroids = detect_stitching_mistakes(
                                                            self.render,
                                                            new_prestitched,
                                                            new_poststitched,
                                                            self.args['match_collection'],
                                                            self.args['match_collection_owner'],
                                                            self.args['residual_threshold'],
                                                            self.args['neighbors_distance'],
                                                            self.args['min_cluster_size'],
                                                            zvalues,
                                                            pool_size=self.args['pool_size'])
        #holes = [z for (z, dt) in zip(zvalues, disconnected_tiles) if len(dt) > 0]
        #gaps = [z for (z, gt) in zip(zvalues, gap_tiles) if len(gt) > 0]
        #seams = [z for (z,sm) in zip(zvalues, seam_centroids) if len(sm) > 0]
        # find the indices of sections having holes
        hole_indices = [i for i, dt in enumerate(disconnected_tiles) if len(dt) > 0]
        gaps_indices = [i for i, gt in enumerate(gap_tiles) if len(gt) > 0]
        seams_indices = [i for i, sm in enumerate(seam_centroids) if len(sm) > 0]
        holes = [zvalues[i] for i in hole_indices]
        gaps = [zvalues[i] for i in gaps_indices]
        seams = [zvalues[i] for i in seams_indices]
        combinedz = list(set(holes + gaps + seams))
        qc_passed_sections = set(zvalues) - set(combinedz)
        centroids = [seam_centroids[i] for i in seams_indices]

        self.args['output_html'] = self.args['out_html_dir']
        if len(combinedz) > 0:
            if self.args['plot_sections']:
                self.args['output_html'] = plot_section_maps(self.render, new_poststitched, combinedz, out_html_dir=self.args['output_html'])

        self.output({'output_html':self.args['output_html'],
                     'qc_passed_sections': qc_passed_sections,
                     'hole_sections': holes,
                     'gap_sections':gaps,
                     'seam_sections':seams,
                     'seam_centroids':np.array(centroids)})
        # delete the stacks that were cloned
        #if status1.find('LOADING') >= 0:
        if status1 == 'LOADING':
            self.render.run(renderapi.stack.delete_stack, new_prestitched)

        #if status2.find('LOADING') >= 0:
        if status2 == 'LOADING':
            self.render.run(renderapi.stack.delete_stack, new_poststitched)
if __name__ == "__main__":
    mod = DetectMontageDefectsModule(input_data=example)
    mod.run()
