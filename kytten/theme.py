#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/theme.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import os

import pyglet
import ctypes as c
from pyglet import gl
from .tools import wrapper, yield_single_value, iteritems

try:
    import json
    json_load = json.loads
except ImportError:
    try:
        import simplejson as json
        json_load = json.loads
    except ImportError:
        import sys
        print("Warning: using 'safe_eval' to process json files, " \
              "please upgrade to Python 2.6 or install simplejson")
        from . import safe_eval
        def json_load(expr):
            # strip carriage returns
            return safe_eval.safe_eval(''.join(str(expr).split('\r')))

DEFAULT_THEME_SETTINGS = {
    "font": "Lucida Grande",
    "font_size": 12,
    "font_size_small": 10,
    "text_color": [255, 255, 255, 255],
    "gui_color": [255, 255, 255, 255],
    "highlight_color": [255, 255, 255, 64],
    "disabled_color": [160, 160, 160, 255],
}

class ThemeTextureGroup(pyglet.graphics.TextureGroup):
    '''
    ThemeTextureGroup, in addition to setting the texture, also ensures that
    we map to the nearest texel instead of trying to interpolate from nearby
    texels.  This prevents 'blooming' along the edges.
    '''
    def set_state(self):
        pyglet.graphics.TextureGroup.set_state(self)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)

        # To Allow Normal Rendering when Buffering with FrameBufferObject
        # Without this option : problem with alpha blending when rendering buffered GUI textures
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)


class CustomGraphicTextureGroup(pyglet.graphics.TextureGroup):
    '''
    CustomGraphicTextureGroup, in addition to setting the texture, also ensures that
    correct interpolation between texels.
    '''

    def set_state(self):
        pyglet.graphics.TextureGroup.set_state(self)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)
        # To Allow Normal Rendering when Buffering with FrameBufferObject
        # Without this option : problem with alpha blending when rendering buffered GUI textures
        #Also in context.glContext

class UntexturedGroup(pyglet.graphics.Group):
    '''
    CustomGraphicTextureGroup, in addition to setting the texture, also ensures that
    correct interpolation between texels.
    '''

    def set_state(self):
        pyglet.graphics.Group.set_state(self)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)
        # To Allow Normal Rendering when Buffering with FrameBufferObject
        # Without this option : problem with alpha blending when rendering buffered GUI textures
        #Also in context.glContext



class UndefinedGraphicElementTemplate:
    def __init__(self, theme):
        self.theme = theme
        self.width = 0
        self.height = 0
        self.margins = [0, 0, 0, 0]
        self.padding = [0, 0, 0, 0]

    def generate(self, color, batch, group):
        return UndefinedGraphicElement(self.theme, color, batch, group)

    def write(self, f, indent=0):
        f.write('None')

class TextureGraphicElementTemplate(UndefinedGraphicElementTemplate):
    def __init__(self, theme, texture, width=None, height=None):
        UndefinedGraphicElementTemplate.__init__(self, theme)
        self.texture = texture
        self.width = width or texture.width
        self.height = height or texture.height

    def generate(self, color, batch, group):
        return TextureGraphicElement(self.theme, self.texture,
                                     color, batch, group)

    def write(self, f, indent=0):
        f.write('{\n')
        f.write(' ' * (indent + 2) + '"src": "%s"' % self.texture.src)
        if hasattr(self.texture, 'region'):
            f.write(',\n' + ' ' * (indent + 2) + '"region": %s' %
                    repr(list(self.texture.region)))
        f.write('\n' + ' ' * indent + '}')

class FrameTextureGraphicElementTemplate(TextureGraphicElementTemplate):
    def __init__(self, theme, texture, stretch, padding, fixed_minsize=True, width=None, height=None):
        TextureGraphicElementTemplate.__init__(self, theme, texture, width=width, height=height)

        self.stretch_texture = texture.get_region(*stretch).get_texture()
        x, y, width, height = stretch
        self.margins = (x, texture.width - width - x,   # left, right
                        texture.height - height - y, y) # top, bottom
        self.padding = padding
        self.fixed_minsize = fixed_minsize

    def generate(self, color, batch, group):
        return FrameTextureGraphicElement(
            self.theme, self.texture, self.stretch_texture,
            self.margins, self.padding, color, self.fixed_minsize, batch, group)

    def write(self, f, indent=0):
        f.write('{\n')
        f.write(' ' * (indent + 2) + '"src": "%s"' % self.texture.src)
        if hasattr(self.texture, 'region'):
            f.write(',\n' + ' ' * (indent + 2) + '"region": %s' % repr(list(self.texture.region)))
        left, right, top, bottom = self.margins
        if left != 0 or right != 0 or top != 0 or bottom != 0 or  self.padding != [0, 0, 0, 0]:
            stretch = [left, bottom, self.width-right-left, self.height-top-bottom]
            f.write(',\n' + ' ' * (indent + 2) + '"stretch": %s' % repr(list(stretch)))
            f.write(',\n' + ' ' * (indent + 2) + '"padding": %s' % repr(list(self.padding)))
        if not self.fixed_minsize:
            f.write(',\n' + ' ' * (indent + 2) + '"fixed_minsize": false')
        f.write('\n' + ' ' * indent + '}')

class TextureIconElementTemplate(TextureGraphicElementTemplate):
    def __init__(self, theme, texture, icon):
        TextureGraphicElementTemplate.__init__(self, theme, texture)
        self.icon = icon

    def generate(self, color, batch, group, igroup, no_label=False):
        return TextureIconElement(
            self.theme, self.texture, self.icon,
            color, batch, group, igroup, no_label)

class TextureSkewedElementTemplate(TextureGraphicElementTemplate):

    def __init__(self, theme, texture, skewed, skew=0):
        TextureGraphicElementTemplate.__init__(self, theme, texture)
        self.skewed = skewed
        self.skew = skew

    def generate(self, color, batch, group):
        return TextureSkewedElement(
            self.theme, self.texture, color, batch, group,
            self.skewed, self.skew)


