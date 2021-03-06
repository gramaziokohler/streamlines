import compas.geometry as cg

from time import time
from functools import partial

from compas.geometry import scale_vector
from compas.geometry import add_vectors
from compas.geometry import normalize_vector
from compas.geometry import length_vector


def vector_lines_on_faces(mesh, vector_tag, uniform=True, factor=0.02):
    '''
    '''
    def line_sdl(start, direction, length):
        direction = normalize_vector(direction[:])
        a = add_vectors(start, scale_vector(direction, -length))
        b = add_vectors(start, scale_vector(direction, +length))

        return a, b

    lines = []
    for fkey, attr in mesh.faces(data=True):
        vector = attr.get(vector_tag)

        if not vector:
            raise ValueError('Vector {} not defined on face {}'.format(vector_tag, fkey))

        if uniform:
            vec_length = factor
        else:
            vec_length = length_vector(vector) * factor

        pt = mesh.face_centroid(fkey)
        lines.append(line_sdl(pt, vector, vec_length))
    return lines


def line_tuple_to_dict(line):
    '''
    '''
    a, b = line
    return {'start': a, 'end': b}


if __name__ == '__main__':

    from compas.datastructures import Mesh
    from compas.datastructures import mesh_unify_cycles

    from compas.utilities import i_to_rgb

    from compas_plotters import MeshPlotter

    from streamlines.custom_mesh import StructuralMesh

    from streamlines.kmeans import make_faces
    from streamlines.kmeans import furthest_init
    from streamlines.kmeans import k_means

    from streamlines.utilities import Utilities

    ut = Utilities()

    # ==========================================================================
    # Constants
    # ==========================================================================

    HERE = '/Users/arpj/code/libraries/streamlines/examples/four_point_slab.json'

    tags = [
        'n_1',
        'n_2',
        'm_1',
        'm_2',
        'ps_1_top',
        'ps_1_bot',
        'ps_1_mid',
        'ps_2_top',
        'ps_2_bot',
        'ps_2_mid',
        'custom_1',
        'custom_2'
        ]

    # (odd numbers only!) (after 11, starts to get confused!) but at 19, kind of works again
    
    # THERE = '/Users/arpj/code/libraries/streamlines/examples/gif_{0}_{1}/kmeans_{0}_{1}_'
    # THERE = THERE.format(NUM, ITERS)
    # EXPORT_PNG = False

    # ==========================================================================
    # Import mesh
    # ==========================================================================

    mesh = Mesh()
    mesh.load(HERE)
    mesh_unify_cycles(mesh)

    # ==========================================================================
    # Create PS vector lines
    # ==========================================================================

    vector_tag = 'ps_1_top'
    lines = vector_lines_on_faces(mesh, vector_tag, True, factor=0.05)

    lines = [line for line in map(line_tuple_to_dict, lines)]
    for line in lines:
        line['width'] = 0.60

    # ==========================================================================
    # Instantiate StructuralMesh()
    # ==========================================================================

    str_mesh = StructuralMesh(mesh)

    for tag in tags:
        vector_field = mesh.get_faces_attribute(keys=list(mesh.faces()), name=tag)
        str_mesh.set_face_vectors(vector_field, tag, normalize=True)
        str_mesh.set_vertex_vectors_angles(tag)

    # ==========================================================================
    # Define Callback
    # ==========================================================================

    # def callback(k, plotter, clusters, filepath, export):
    #     num = len(list(clusters.keys()))

    #     facedict = {}

    #     for idx, cluster in clusters.items():
    #         color = [i / 255 for i in i_to_rgb(idx / num)]
    #         for fkey in cluster.faces_keys:
    #             facedict[fkey] = color

    #     facecolors = sorted(facedict.items(),  key=lambda x: x[0])
    #     facecolors = [x[1] for x in facecolors]
    #     plotter.facecollection.set_facecolors(facecolors)

    #     if export:
    #         plotter.save(THERE + '{}_{}.png'.format(time(), k))
    #     plotter.update(pause=0.50)

    # ==========================================================================
    # Set up Plotter
    # ==========================================================================

    # plotter = MeshPlotter(mesh, figsize=(12, 9))
    # plotter.draw_lines(lines)
    # plotter.draw_faces()
    # plotter.update(pause=0.5)

    # callback = partial(callback, plotter=plotter, filepath=THERE, export=EXPORT_PNG)

    # ==========================================================================
    # Set up K-Means algorithm
    # ==========================================================================


    # define loss file
    errors = []

    # NUM = 5  # number of clusters 
    TEST_RANGE = 100
    ITERS = 30  # number of iterations
    MERGESPLIT = False  # merge split in k means. True is good for this example, but not for knitcandela!

    for num in range(1, TEST_RANGE):
        print('num clusters: ', num)
    
        faces = make_faces(str_mesh, vector_tag, weight=False)
        clusters = furthest_init(num, faces)
    
        sel_clusters = clusters[-1]
        all_clusters = k_means(sel_clusters, faces, ITERS, MERGESPLIT)
        final_clusters = all_clusters[-1]


        error = 0.0
        for idx, cluster in final_clusters.items():
            proxy = normalize_vector(cluster.proxy)
            fkeys = cluster.faces_keys

            for fkey in fkeys:
                vector = str_mesh.cMesh.get_face_attribute(fkey, vector_tag)
                vector = normalize_vector(vector)
                ali_vec = ut.align_vector(vector, proxy)
                difference = cg.subtract_vectors(ali_vec, proxy)
                _error = cg.length_vector_sqrd(difference)  # original

            # for face in faces:
            #     error += face.get_error()

                error += _error
        
        print('error', error)
        error /= mesh.number_of_faces()
        print('error', error)
        errors.append(error)
    
    with open('errors.txt', 'w') as f:
        for e in errors:
            f.write(str(e))
            f.write('\n')

    import matplotlib.pyplot as plt

    plt.plot(errors)
    plt.show()
    # ==========================================================================
    # Visualization
    # ==========================================================================

    # plotter.show()
