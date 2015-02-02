#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/glcontext.py
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

from ctypes import c_uint
import pyglet.gl as gl

class GuiRenderContextClass(object):
    def __init__(self):
        pass

    def __call__(self, width, height):
        self.frustum_width = width
        self.frustum_height= height
        return self

    def __enter__(self):
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_TEXTURE_2D)

        gl.glEnable(gl.GL_BLEND)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDisable(gl.GL_DEPTH_TEST)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.gluOrtho2D (0, self.frustum_width, 0, self.frustum_height)

        gl.glMatrixMode (gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

    def __exit__(self,  type, value , traceback ):
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()

        gl.glMatrixMode (gl.GL_MODELVIEW)
        gl.glPopMatrix()

        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

GuiRenderContext = GuiRenderContextClass()

class GuiInternalBuffer(object):
    def __init__(self, width = 512, height = 512, screen_size=None ):
        self.render_target_size = width, height

        # create the framebuffer
        self._buffer = (c_uint * 1)() ; gl.glGenFramebuffersEXT(1,self._buffer)
        self._buffer = self._buffer[0]

        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, self._buffer)

        self.rgb_texture = self._create_texture(texture_size=self.render_target_size)

        gl.glFramebufferTexture2DEXT(gl.GL_FRAMEBUFFER_EXT, gl.GL_COLOR_ATTACHMENT0_EXT, gl.GL_TEXTURE_2D, self.rgb_texture, 0)

        status = gl.glCheckFramebufferStatusEXT(gl.GL_FRAMEBUFFER_EXT)
        if status != gl.GL_FRAMEBUFFER_COMPLETE_EXT:
            print("ERROR on FRAMEBUFFER")
            return
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, 0)

    def recreate_texture(self, texture_size):
        #(width, height) = texture_size
        self.rgb_texture = self._create_texture(textureID=self.rgb_texture, texture_size=texture_size)
        self.render_target_size = texture_size

    @staticmethod
    def _create_texture(textureID=None, texture_size=None):
        # create a texture for Rendering Color
        if textureID is not None:
            rgb_texture = textureID
        else:
            rgb_texture = (c_uint * 1)() ; gl.glGenTextures(1, rgb_texture)
            rgb_texture = rgb_texture[0]

        width, height = texture_size

        gl.glActiveTexture(gl.GL_TEXTURE0)

        gl.glBindTexture(gl.GL_TEXTURE_2D, rgb_texture)

        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

        return rgb_texture

    # start rendering to this framebuffer
    def activate(self):

        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, self._buffer)

        gl.glPushAttrib(gl.GL_VIEWPORT_BIT)
        gl.glViewport(0, 0, *self.render_target_size)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    # stop rendering to this framebuffer
    def deactivate(self, *args):

        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, 0)
        gl.glPopAttrib()

    __enter__ = activate
    __exit__ = deactivate

    def render(self):

        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.rgb_texture)
        gl.glEnable(gl.GL_TEXTURE_2D)

        width, height = self.render_target_size

        gl.glColor4f(1.0,1.0,1.0,1.0)

        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0.0, 0.0) ; gl.glVertex3f(0, 0, 0)
        gl.glTexCoord2f(1.0, 0.0) ; gl.glVertex3f(width, 0, 0)
        gl.glTexCoord2f(1.0, 1.0) ; gl.glVertex3f(width , height, 0)
        gl.glTexCoord2f(0.0, 1.0) ; gl.glVertex3f(0, height, 0)
        gl.glEnd()

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glDisable(gl.GL_TEXTURE_2D)

    def delete(self):
        '''
        Destroy this framebuffer and free allocated resources.
        '''
        gl.glDeleteFramebuffersEXT(1, [self._buffer])
        gl.glDeleteTextures(1, [self.rgb_texture])
        self._buffer = None