class FrameRepeatTextureGraphicElementTemplate(TextureGraphicElementTemplate):
    def __init__(self, theme, texture, repeat, padding,
                 width=None, height=None):
        TextureGraphicElementTemplate.__init__(self, theme, texture,
                                               width=width, height=height)
        #bottom-left, top-right opengl texture coordinates wich is different from pyglet texture 'tex_coords' (12 float tuple)
        s0,t0,_, s1,t0,_, s1, t1, _, s0, t1, _ =  texture.tex_coords
        self.texture.texcoords = (s0,t0,s1,t1)

        x, y, width, height = repeat
        self.texture.size = (float(self.texture.width), float(self.texture.height))
        self.texture.header_bar=[0,0,None,None]
        self.texture.content_padding = padding
        self.texture.border_padding = ( x, texture.width - width - x,   # left, right
                                        texture.height - height - y, y) # top, bottom
        # Used for writing theme
        self.margins = (x, texture.width - width - x,   # left, right
                        texture.height - height - y, y) # top, bottom
        self.padding = padding

    def generate(self, color, batch, group):
        return Repeat_NinePatchTextureGraphicElement(self.texture, color, self.texture.size, (0,0), batch, group)

    def write(self, f, indent=0):
        f.write('{\n')
        f.write(' ' * (indent + 2) + '"src": "%s"' % self.texture.src)
        if hasattr(self.texture, 'region'):
            f.write(',\n' + ' ' * (indent + 2) + '"region": %s' %
                    repr(list(self.texture.region)))
        left, right, top, bottom = self.margins

        if left != 0 or right != 0 or top != 0 or bottom != 0 or \
           self.padding != [0, 0, 0, 0]:
            repeat = [left, bottom,
                       self.width - right - left, self.height - top - bottom]
            f.write(',\n' + ' ' * (indent + 2) + '"repeat": %s' %
                    repr(list(repeat)))
            f.write(',\n' + ' ' * (indent + 2) + '"padding": %s' %
                    repr(list(self.padding)))
        f.write('\n' + ' ' * indent + '}')


class TextureIconElement:
    def __init__(self, theme, texture, icon, color, batch, group, igroup,
                 no_label):
        self.x = self.y = 0
        self.no_label = no_label
        self.width, self.height = texture.width, texture.height
        self.iwidth, self.iheight = icon.width, icon.height
        self.group = ThemeTextureGroup(texture, group)
        self.igroup = ThemeTextureGroup(icon, igroup)
        self.vertex_list = batch.add(4, gl.GL_QUADS, self.group,
                                     ('v2i', self._get_vertices()),
                                     ('c4B', color * 4),
                                     ('t3f', texture.tex_coords))
        self.ivertex_list = batch.add(4, gl.GL_QUADS, self.igroup,
                                     ('v2i', self._get_ivertices()),
                                     ('c4B', color * 4),
                                     ('t3f', icon.tex_coords))

    def _get_vertices(self):
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(self.width), y1 + int(self.height)
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def _get_ivertices(self):
        divider = 1.5
        if self.no_label:
            divider = 2
        x1 = int(self.x + self.width/2 - self.iwidth/2)
        y1 = int(self.y + self.height/divider - self.iheight/2)
        x2, y2 = x1 + int(self.iwidth), y1 + int(self.iheight)
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def delete(self):
        self.vertex_list.delete()
        self.vertex_list = None
        self.ivertex_list.delete()
        self.ivertex_list = None
        self.group = None

    def get_content_region(self):
        return (self.x, self.y, self.width, self.height)

    def get_content_size(self, width, height):
        return width, height

    def get_needed_size(self, content_width, content_height):
        return self.width, self.height

    def update(self, x, y, width, height):
        self.x, self.y, self.width, self.height = x, y, width, height
        if self.vertex_list is not None:
            self.vertex_list.vertices = self._get_vertices()
        if self.ivertex_list is not None:
            self.ivertex_list.vertices = self._get_ivertices()

class TextureSkewedElement:
    def __init__(self, theme, texture, color, batch, group, skewed, skew=0):
        self.x = self.y = 0
        self.skewed = skewed
        self.skew = skew
        self.tilt = .5
        self.width, self.height = texture.width, texture.height
        self.group = ThemeTextureGroup(texture, group)
        self.vertex_list = batch.add(4, gl.GL_QUADS, self.group,
                                     ('v2i', self._get_vertices()),
                                     ('c4B', color * 4),
                                     ('t3f', texture.tex_coords))

    def _get_vertices(self):
        x1, y1 = int(self.x), int(self.y)
        x2 = x1 + int(self.width)
        tilt, skew = self.height * self.tilt, self.height * self.skew
        yl = y1 + min(max(int(tilt + skew), 0), self.height)
        yr = y1 + min(max(int(tilt - skew), 0), self.height)
        if self.skewed == 'top':
            return (x1, y1, x2, y1, x2, yr, x1, yl)
        else:
            yt = y1 + self.height
            return (x1, yl, x2, yr, x2, yt, x1, yt)

    def delete(self):
        self.vertex_list.delete()
        self.vertex_list = None
        self.group = None

    def get_content_region(self):
        return (self.x, self.y, self.width, self.height)

    def get_content_size(self, width, height):
        return width, height

    def get_needed_size(self, content_width, content_height):
        return self.width, self.height

    def update(self, x, y, width, height, skew=0, tilt=.5):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.skew, self.tilt = skew, tilt
        if self.vertex_list is not None:
            self.vertex_list.vertices = self._get_vertices()

class TextureGraphicElement:
    def __init__(self, theme, texture, color, batch, group):
        self.x = self.y = 0
        self.width, self.height = texture.width, texture.height
        self.group = ThemeTextureGroup(texture, group)
        self.vertex_list = batch.add(4, gl.GL_QUADS, self.group,
                                     ('v2i', self._get_vertices()),
                                     ('c4B', color * 4),
                                     ('t3f', texture.tex_coords))

    def _get_vertices(self):
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(self.width), y1 + int(self.height)
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def delete(self):
        self.vertex_list.delete()
        self.vertex_list = None
        self.group = None

    def get_content_region(self):
        return (self.x, self.y, self.width, self.height)

    def get_content_size(self, width, height):
        return width, height

    def get_needed_size(self, content_width, content_height):
        return content_width, content_height

    def update(self, x, y, width, height):
        self.x, self.y, self.width, self.height = x, y, width, height
        if self.vertex_list is not None:
            self.vertex_list.vertices = self._get_vertices()

