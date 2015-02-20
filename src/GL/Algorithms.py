from OpenGL import GL, GLU
from vispy import gloo
from vispy.util.transforms import *
import numpy
from operator import add

from Camera import Camera
from Light import Light
from Utils import *

def concatPositions(verticesList):
    return reduce(add, verticesList, [])

# add index so mesh reference only their vertices
def concatIndices(indicesList):
    def addIndices(newIndices, indices):
        max_index = max(newIndices)+1 if len(newIndices) > 0 else 0
        # curr = indices
        # prev = None
        # # reduce from n dimensions to 1
        # while (type(curr) != int):
        #     prev = curr
        #     print (type(curr))
        #     print type(prev)
        #     curr = reduce(lambda x,y: x+y, prev)
        try:
            newIndices.extend([item+max_index for sublist in indices for item in sublist])
        except:
            newIndices.extend([item+max_index for item in indices])
        return newIndices
    return reduce(addIndices, indicesList, [])

def concatNormals(normalsList):
    return reduce(add, normalsList, [])

class ShadowMapAlgorithm:
    def __init__(self):
        # assign members that never change
        self._program = gloo.Program("shaders/shadowmapalgo.vertexshader",
                                    "shaders/shadowmapalgo.fragmentshader")
        self._shadowMap = gloo.Program("shaders/shadowmap.vertexshader",
                                        "shaders/shadowmap.fragmentshader")

    def init(self, positions, indices, normals, camera, light):
        """ Method that initialize the algorithm """
        self._positions = gloo.VertexBuffer(concatPositions(positions))
        self._indices = gloo.IndexBuffer(numpy.array(concatIndices(indices)))
        self._normals = gloo.VertexBuffer(concatNormals(normals))
        self._camera = camera
        self._light = light
        self._program['position'] = self._positions
        self._program['normal'] = self._normals
        self._shadowMap['position'] = self._positions
        self.active = True
        
        # Shadow map
        shape = 768,1366
        self._renderTexture = gloo.Texture2D(shape=(shape + (4,)), dtype=numpy.float32)
        self._fbo = gloo.FrameBuffer(self._renderTexture)

        # matrices
        self._projection = perspective(60, 16.0/9.0, 0.1, 50)
        self._shadow_projection = ortho(-5, +5, -5, +5, 10, 50)

    def update(self):
        """ Method to call on each OpenGL update """
        if self.active:
            # create render matrices
            view = numpy.eye(4, dtype=numpy.float32)
            translate(view, 0, -4, self._camera.getZoom())
            model = numpy.eye(4, dtype=numpy.float32)
            rotate(model, self._camera.getX(), 1, 0, 0)
            rotate(model, self._camera.getY(), 0, 1, 0)
            rotate(model, self._camera.getZ(), 0, 0, 1)
            # create shadow map matrices
            shadow_model = numpy.eye(4, dtype=numpy.float32)
            shadow_view = lookAt(self._light.getPosition(), (0,2,0), (0,1,0))
            # create shadow map
            with self._fbo:
                self._shadowMap['u_projection'] = self._shadow_projection
                self._shadowMap['u_model'] = shadow_model
                self._shadowMap['u_view'] = shadow_view
                self._shadowMap.draw('triangles', self._indices)

            # draw scene
            biasMatrix = numpy.matrix( [[0.5, 0.0, 0.0, 0.0],
                                        [0.0, 0.5, 0.0, 0.0],
                                        [0.0, 0.0, 0.5, 0.0],
                                        [0.5, 0.5, 0.5, 1.0]])
            # normal = numpy.array(numpy.matrix(numpy.dot(view, model)).I.T)
            self._program['u_model'] = model
            self._program['u_view'] = view
            self._program['u_projection'] = self._projection
            self._program['u_bias_matrix'] = biasMatrix
            self._program['u_depth_model'] = shadow_model
            self._program['u_depth_view'] = shadow_view
            self._program['u_depth_projection'] = self._shadow_projection
            self._program['u_shadow_map'] = self._renderTexture
            self._program['u_color'] = (0.5, 0.5, 0.8, 1) # TODO remove hardcoded value
            self._program['u_light_intensity'] = self._light.getIntensity()
            self._program['u_light_position'] = self._light.getPosition()
            self._program.draw('triangles', self._indices)

            # draw shadowmap as minimap
            GL.glViewport(0,0,455,256)
            self._shadowMap.draw('triangles', self._indices)
            GL.glViewport(0,0,1366,768)

    def terminate(self):
        """ Method to stop algorithm """
        self.active = False
        self._positions = []
        self._indices = []
        self._normals = []
        self._camera = None
        self._light = None

