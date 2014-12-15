#!/usr/bin/python2
# -*- coding: utf8 -*-

from PyQt4 import QtCore, QtGui, QtOpenGL
from OpenGL import GL,GLU
import vispy.gloo as gloo
from vispy.util.transforms import *
from vispy.geometry import *
import numpy

from ObjParser import ObjParser
from Camera import Camera
from Light import Light   
from SceneObject import SceneObject    


class OpenGLWidget(QtOpenGL.QGLWidget):
    """ docstring """
    def __init__(self, object_names = [], parent=None):
        """ docstring """
        QtOpenGL.QGLWidget.__init__(self, parent)
        self._objectNames = object_names[0]

    def getObjectNames(self):
        """ Reload openGLWidget """
        return self._objectNames

    def setObjects(self, object_names):
        """ docstring """
        self._objectNames = object_names[0]
        self.initializeGL()

    # ---------- Partie : Qt ------------
 
    def minimumSizeHint(self):
        """ docstring """
        return QtCore.QSize(50, 50)
 
    def sizeHint(self):
        """ docstring """
        return QtCore.QSize(400, 400)

        # Events
    def mousePressEvent(self, event):
        """ This method is called when there is a click """
        self.lastPos = QtCore.QPoint(event.pos())
 
    def mouseMoveEvent(self, event):
        """ This method is called when there is a mouse (drag) event"""
        smoothFactor = 10
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        dx = int(dx/smoothFactor)
        dy = int(dy/smoothFactor)
        res = False
        if event.buttons() & QtCore.Qt.LeftButton:
            res |= self._camera.setX(self._camera.getX() + 8 * dy)
            res |= self._camera.setY(self._camera.getY() + 8 * dx)
        elif event.buttons() & QtCore.Qt.RightButton:
            res |= self._camera.setX(self._camera.getX() + 8 * dy)
            res |= self._camera.setZ(self._camera.getZ() + 8 * dx)
        self.lastPos = QtCore.QPoint(event.pos())
        if res:
            self.updateGL()
 
    def wheelEvent(self, event):
        """ docstring """
        if (event.delta() > 0):
            self._camera.zoomIn()
        else:
            self._camera.zoomOut()
        self.updateGL()

    def updateLights(self,position):
        """ """
        self._light.setLightsRatio(position)
        self.updateGL()


    # ---------- Partie : Opengl ------------
 
    # Called at startup
    def initializeGL(self):
        """ docstring """
        # save mouse cursor position for smooth rotation
        self.lastPos = QtCore.QPoint()

        self.vertexshader = gloo.VertexShader("shaders/vertex.shader")
        self.fragmentshader = gloo.FragmentShader("shaders/fragment.shader")

        gloo.set_state(clear_color=(0.30, 0.30, 0.35, 1.00), depth_test=True,
                       polygon_offset=(1, 1),
                       blend_func=('src_alpha', 'one_minus_src_alpha'),
                       line_width=0.75)
        # create camera and light
        self._camera = Camera()
        self._light = Light()

        self.shadowMap = gloo.Program("""
            attribute vec3 position;
             
            uniform mat4 u_projection;
            uniform mat4 u_model;
            uniform mat4 u_view;
             
            void main(){
                gl_Position =  u_projection * u_view * u_model * vec4(position,1);
            }
            """,
            """
            // should we trust openGL to do that ?
            //out float fragmentdepth;
             
            void main(){
                // Not really needed, OpenGL does it anyway
                //fragmentdepth = gl_FragCoord.z;
                gl_FragDepth = gl_FragCoord.z;
            }
            """)
        self.shadowMap['u_projection'] = ortho(-10,10,-10,10,-10,100)
        self.positions = []
        self.indices = []

        # create floor and load .obj objects
        self.objects = []
        self.makeFloor()
        # examples : should be removed or used for empty scenes
        # self.makeCube((0,1.1,0),(0,1,0,1))
        # self.makeSphere((0,3,0),(1,1,1,1))
        self.loadObjects()


    # maybe define that function else where ?
    def lookAt(self, eye, center, up):
        ret = numpy.eye(4, dtype=numpy.float32)

        Z = numpy.array(eye, numpy.float32) - numpy.array(center, numpy.float32)
        Z = self.normalize(Z)
        Y = numpy.array(up, numpy.float32)
        X = numpy.cross(Y, Z)
        Y = numpy.cross(Z, X)

        X = self.normalize(X)
        Y = self.normalize(Y)

        ret[0][0] = X[0]
        ret[1][0] = X[1]
        ret[2][0] = X[2]
        ret[3][0] = -numpy.dot(X, eye)
        ret[0][1] = Y[0]
        ret[1][1] = Y[1]
        ret[2][1] = Y[2]
        ret[3][1] = -numpy.dot(Y, eye)
        ret[0][2] = Z[0]
        ret[1][2] = Z[1]
        ret[2][2] = Z[2]
        ret[3][2] = -numpy.dot(Z, eye)
        ret[0][3] = 0
        ret[1][3] = 0
        ret[2][3] = 0
        ret[3][3] = 1.0
        return ret

    def normalize(self, v):
        norm=numpy.linalg.norm(v)
        if norm==0: 
           return v
        return v/norm

    # Objects construction methods
    def makeFloor(self):
        """ docstring """
        program = gloo.Program(self.vertexshader, self.fragmentshader)
        vertices = [[ 10, 0, 10], [10, 0, -10], [-10, 0, -10], [-10,0, 10],
                    [ 10, -0.1, 10], [10, -0.1, -10], [-10, -0.1, -10], [-10, -0.1, 10]]
        program['position'] =  gloo.VertexBuffer(vertices)
        normals = []
        for index in range(len(vertices)):
            prev = vertices[index-1]
            curr = vertices[index]
            next = vertices[(index+1)%len(vertices)]
            diff1 = numpy.subtract(prev, curr)
            diff2 = numpy.subtract(next, curr)
            normals.append(numpy.cross(diff2, diff1))
        program['normal'] = gloo.VertexBuffer(normals)
        I = [0,1,2, 0,2,3,  0,3,4, 0,4,5,  0,5,6, 0,6,1,
             1,6,7, 1,7,2,  7,4,3, 7,3,2,  4,7,6, 4,6,5]
        indices = gloo.IndexBuffer(I)
        O = [0,1, 1,2, 2,3, 3,0,
             4,7, 7,6, 6,5, 5,4,
             0,5, 1,6, 2,7, 3,4 ]
        outlines = gloo.IndexBuffer(O)
        self.objects.append(SceneObject(program, 
                                        (0,0,0),
                                        (0.5,0.5,0.5,1),
                                        indices,
                                        outlines))
        self.positions.append(gloo.VertexBuffer(vertices))
        self.indices.append(indices)

    def makeCube(self, position, color):
        """ docstring """
        V, F, O = create_cube()
        vertices = gloo.VertexBuffer(V)
        indices = gloo.IndexBuffer(F)
        outlines = gloo.IndexBuffer(O)

        program = gloo.Program(self.vertexshader, self.fragmentshader)
        program.bind(vertices)
        self.objects.append(SceneObject(program,
                                        position,
                                        color,
                                        indices,
                                        outlines))

    def makeSphere(self, position, color):
        sphere = create_sphere(36,36)
        V = sphere.vertices()
        N = sphere.vertex_normals()
        F = sphere.faces()
        vertices = gloo.VertexBuffer(V)
        normals = gloo.VertexBuffer(N)
        indices = gloo.IndexBuffer(F)

        program = gloo.Program(self.vertexshader, self.fragmentshader)
        program['position'] = vertices
        program['normal'] = normals
        self.objects.append(SceneObject(program,
                                        position,
                                        color,
                                        indices))

    def loadObjects(self):
        for obj in self._objectNames:
            parser = ObjParser(obj[0])
            position = obj[1]
            color = (0.5,0.5,0.8,1)
            face = parser.getFaces()
            indices = gloo.IndexBuffer(face.astype(numpy.uint16))
            vertices = gloo.VertexBuffer(parser.getVertices())
            program = gloo.Program(self.vertexshader, self.fragmentshader)
            program['position'] = vertices
            program['normal'] = gloo.VertexBuffer(parser.getNormals().astype(numpy.float32))
            #program['u_texture'] = gloo.Texture2D(imread(parser.getMtl().getTexture()))
            self.objects.append(SceneObject(program,
                                            position,
                                            color,
                                            indices))
            self.positions.append(vertices)
            self.indices.append(indices)
 
    # Called on each update/frame
    def paintGL(self):
        """ docstring """
        gloo.clear(color=True, depth=True)

        # set frustum
        self.view = numpy.eye(4, dtype=numpy.float32)
        translate(self.view, 0, -4, self._camera.getZoom())
        self.projection = perspective(60, 4.0/3.0, 0.1, 100)

        self.paintObjects()

    def paintObjects(self):
        shape = 1024,1024
        renderTexture = gloo.Texture2D(shape=(shape + (3,)), dtype=numpy.float32)
        fbo = gloo.FrameBuffer(renderTexture, gloo.DepthBuffer(shape))

        for index, obj in enumerate(self.objects):
            # apply rotation and translation
            model = numpy.eye(4, dtype=numpy.float32)
            translate(model, *obj.position)
            rotate(model, self._camera.getX(), 1, 0, 0)
            rotate(model, self._camera.getY(), 0, 1, 0)
            rotate(model, self._camera.getZ(), 0, 0, 1)
            # create shadow map
            with fbo:
                self.shadowMap['u_model'] = model
                self.shadowMap['u_view'] = self.lookAt(self._light.getPosition(), (0,0,0), (0,1,0))
                self.shadowMap['position'] = self.positions[index]
                self.shadowMap.draw('triangles', obj.indices)
            # draw object
            normal = numpy.array(numpy.matrix(numpy.dot(self.view, model)).I.T)
            obj.program['u_normal'] = normal
            obj.program['u_light_position'] = self._light.getPosition()
            obj.program['u_light_intensity'] = self._light.getIntensity()
            obj.program['u_model'] = model
            obj.program['u_view'] = self.view
            obj.program['u_projection'] = self.projection
            if (obj.visible):
                obj.program['u_color'] = obj.color
                obj.program.draw('triangles', obj.indices)
                if (obj.outline):
                    obj.program['u_color'] = (0,0,0,1)
                    obj.program.draw('lines', obj.outline)


    def shadowMapTexture(self):
        fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)
        texture = GL.glGenTextures( 1 )
        GL.glBindTexture( GL.GL_TEXTURE_2D, texture )
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT,
            1024, 1024, 0,
            GL.GL_DEPTH_COMPONENT, GL.GL_UNSIGNED_BYTE, None
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_DEPTH_ATTACHMENT,
            GL.GL_TEXTURE_2D,
            texture,
            0 #mip-map level...
        )
        # if sys.platform in ('win32','darwin'):
        #     """Win32 and OS-x require that a colour buffer be bound..."""
        #     color = GL.glGenRenderbuffers(1)
        #     GL.glBindRenderbuffer( GL.GL_RENDERBUFFER, color )
        #     GL.glRenderbufferStorage(
        #         GL.GL_RENDERBUFFER,
        #         GL.GL_RGBA,
        #         1024,
        #         1024,
        #     )
        #     GL.glFramebufferRenderbuffer( GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_RENDERBUFFER, color )
        #     GL.glBindRenderbuffer( GL.GL_RENDERBUFFER, 0 )
        # GL.glViewport(0,0,1024,1024)
        GL.glDrawBuffer( GL.GL_NONE )
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        return texture

    # Called when window is resized
    def resizeGL(self, width, height):
        """ docstring """
        # set openGL in the center of the widget
        GL.glViewport(0, 0, width, height)
 
 