class FrameTextureGraphicElement:
    def __init__(self, theme, texture, inner_texture, margins, padding,
                 color, fixed_minsize, batch, group):
        self.x = self.y = 0
        self.width, self.height = texture.width, texture.height
        self.group = ThemeTextureGroup(texture, group)
        self.outer_texture = texture
        self.inner_texture = inner_texture
        self.margins = margins
        self.padding = padding
        self.fixed_minsize = fixed_minsize
        self.vertex_list = batch.add(36, gl.GL_QUADS, self.group,
                                     ('v2i', self._get_vertices()),
                                     ('c4B', color * 36),
                                     ('t2f', self._get_tex_coords()))

    def _get_tex_coords(self):
        x1, y1 = self.outer_texture.tex_coords[0:2] # outer's lower left
        x4, y4 = self.outer_texture.tex_coords[6:8] # outer's upper right
        x2, y2 = self.inner_texture.tex_coords[0:2] # inner's lower left
        x3, y3 = self.inner_texture.tex_coords[6:8] # inner's upper right
        return (x1, y1, x2, y1, x2, y2, x1, y2,  # bottom left
                x2, y1, x3, y1, x3, y2, x2, y2,  # bottom
                x3, y1, x4, y1, x4, y2, x3, y2,  # bottom right
                x1, y2, x2, y2, x2, y3, x1, y3,  # left
                x2, y2, x3, y2, x3, y3, x2, y3,  # center
                x3, y2, x4, y2, x4, y3, x3, y3,  # right
                x1, y3, x2, y3, x2, y4, x1, y4,  # top left
                x2, y3, x3, y3, x3, y4, x2, y4,  # top
                x3, y3, x4, y3, x4, y4, x3, y4)  # top right

    def _get_vertices(self):
        left, right, top, bottom = self.margins
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(left), y1 + int(bottom)
        x3 = x1 + int(self.width) - int(right)
        y3 = y1 + int(self.height) - int(top)
        x4, y4 = x1 + int(self.width), y1 + int(self.height)
        return (x1, y1, x2, y1, x2, y2, x1, y2,  # bottom left
                x2, y1, x3, y1, x3, y2, x2, y2,  # bottom
                x3, y1, x4, y1, x4, y2, x3, y2,  # bottom right
                x1, y2, x2, y2, x2, y3, x1, y3,  # left
                x2, y2, x3, y2, x3, y3, x2, y3,  # center
                x3, y2, x4, y2, x4, y3, x3, y3,  # right
                x1, y3, x2, y3, x2, y4, x1, y4,  # top left
                x2, y3, x3, y3, x3, y4, x2, y4,  # top
                x3, y3, x4, y3, x4, y4, x3, y4)  # top right

    def delete(self):
        self.vertex_list.delete()
        self.vertex_list = None
        self.group = None

    def get_content_region(self):
        left, right, top, bottom = self.padding
        return (self.x + left, self.y + bottom,
                self.width - left - right, self.height - top - bottom)

    def get_content_size(self, width, height):
        left, right, top, bottom = self.padding
        return width - left - right, height - top - bottom

    def get_needed_size(self, content_width, content_height):
        left, right, top, bottom = self.padding
        min_size = (self.outer_texture.width, self.outer_texture.height) if self.fixed_minsize else (0,0)
        return (max(content_width + left + right, min_size[0]),
                max(content_height + top + bottom, min_size[1]))

    def update(self, x, y, width, height):
        self.x, self.y, self.width, self.height = x, y, width, height
        if self.vertex_list is not None:
            self.vertex_list.vertices = self._get_vertices()



class Stretch_NinePatchTextureGraphicElement(object):

    def __init__(self, texture, color=None, size=(0,0), position=(0,0), batch=None, group=None):

        self._x, self._y = self.position = position
        self.width, self.height = self.size = size

        self._color = get_color_value(color)
        self._batch = batch
        self._texture = texture
        self._texture.target=gl.GL_TEXTURE_2D
        self._group = CustomGraphicTextureGroup(self._texture, parent=group)

        #self.padding = texture.border_padding
        self._header_bar = texture.header_bar

        self._vertex_list = batch.add(36, gl.GL_QUADS, self._group,
                                     ('v2i', self._get_vertices()),
                                     ('c4B', self._color * 36),
                                     ('t2f', self._get_tex_coords()))

    def _get_tex_coords(self):
        s0, t0, s1, t1 = self._texture.texcoords
        left, right, top, bottom = self._texture.border_padding
        tex_width, tex_height = self._texture.size
        t_width, t_height = s1-s0, t1-t0

        x1, y1 = s0, t0 # outer's lower left
        x4, y4 = s1, t1 # outer's upper right
        x2, y2 = s0 + t_width*float(left)/tex_width, t0 + t_height*float(bottom)/tex_height # inner's lower left

        x3, y3 = s1 - t_width*(float(right)/tex_width), t1 - t_height*(float(top)/tex_height) # inner's upper right

        #was used only works when texture not in tetxure_atlas
        #x3, y3 = t_width*(1.0-float(right)/tex_width), t_height*(1.0-float(top)/tex_height) # inner's upper right

        return (x1, y1, x2, y1, x2, y2, x1, y2,  # bottom left
                x2, y1, x3, y1, x3, y2, x2, y2,  # bottom
                x3, y1, x4, y1, x4, y2, x3, y2,  # bottom right
                x1, y2, x2, y2, x2, y3, x1, y3,  # left
                x2, y2, x3, y2, x3, y3, x2, y3,  # center
                x3, y2, x4, y2, x4, y3, x3, y3,  # right
                x1, y3, x2, y3, x2, y4, x1, y4,  # top left
                x2, y3, x3, y3, x3, y4, x2, y4,  # top
                x3, y3, x4, y3, x4, y4, x3, y4)  # top right

    def _get_vertices(self):
        left, right, top, bottom = self._texture.border_padding
        x1, y1 = int(self._x), int(self._y)
        x2, y2 = x1 + int(left), y1 + int(bottom)
        x3 = x1 + int(self.width) - int(right)
        y3 = y1 + int(self.height) - int(top)
        x4, y4 = x1 + int(self.width), y1 + int(self.height)
        return (x1, y1, x2, y1, x2, y2, x1, y2,  # bottom left #x1-10, y1-10, x2-10, y1-10, x2-10, y2-10, x1-10, y2-10,
                x2, y1, x3, y1, x3, y2, x2, y2,  # bottom
                x3, y1, x4, y1, x4, y2, x3, y2,  # bottom right
                x1, y2, x2, y2, x2, y3, x1, y3,  # left
                x2, y2, x3, y2, x3, y3, x2, y3,  # center
                x3, y2, x4, y2, x4, y3, x3, y3,  # right
                x1, y3, x2, y3, x2, y4, x1, y4,  # top left
                x2, y3, x3, y3, x3, y4, x2, y4,  # top
                x3, y3, x4, y3, x4, y4, x3, y4)  # top right

    def delete(self):
        if self._vertex_list is not None:
            self._vertex_list.delete()
            self._vertex_list = None
        self._texture = None

        # Easy way to break circular reference, speeds up GC
        self._group = None

    def get_content_region(self):
        left, right, top, bottom = self._texture.content_padding
        return (self._x + left,   self._y + bottom,   self.width - left - right,   self.height - top - bottom)

    def get_content_size(self, width, height):
        left, right, top, bottom = self._texture.content_padding
        return width - left - right, height - top - bottom

    def get_needed_size(self, content_width, content_height):
        left, right, top, bottom = self._texture.content_padding
        return (content_width + left + right,  content_height + top + bottom)

    def update(self, x, y, width=None, height=None):
        self._x, self._y = self.position = (x,y)

        width = self.width  if width  is None else width
        height= self.height if height is None else height

        self.width, self.height = self.size = (width, height)

        if self._vertex_list is not None:
            self._vertex_list.vertices = self._get_vertices()

