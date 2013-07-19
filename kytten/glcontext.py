#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/glcontext.py
# Copyrighted (C) 2013 by "Parashurama"

from ctypes import c_ulong
import pyglet.gl as gl

def SetGuiContext(width, height):
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glEnable(gl.GL_BLEND)
    #gl.glClearColor(0.0,0.0,0.0,0.0)
    #gl.glEnable(gl.GL_SCISSOR_TEST)
    gl.glEnable(gl.GL_TEXTURE_2D)

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.gluOrtho2D (0, width, 0, height)

    gl.glMatrixMode (gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    #gl.glScalef(1.0, -1.0, 1.0)      # Inverse Vertical Scale and SubstractWindow Height to convert
    #gl.glTranslatef(0.0, -900.0, 0.) # between Wxpython coordinates and opengl.gl screen coordinates


def RestoreContext():

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()

    gl.glMatrixMode (gl.GL_MODELVIEW)
    gl.glPopMatrix()
    gl.glEnable(gl.GL_CULL_FACE)
    #gl.glCullFace(gl.GL_BACK)

    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_BLEND)

    gl.glDisable(gl.GL_TEXTURE_2D)
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    #gl.glDisable(gl.GL_SCISSOR_TEST)




class RenderBuffer:
    def __init__(self, width = 512, height = 512, screen_size=None ):
        self.surface = None
        self.width = width
        self.height = height

        if not screen_size: self.screen_size=(width,height)
        else: self.screen_size=screen_size

        # create the framebuffer
        self.buffer = (c_ulong * 1)()
        gl.glGenFramebuffersEXT(1,self.buffer)
        self.buffer = self.buffer[0]

        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, self.buffer)

        self.RGB_INFO = self.create_texture()

        gl.glFramebufferTexture2DEXT(gl.GL_FRAMEBUFFER_EXT, gl.GL_COLOR_ATTACHMENT0_EXT, gl.GL_TEXTURE_2D, self.RGB_INFO, 0)

        status = gl.glCheckFramebufferStatusEXT(gl.GL_FRAMEBUFFER_EXT)
        if status != gl.GL_FRAMEBUFFER_COMPLETE_EXT:
            print "ERROR on FRAMEBUFFER"
            return
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, 0)

    def recreate_texture(self, (width, height)):
        self.RGB_INFO = self.create_texture(TexID=self.RGB_INFO, Size=(width, height))

    def create_texture(self, TexID=None, Size=None):
        # create a texture for Rendering Color
        if TexID is not None:
            RGB_INFO = TexID
        else:
            RGB_INFO = (c_ulong * 1)()
            gl.glGenTextures(1, RGB_INFO)
            RGB_INFO = RGB_INFO[0]

        if Size is not None: (self.width, self.height) = Size

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, RGB_INFO)

        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_MAG_FILTER,gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_MIN_FILTER,gl.GL_NEAREST)

        return RGB_INFO

    # start rendering to this framebuffer
    def activate(self):

        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, self.buffer)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        #gl.glOrtho( -self.width/2., self.width/2., -self.height/2., self.height/2., 50., 500.)
        #glOrtho( -width/2., width/2., -height/2., height/2., 50., 500.)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()

        gl.glViewport(0, 0, self.width, self.height)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        #gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE)
        #gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA,gl.GL_ONE,gl.GL_ONE_MINUS_SRC_ALPHA)
        #gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA,gl.GL_ONE,gl.GL_ONE_MINUS_SRC_ALPHA)
    # stop rendering to this framebuffer
    def deactivate(self):

        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, 0)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

    # destroy this framebuffer and free allocated resources.
    #def __del__(self):
        #gl.glDeleteFramebuffersEXT(1, [self.buffer])
        #gl.glDeleteTextures(1, [self.surface])
    #    self.buffer = None
    #   self.surface = None

    def render(self):

        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        #gl.glBlendFuncSeparate(G, gl.GL_ONE_MINUS_SRC_ALPHA, gl.GL_ZERO, gl.GL_ONE)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.RGB_INFO)


        gl.glColor4f(1.0,1.0,1.0,1.0)

        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 0)     ; gl.glVertex3f(0, 0, 0)
        gl.glTexCoord2f(1.0,0.0)  ; gl.glVertex3f(self.width, 0, 0)
        gl.glTexCoord2f(1.0, 1.0) ; gl.glVertex3f(self.width , self.height, 0)
        gl.glTexCoord2f(0.0, 1.0) ; gl.glVertex3f(0, self.height, 0)
        gl.glEnd()

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

def RenderQuad():
    gl.glColor4f(255,255,255,1)

    gl.glBegin(gl.GL_QUADS)
    gl.glVertex3f(0, 0, 0)
    gl.glVertex3f(700, 0, 0)
    gl.glVertex3f(700 , 700, 0)
    gl.glVertex3f(0, 700, 0)
    gl.glEnd()


def RenderTEST(color, (DX, DY)):
    gl.glDisable(gl.GL_TEXTURE_2D)
    gl.glColor4f(*color)

    gl.glBegin(gl.GL_QUADS)

    gl.glVertex3f(DX+32, DY+32, 0)
    gl.glVertex3f(DX+64, DY+32, 0)
    gl.glVertex3f(DX+64, DY+64, 0)
    gl.glVertex3f(DX+32, DY+64, 0)

    gl.glEnd()
    gl.glColor4f(1.0,1.0,1.0,1.0)
    gl.glEnable(gl.GL_TEXTURE_2D)