class RayTracingAlgorithm:
    def __init__(self):

        self.program = gloo.Program("shaders/raytracingalgo.vertexshader", "shaders/raytracingalgo.fragmentshader")

        self.init(positions, indices, normals, camera, light)

    def init(self, positions, indices, normals, camera, light):
        self._positions = gloo.VertexBuffer(positions)
        self._indices = gloo.IndexBuffer(numpy.array(indices))
        self._normals = gloo.VertexBuffer(normals)
        self._camera = camera
        self._light = light
        self.program['a_position'] = [(-1., -1.), (-1., +1.),
                                      (+1., -1.), (+1., +1.)]

        self.program['plane_position'] = (0., -.5, 0.)
        self.program['plane_normal'] = (0., 1., 0.)

        self.program['light_intensity'] = 1.
        self.program['light_specular'] = (1., 50.)
        self.program['light_position'] = (5., 5., -10.)
        self.program['light_color'] = (1., 1., 1.)
        self.program['ambient'] = .05
        self.program['O'] = (0., 0., -1.)
        self.active = True

    def update(self):
        if self.active:
            pass

    def terminate(self):
        self.active = False
        self._positions = []
        self._indices = []
        self._normals = []
        self._camera = None
        self._light = None

class NoShadowAlgorithm:
    def __init__(self):
        self._program = gloo.Program("shaders/noshadowalgo.vertexshader", "shaders/noshadowalgo.fragmentshader")

    def init(self, positions, indices, normals, camera, light):
        self._positions = gloo.VertexBuffer(concatPositions(positions))
        self._indices = gloo.IndexBuffer(numpy.array(concatIndices(indices)))
        self._normals = gloo.VertexBuffer(concatNormals(normals))
        self._camera = camera
        self._light = light
        self._projection = perspective(60, 4.0/3.0, 0.1, 100)

        self.active = True

        self._program['u_light_intensity'] = 1.
        self._program['u_light_position'] = (5., 5., -10.)
        self._program['normal'] = self._normals
        self._program['position'] = self._positions

    def update(self):
        if self.active:
            # create render matrices
            view = numpy.eye(4, dtype=numpy.float32)
            translate(view, 0, -4, self._camera.getZoom())
            model = numpy.eye(4, dtype=numpy.float32)
            rotate(model, self._camera.getX(), 1, 0, 0)
            rotate(model, self._camera.getY(), 0, 1, 0)
            rotate(model, self._camera.getZ(), 0, 0, 1)
            # draw scene
            normal = numpy.array(numpy.matrix(numpy.dot(view, model)).I.T)
            self._program['u_normal'] = normal
            self._program['u_light_position'] = self._light.getPosition()
            self._program['u_light_intensity'] = self._light.getIntensity()
            self._program['u_model'] = model
            self._program['u_view'] = view
            self._program['u_projection'] = self._projection
            self._program['u_color'] = (0.5, 0.5, 0.8, 1) 
            self._program.draw('triangles', self._indices)

    def terminate(self):
        self.active = False
        self._positions = []
        self._indices = []
        self._normals = []
        self._camera = None
        self._light = None