class Repeat_NinePatchTextureGraphicElement(object):

    def __init__(self, texture, color=None, size=(0,0), position=(0,0), batch=None, group=None):

        self._x, self._y = self.position = position
        self.width, self.height = self.size = size

        self._color = get_color_value(color)

        self._batch = batch
        self._texture = texture
        self._texture.target=gl.GL_TEXTURE_2D
        self._vertex_list = None
        self._group = CustomGraphicTextureGroup(self._texture, parent=group)
        self._header_bar = texture.header_bar

        #self.padding = texture.padding

    def _get_vertices(self):
        return list(repeat_ninepatches_vertexcoords(self._texture, self.position, self.size))

    def _get_texcoords(self):
        return list(repeat_ninepatches_texcoords(self._texture, self.position, self.size))

    def delete(self):
        if self._vertex_list is not None:
            self._vertex_list.delete()
            self._vertex_list = None
        self._texture = None

        # Easy way to break circular reference, speeds up GC
        self._group = None

    def get_content_region(self):
        left, right, top, bottom = self._texture.content_padding
        return (self._x + left,   self._y + bottom,   self.width - left - right,   self.height - top - bottom)

    def get_content_size(self, width, height):
        left, right, top, bottom = self._texture.content_padding
        return width - left - right, height - top - bottom

    def get_needed_size(self, content_width, content_height):
        left, right, top, bottom = self._texture.content_padding
        return (content_width + left + right,  content_height + top + bottom)

    def update(self, x, y, width=None, height=None):
        self._x, self._y = self.position =(x,y)

        width = self.width  if width  is None else width
        height= self.height if height is None else height

        if self._vertex_list is not None and (self.width == width) and (self.height == height):
            self._vertex_list.vertices = self._get_vertices()

        else:
            if self._vertex_list is not None:
                self._vertex_list.delete()

            self.width, self.height = self.size = (width, height)
            vertices = self._get_vertices()
            n_vertexes = len(vertices)//3

            self._vertex_list = self._batch.add (n_vertexes, gl.GL_QUADS, self._group,
                                                ('v3f/dynamic',vertices),
                                                ('c4B', self._color*n_vertexes ),
                                                ('t2f', self._get_texcoords())
                                                )

class UntexturedGraphicElement(object):
    def __init__(self, color, batch, group):
        self.x = self.y = 0
        self.width, self.height = 0, 0
        self.group = UntexturedGroup(group)
        self.vertex_list = batch.add(4, gl.GL_QUADS, self.group,
                                     ('v2i', self._get_vertices()),
                                     ('c4B', color * 4))

    def _get_vertices(self):
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(self.width), y1 + int(self.height)
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def delete(self):
        self.vertex_list.delete()
        self.vertex_list = None
        self.group = None

    def get_content_region(self):
        return (self.x, self.y, self.width, self.height)

    def get_content_size(self, width, height):
        return width, height

    def get_needed_size(self, content_width, content_height):
        return content_width, content_height

    def update(self, x, y, width, height):
        self.x, self.y, self.width, self.height = x, y, width, height
        if self.vertex_list is not None:
            self.vertex_list.vertices = self._get_vertices()


class DefaultTextureGraphicElement(object):

    def __init__(self, texture, color=None, size=(0,0), position=(0,0), batch=None, group=None):
        self._x, self._y = self.position = position
        self.width, self.height = self.size = size

        self._texture = texture
        self._texture.target=gl.GL_TEXTURE_2D
        self._group = CustomGraphicTextureGroup(self._texture, parent=group)

        self._color = get_color_value(color)

        self._vertex_list = batch.add(4, gl.GL_QUADS, self._group,
                                     ('v2i', self._get_vertices()),
                                     ('c4B', self._color * 4),
                                     ('t2f', self._get_texcoords()))

    def _get_vertices(self):
        x1, y1 = int(self._x), int(self._y)
        x2, y2 = x1 + int(self.width), y1 + int(self.height)
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def _get_texcoords(self):
        s0,t0,s1,t1 = self._texture.texcoords
        return s0,t0,s1,t0,s1,t1,s0,t1

    def delete(self):
        if self._vertex_list:
            self._vertex_list.delete()
            self._vertex_list = None
        self._texture = None

        # Easy way to break circular reference, speeds up GC
        self._group = None

    def get_content_region(self):
        return (self._x, self._y, self.width, self.height)

    def get_content_size(self, width, height):
        return width, height

    def get_needed_size(self, content_width, content_height):
        return content_width, content_height

    def update(self, x, y, width=None, height=None):
        self._x, self._y, self.width, self.height = x, y, width or self.width, height or self.height
        if self._vertex_list is not None:
            self._vertex_list.vertices = self._get_vertices()



class UndefinedGraphicElement(TextureGraphicElement):
    def __init__(self, theme, color, batch, group):
        self.x = self.y = self.width = self.height = 0
        self.group = group
        self.vertex_list = batch.add(12, gl.GL_LINES, self.group,
                                     ('v2i', self._get_vertices()),
                                     ('c4B', color * 12))

    def _get_vertices(self):
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(self.width), y1 + int(self.height)
        return (x1, y1, x2, y1, x2, y1, x2, y2,
                x2, y2, x1, y2, x1, y2, x1, y1,
                x1, y1, x2, y2, x1, y2, x2, y1)



class ScopedDict(dict):
    '''
    ScopedDicts differ in several useful ways from normal dictionaries.

    First, they are 'scoped' - if a key exists in a parent ScopedDict but
    not in the child ScopedDict, we return the parent value when asked for it.

    Second, we can use paths for keys, so we could do this:
        path = ['button', 'down', 'highlight']
        color = theme[path]['highlight_color']

    This would return the highlight color assigned to the highlight a button
    should have when it is clicked.
    '''
    def __init__(self, arg={}, parent=None):
        self.parent = parent
        for k, v in iteritems(arg):
            if isinstance(v, dict):
                self[k] = ScopedDict(v, self)
            else:
                self[k] = v
    def __getitem__(self, key):
        if key is None:
            return self
        elif isinstance(key, list) or isinstance(key, tuple):
            if len(key) > 1:
                return self.__getitem__(key[0]).__getitem__(key[1:])
            elif len(key) == 1:
                return self.__getitem__(key[0])
            else:
                return self  # theme[][key] should return theme[key]
        else:
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                if self.parent is not None:
                    return self.parent.__getitem__(key)
                else:
                    raise

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            dict.__setitem__(self, key, ScopedDict(value, self))
        else:
            dict.__setitem__(self, key, value)

    def get(self, key, default=None):
        if isinstance(key, list) or isinstance(key, tuple):
            if len(key) > 1:
                return self.__getitem__(key[0]).get(key[1:], default)
            elif len(key) == 1:
                return self.get(key[0], default)
            else:
                raise KeyError(key)  # empty list

        if key in self:
            return dict.get(self, key)
        elif self.parent:
            return self.parent.get(key, default)
        else:
            return default

    def get_path(self, path, default=None):
        assert isinstance(path, list) or isinstance(path, tuple)
        if len(path) == 1:
            return self.get(path[0], default)
        else:
            return self.__getitem__(path[0]).get_path(path[1:], default)

    def set_path(self, path, value):
        assert isinstance(path, list) or isinstance(path, tuple)
        if len(path) == 1:
            return self.__setitem__(path[0], value)
        else:
            return self.__getitem__(path[0]).set_path(path[1:], value)

    def write(self, f, indent=0):
        f.write('{\n')
        first = True
        for k, v in iteritems(self):
            if not first:
                f.write(',\n')
            else:
                first = False
            f.write(' ' * (indent + 2) + '"%s": ' % k)
            if isinstance(v, ScopedDict):
                v.write(f, indent + 2)
            elif isinstance(v, UndefinedGraphicElementTemplate):
                v.write(f, indent + 2)
            elif hasattr(v, 'startswith'):# string bytes or unicode
                if   v == "True":
                    f.write("true")
                elif v == "False":
                    f.write("false")
                else:
                    f.write('"%s"' % v)
            elif isinstance(v, tuple):
                f.write('%s' % repr(list(v)))
            else:
                f.write(repr(v))

        f.write('\n')
        f.write(' ' * indent + '}')

class Theme(ScopedDict):
    '''
    Theme is a dictionary-based class that converts any elements beginning
    with 'image' into a GraphicElementTemplate.  This allows us to specify
    both simple textures and 9-patch textures, and more complex elements.
    '''
    def __init__(self, arg, override={}, default=DEFAULT_THEME_SETTINGS,
                 allow_empty_theme=False, name='theme.json'):
        '''
        Creates a new Theme.

        @param arg The initializer for Theme.  May be:
            * another Theme - we'll use the same graphic library but
                              apply an override for its dictionary.
            * a dictionary - interpret any subdirectories where the key
                             begins with 'image' as a GraphicElementTemplate
            * a filename - read the JSON file as a dictionary
        @param override Replace some dictionary entries with these
        @param default Initial dictionary entries before handling input
        @param allow_empty_theme True if we should allow creating a new theme
        '''
        ScopedDict.__init__(self, default, None)

        self.groups = {}

        if isinstance(arg, Theme):
            self.textures = arg.textures
            for k, v in iteritems(arg):
                self.__setitem__(k, v)
            self.update(override)
            return

        if isinstance(arg, dict):
            self.loader = pyglet.resource.Loader(os.getcwd())
            input = arg
        elif os.path.isfile(arg) or os.path.isdir(arg):
                self.loader = pyglet.resource.Loader(path=arg)
                try:
                    theme_file = self.loader.file(name)
                    input = json_load(theme_file.read().decode('utf-8'))
                    theme_file.close()
                except pyglet.resource.ResourceNotFoundException:
                    input = {}
        else:
            raise IOError("Invalid path. Theme folder '{}' couldn't be found!".format(os.path.abspath(arg)))

        self.textures = {}
        self._update_with_images(self, input)
        self.update(override)

    def __getitem__(self, key):
        try:
            return ScopedDict.__getitem__(self, key)
        except KeyError as e:
            if hasattr(key,"startswith") and key.startswith('image'):
                return UndefinedGraphicElementTemplate(self)
            else:
                raise e

    def _get_texture(self, filename):
        '''
        Returns the texture associated with a filename.  Loads it from
        resources if we haven't previously fetched it.

        @param filename The filename of the texture
        '''
        if filename not in self.textures:
            texture = self.loader.texture(filename)
            texture.src = filename
            self.textures[filename] = texture
        return self.textures[filename]

    def _get_texture_region(self, filename, x, y, width, height):
        '''
        Returns a texture region.

        @param filename The filename of the texture
        @param x X coordinate of lower left corner of region
        @param y Y coordinate of lower left corner of region
        @param width Width of region
        @param height Height of region
        '''
        texture = self._get_texture(filename)
        retval = texture.get_region(x, y, width, height).get_texture()
        retval.src = texture.src
        retval.region = [x, y, width, height]
        return retval

    def _update_with_images(self, target, input):
        '''
        Update a ScopedDict with the input dictionary.  Translate
        images into texture templates.

        @param target The ScopedDict which is to be populated
        @param input The input dictionary
        '''
        for k, v in iteritems(input):
            if k.startswith('image'):
                if isinstance(v, dict):
                    width = height = None
                    if 'region' in v:
                        x, y, width, height = v['region']
                        texture = self._get_texture_region(
                                v['src'], x, y, width, height)
                    else:
                        texture = self._get_texture(v['src'])
                    if 'icon' in v:
                        icon = self._get_texture(v['icon'])
                        target[k] = TextureIconElementTemplate(
                            self,
                            texture,
                            icon)
                    elif 'skewed' in v:
                        target[k] = TextureSkewedElementTemplate(
                            self,
                            texture,
                            v['skewed'],
                            v.get('skew', 0))
                    elif 'stretch' in v:
                        target[k] = FrameTextureGraphicElementTemplate(
                            self,
                            texture,
                            v['stretch'],
                            v.get('padding', [0, 0, 0, 0]),
                            fixed_minsize = v.get('fixed_minsize', True),
                            width=width, height=height)
                    elif 'repeat' in v:
                        target[k] = FrameRepeatTextureGraphicElementTemplate(
                            self,
                            texture,
                            v['repeat'],
                            v.get('padding', [0, 0, 0, 0]),
                            width=width, height=height)
                    else:
                        target[k] = TextureGraphicElementTemplate(
                            self, texture, width=width, height=height)
                else:
                    target[k] = TextureGraphicElementTemplate(
                        self, self._get_texture(v))
            elif isinstance(v, dict):
                temp = ScopedDict(parent=target)
                self._update_with_images(temp, v)
                target[k] = temp
            else:
                target[k] = v

    def write(self, f, indent=0):
        ScopedDict.write(self, f, indent)
        f.write('\n')