class ShadowVolumeAlgorithm:
    def __init__(self):
        self._program = gloo.Program("shaders/shadowvolume.vertexshader",
            "shaders/shadowvolume.fragmentshader")

    def init(self, positions, indices, normals, camera, light):
        self._positions = gloo.VertexBuffer(positions)
        self._indices = gloo.IndexBuffer(numpy.array(indices))
        self._normals = gloo.VertexBuffer(normals)
        self._camera = camera
        self._light = light
        self._projection = perspective(60, 4.0/3.0, 0.1, 100)
        self._program['normal'] = self._normals
        self._program['position'] = self._positions

        # shape=(1366,768)
        # self._color_buffer = gloo.ColorBuffer(shape=(shape + (4,)))
        # self._depth_buffer = gloo.DepthBuffer(shape=(shape + (4,)))
        # self._stencil_buffer = gloo.StencilBuffer(shape=(shape + (4,)))
        # self._frame_buffer = gloo.FrameBuffer(self._color_buffer,
                                                # self._depth_buffer,
                                                # self._stencil_buffer)
        self.active = True

    def update(self):
        if self.active:
            # create render matrices
            view = numpy.eye(4, dtype=numpy.float32)
            translate(view, 0, -4, self._camera.getZoom())
            model = numpy.eye(4, dtype=numpy.float32)
            rotate(model, self._camera.getX(), 1, 0, 0)
            rotate(model, self._camera.getY(), 0, 1, 0)
            rotate(model, self._camera.getZ(), 0, 0, 1)
            # draw scene
            # normal = numpy.array(numpy.matrix(numpy.dot(view, model)).I.T)
            # self._program['u_normal'] = normal
            self._program['u_light_position'] = self._light.getPosition()
            self._program['u_light_color'] = self._light.getColor()
            self._program['u_model'] = model
            self._program['u_view'] = view
            self._program['u_projection'] = self._projection
            self._program['u_color'] = (0.5, 0.5, 0.8)
            # # shadow volumes creation
            # # http://archive.gamedev.net/archive/reference/articles/article1990.html
            # with self._frame_buffer:
            #     # step 1 : render scene with lights turned off
            #     self._color_buffer.activate()
            #     self._depth_buffer.activate()
            #     self._program['u_light_color'] = (0,0,0)
            #     self._program.draw('triangles', self._indices)
            #     self._program['u_light_color'] = self._light.getColor()
            #     # step 2 : turn off color and depth buffers
            #     self._color_buffer.deactivate()
            #     self._depth_buffer.deactivate()
            #     self._stencil_buffer.activate()
            #     gloo.set_state(None, cull_face=True)
            #     gloo.set_state(None, stencil_test=True)
            #     # step 3 : draw front faces, depth test and stencil buffer increment
            #     gloo.set_stencil_func('always', 0, 0)
            #     gloo.set_stencil_op('keep', 'incr', 'keep')
            #     gloo.set_cull_face('front')
            #     self._program.draw('triangles', self._indices) # SHOULD DRAW SHADOW VOLUMES
            #     # step 4 : draw back faces, depth test and stencil buffer decrement
            #     gloo.set_stencil_op('keep', 'decr', 'keep')
            #     gloo.set_cull_face('back')
            #     self._program.draw('triangles', self._indices) # SHOULD DRAW SHADOW VOLUMES
            # self._color_buffer.activate()
            # self._depth_buffer.activate()
            # # step 5 : turn on color and depth buffers
            # gloo.set_depth_func('equal')
            # gloo.set_state(None, stencil_test=True)
            # gloo.set_stencil_func('equal', 0, 0)
            # gloo.set_stencil_op('keep', 'keep', 'keep')
            # # step 6 : draw scene with lights turned on where stencil buffer is 0


            # # draw scene
            # self._program.draw('triangles', self._indices)

    def terminate(self):
        self.active = False
        self._positions = []
        self._indices = []
        self._normals = []
        self._camera = None
        self._light = None