#######################

@wrapper(yield_single_value)
def repeat_ninepatches_vertexcoords(texture, position, size):
    left,right,top,bottom = texture.border_padding

    X1,Y1=position

    X2=X1+size[0]
    Y2=Y1+size[1]

    i=-1 ; j=-1

    repeatwidth=size[0]-(left+right)  ; repeatx_tex=texture.size[0]-(left+right) ; repeatx=repeatwidth/repeatx_tex
    repeatheight=size[1]-(bottom+top) ; repeaty_tex=texture.size[1]-(bottom+top) ; repeaty=repeatheight/repeaty_tex

    for pos in (
        (X1,Y1,0.0), (X1+left,Y1,0.0), (X1+left,Y1+bottom,0.0), (X1,Y1+bottom,0.0),
        (X1,Y2-top,0.0), (X1+left,Y2-top,0.0), (X1+left,Y2,0.0), (X1,Y2,0.0),
        (X2-right,Y1,0.0), (X2,Y1,0.0), (X2,Y1+bottom,0.0), (X2-right,Y1+bottom,0.0),
        (X2-right,Y2-top,0.0), (X2,Y2-top,0.0), (X2,Y2,0.0), (X2-right,Y2,0.0) ):
        yield pos

    #VERTEXARRAY= np.vstack( (VERTEXARRAY, np.array([  ( (X1,Y1+bottom + i*repeaty_tex,0.0), (X1+left,Y1+bottom + i*repeaty_tex,0.0), (X1+left,Y1+bottom + (i+1)*repeaty_tex,0.0), (X1,Y1+bottom + (i+1)*repeaty_tex,0.0) ) for i in range(int(repeaty)) ]+[ ( (X1,Y1+bottom + (i+1)*repeaty_tex,0.0), (X1+left,Y1+bottom + (i+1)*repeaty_tex,0.0),  (X1+left,Y2-top,0.0), (X1,Y2-top,0.0) )  ],'float32' ).reshape(-1,3) ))
    for i in range(int(repeaty)):
        yield (X1,Y1+bottom + i*repeaty_tex,0.0)
        yield (X1+left,Y1+bottom + i*repeaty_tex,0.0)
        yield (X1+left,Y1+bottom + (i+1)*repeaty_tex,0.0)
        yield (X1,Y1+bottom + (i+1)*repeaty_tex,0.0)

    yield (X1,Y1+bottom + (i+1)*repeaty_tex,0.0)
    yield (X1+left,Y1+bottom + (i+1)*repeaty_tex,0.0)
    yield (X1+left,Y2-top,0.0)
    yield (X1,Y2-top,0.0)

    #VERTEXARRAY= np.vstack( (VERTEXARRAY, np.array([  ( (X2-right,Y1+bottom + i*repeaty_tex,0.0), (X2,Y1+bottom + i*repeaty_tex,0.0), (X2,Y1+bottom + (i+1)*repeaty_tex,0.0), (X2-right,Y1+bottom + (i+1)*repeaty_tex,0.0) ) for i in range(int(repeaty)) ]+[ ( (X2-right,Y1+bottom + (i+1)*repeaty_tex,0.0), (X2,Y1+bottom + (i+1)*repeaty_tex,0.0),  (X2,Y2-top,0.0), (X2-right,Y2-top,0.0) )  ],'float32' ).reshape(-1,3) ))
    for i in range(int(repeaty)):
        yield (X2-right,Y1+bottom + i*repeaty_tex,0.0)
        yield (X2,Y1+bottom + i*repeaty_tex,0.0)
        yield (X2,Y1+bottom + (i+1)*repeaty_tex,0.0)
        yield (X2-right,Y1+bottom + (i+1)*repeaty_tex,0.0)

    yield (X2-right,Y1+bottom + (i+1)*repeaty_tex,0.0)
    yield (X2,Y1+bottom + (i+1)*repeaty_tex,0.0)
    yield (X2,Y2-top,0.0)
    yield (X2-right,Y2-top,0.0)

    #    VERTEXARRAY= np.vstack( (VERTEXARRAY, np.array([  ( (X1+left + j*repeatx_tex,Y1,0.0), (X1+left + (j+1)*repeatx_tex,Y1,0.0), (X1+left + (j+1)*repeatx_tex,Y1+bottom,0.0), (X1+left + j*repeatx_tex,Y1+bottom,0.0) ) for j in range(int(repeatx)) ]+[ ( (X1+left + (j+1)*repeatx_tex,Y1,0.0), (X2-right, Y1,0.0),(X2-right, Y1+bottom,0.0), (X1+left + (j+1)*repeatx_tex,Y1+bottom,0.0) )  ],'float32' ).reshape(-1,3) ))

    for j in range(int(repeatx)):
        yield (X1+left + j*repeatx_tex,Y1,0.0)
        yield (X1+left + (j+1)*repeatx_tex,Y1,0.0)
        yield (X1+left + (j+1)*repeatx_tex,Y1+bottom,0.0)
        yield (X1+left + j*repeatx_tex,Y1+bottom,0.0)

    yield (X1+left + (j+1)*repeatx_tex,Y1,0.0)
    yield (X2-right, Y1,0.0)
    yield (X2-right, Y1+bottom,0.0)
    yield (X1+left + (j+1)*repeatx_tex,Y1+bottom,0.0)

    #VERTEXARRAY= np.vstack( (VERTEXARRAY, np.array([  ( (X1+left + j*repeatx_tex,Y2-top,0.0), (X1+left + (j+1)*repeatx_tex, Y2-top,0.0), (X1+left + (j+1)*repeatx_tex,Y2,0.0), (X1+left + j*repeatx_tex,Y2,0.0) ) for j in range(int(repeatx)) ]+[ ( (X1+left + (j+1)*repeatx_tex,Y2-top,0.0), (X2-right, Y2-top,0.0),(X2-right, Y2,0.0), (X1+left + (j+1)*repeatx_tex,Y2,0.0) )  ],'float32' ).reshape(-1,3) ))

    for j in range(int(repeatx)):
        yield (X1+left + j*repeatx_tex,Y2-top,0.0)
        yield (X1+left + (j+1)*repeatx_tex, Y2-top,0.0)
        yield (X1+left + (j+1)*repeatx_tex,Y2,0.0)
        yield (X1+left + j*repeatx_tex,Y2,0.0)

    yield (X1+left + (j+1)*repeatx_tex,Y2-top,0.0)
    yield (X2-right, Y2-top,0.0)
    yield (X2-right, Y2,0.0)
    yield (X1+left + (j+1)*repeatx_tex,Y2,0.0)

    #VERTEXARRAY= np.vstack( (VERTEXARRAY, np.array([  ( (X1+left + j*repeatx_tex, Y1+bottom + i*repeaty_tex,0.0), (X1+left + (j+1)*repeatx_tex, Y1+bottom + i*repeaty_tex,0.0), (X1+left + (j+1)*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0), (X1+left + j*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0) )  for i in range(int(repeaty)) for j in range(int(repeatx)) ] +\

    for i in range(int(repeaty)):
        for j in range(int(repeatx)):
            yield (X1+left + j*repeatx_tex, Y1+bottom + i*repeaty_tex,0.0)
            yield (X1+left + (j+1)*repeatx_tex, Y1+bottom + i*repeaty_tex,0.0)
            yield (X1+left + (j+1)*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0)
            yield (X1+left + j*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0)

    #[ ( (X1+left + (j+1)*repeatx_tex,Y1+bottom + i*repeaty_tex,0.0), (X2-right, Y1+bottom + i*repeaty_tex,0.0),(X2-right,  Y1+bottom + (i+1)*repeaty_tex,0.0), (X1+left + (j+1)*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0) ) for i in range(int(repeaty)) ] +\
    for i in range(int(repeaty)):
        yield (X1+left + (j+1)*repeatx_tex,Y1+bottom + i*repeaty_tex,0.0)
        yield (X2-right, Y1+bottom + i*repeaty_tex,0.0)
        yield (X2-right,  Y1+bottom + (i+1)*repeaty_tex,0.0)
        yield (X1+left + (j+1)*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0)

    #[ ( (X1+left + j*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0), (X1+left + (j+1)*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0), (X1+left + (j+1)*repeatx_tex, Y2-top,0.0), (X1+left + j*repeatx_tex, Y2-top,0.0) ) for j in range(int(repeatx)) ] ,'float32' ).reshape(-1,3) ))
    for j in range(int(repeatx)):
        yield (X1+left + j*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0)
        yield (X1+left + (j+1)*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0)
        yield (X1+left + (j+1)*repeatx_tex, Y2-top,0.0)
        yield (X1+left + j*repeatx_tex, Y2-top,0.0)

    #VERTEXARRAY= np.vstack( (VERTEXARRAY, np.array([ ( (X1+left + (j+1)*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0), (X2-right, Y1+bottom + (i+1)*repeaty_tex,0.0), (X2-right, Y2-top,0.0), (X1+left + (j+1)*repeatx_tex, Y2-top,0.0) ) ], 'float').reshape(-1,3) ) )
    yield (X1+left + (j+1)*repeatx_tex, Y1+bottom + (i+1)*repeaty_tex,0.0)
    yield (X2-right, Y1+bottom + (i+1)*repeaty_tex,0.0)
    yield (X2-right, Y2-top,0.0)
    yield (X1+left + (j+1)*repeatx_tex, Y2-top,0.0)


@wrapper(yield_single_value)
def repeat_ninepatches_texcoords(texture, position, size):


    s0, t0, s1, t1        = texture.texcoords
    left,right,top,bottom = texture.border_padding
    tex_width, tex_height = texture.size
    t_width, t_height     = s1-s0, t1-t0

    repeatwidth=size[0]-(left+right)  ; repeatx_tex=texture.size[0]-(left+right) ; repeatx=repeatwidth/repeatx_tex
    repeatheight=size[1]-(bottom+top) ; repeaty_tex=texture.size[1]-(bottom+top) ; repeaty=repeatheight/repeaty_tex

    tx1=s0 + t_width*float(left)/tex_width     ; tx2a=s1 - t_width*(float(right)/tex_width) ; tx2b=(size[0]-(left+right) )/texture.size[0]
    ty1=t0 + t_height*float(bottom)/tex_height ; ty2a=t1 - t_height*(float(top)/tex_height)   ; ty2b=(size[1]-(bottom+top) )/texture.size[1]

    tys=ty1+(repeaty-int(repeaty))*(ty2a-ty1) ; txs=tx1+(repeatx-int(repeatx) )*(tx2a-tx1)

    i=0 ; j=0

    for pos in ((s0,t0), (tx1,t0), (tx1,ty1), (s0,ty1),
                (s0,ty2a), (tx1,ty2a), (tx1,t1), (s0,t1),
                (tx2a,t0), (s1,t0), (s1,ty1), (tx2a,ty1),
                (tx2a,ty2a), (s1,ty2a), (s1,t1), (tx2a,t1)):
        yield pos

    #TEXTUREARRAY=np.vstack( (TEXTUREARRAY, np.array([  ( (s0,ty1), (tx1,ty1), (tx1,ty2a), (s0,ty2a) ) for i in range(int(repeaty)) ] + [ ((s0,ty1), (tx1,ty1), (tx1,tys),(s0,tys)) ],'float32' ).reshape(-1,2) ) )
    for i in range(int(repeaty)):
        yield (s0,ty1); yield (tx1,ty1); yield (tx1,ty2a); yield (s0,ty2a)

    yield (s0,ty1); yield (tx1,ty1); yield (tx1,tys); yield (s0,tys)

    #TEXTUREARRAY=np.vstack( (TEXTUREARRAY, np.array([  ( (tx2a,ty1), (s1,ty1), (s1,ty2a), (tx2a,ty2a) ) for i in range(int(repeaty)) ] + [ ((tx2a,ty1), (s1,ty1), (s1,tys),(tx2a,tys)) ],'float32' ).reshape(-1,2) ) )
    for i in range(int(repeaty)):
        yield (tx2a,ty1); yield (s1,ty1); yield (s1,ty2a); yield (tx2a,ty2a)

    yield (tx2a,ty1); yield (s1,ty1); yield (s1,tys); yield (tx2a,tys)

    #TEXTUREARRAY=np.vstack( (TEXTUREARRAY, np.array([  ( (tx1,t0), (tx2a,t0), (tx2a,ty1), (tx1,ty1) ) for j in range(int(repeatx)) ] + [( (tx1,t0), (txs,t0), (txs,ty1), (tx1,ty1) ) ],'float32' ).reshape(-1,2) ) )
    for j in range(int(repeatx)):
        yield (tx1,t0); yield (tx2a,t0); yield (tx2a,ty1); yield (tx1,ty1)

    yield (tx1,t0); yield (txs,t0); yield (txs,ty1); yield (tx1,ty1)

    #TEXTUREARRAY=np.vstack( (TEXTUREARRAY, np.array([  ( (tx1,ty2a), (tx2a,ty2a), (tx2a,t1), (tx1,t1) ) for j in range(int(repeatx)) ] + [( (tx1,ty2a), (txs,ty2a), (txs,t1), (tx1,t1) ) ],'float32' ).reshape(-1,2) ) )
    for j in range(int(repeatx)):
        yield(tx1,ty2a); yield (tx2a,ty2a); yield (tx2a,t1); yield (tx1,t1)

    yield (tx1,ty2a); yield (txs,ty2a); yield (txs,t1); yield (tx1,t1)

    #TEXTUREARRAY=np.vstack( (TEXTUREARRAY, np.array([  ( (tx1,ty1), (tx2a,ty1), (tx2a,ty2a), (tx1,ty2a) ) for i in range(int(repeaty)) for j in range(int(repeatx)) ] + [ ( (tx1,ty1), (txs,ty1), (txs,ty2a), (tx1,ty2a) ) for i in range(int(repeaty)) ] + [ ( (tx1,ty1), (tx2a,ty1), (tx2a,tys), (tx1,tys) ) for j in range(int(repeatx)) ]  ,'float32' ).reshape(-1,2) ) )
    for i in range(int(repeaty)):
        for j in range(int(repeatx)):
            yield (tx1,ty1); yield (tx2a,ty1); yield (tx2a,ty2a); yield (tx1,ty2a)

    for i in range(int(repeaty)):
        yield (tx1,ty1); yield (txs,ty1); yield (txs,ty2a); yield (tx1,ty2a)

    for j in range(int(repeatx)):
        yield (tx1,ty1); yield (tx2a,ty1); yield (tx2a,tys); yield (tx1,tys)

    yield (tx1,ty1); yield (txs,ty1); yield (txs,tys); yield (tx1,tys)

def get_color_value(color):
    try:
        if color is None:
            return (255,255,255,255)
        if not len(color) == 4:
            raise TypeError()
        int(color[0]) # RGBA color values
        if isinstance(color[0], float):
            return map(lambda x: int(255*x), color)
        return color
    except TypeError:
        raise TypeError('Invalid Color Type: must be RGBA format: [255,255,255,255] or (1.0,1.0,1.0,1.0)')
#######################

class KyttenTexture(object):

    def __init__(self, imagedata, imagedatatype, size):
        self.size=( float(size[0]),float(size[1]) )
        self.texcoords=(0.0,0.0,1.0,1.0)
        self.padding=(0,0,0,0)
        self._header_bar=[0,0,None,None]
        self.width, self.height = size[0], size[1]

        id = c.c_uint()
        gl.glGenTextures(1, c.byref(id))
        self.id = id.value

        texture_data  = (c.c_ubyte * (self.width * self.height * 4))()

        for i, u in enumerate(imagedata):
            texture_data[i]= u

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.id)

        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, texture_data)

        gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_MAG_FILTER,gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_MIN_FILTER,gl.GL_LINEAR)

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

_SETTINGS = DEFAULT_THEME_SETTINGS.copy()
_SETTINGS.update({"button": { "text_color": [0, 0, 0, 255],
                              "down":{},
                              "up":{}
                            }
                 })

DEFAULT_EMPTY_THEME = ScopedDict(_SETTINGS)

