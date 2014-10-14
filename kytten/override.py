#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/override.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import pyglet
import pyglet.gl as gl
from pyglet.text import runlist
from types import MethodType

from .tools import string_to_unicode, patch_instance_method
from .base import xrange

KYTTEN_LAYOUT_GROUPS = {}
KYTTEN_LAYOUT_GROUP_REFCOUNTS = {}

_Line = pyglet.text.layout._Line

class KyttenEventDispatcher(pyglet.event.EventDispatcher):

    def remove_handler(self, name, handler):
        # See 'remove_handler' method of pyglet.event.EventDispatcher

        for frame in self._event_stack:
            try: # set comparison to EQUAL (is testing was failling for some instance bond functions)
                if frame[name] == handler:
                    del frame[name]
                    break
            except KeyError:
                pass

class TextLayoutGroup_KYTTEN_OVERRIDE(pyglet.graphics.Group):
    def set_state(self):
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_CURRENT_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)
        # To Allow Normal Rendering when Buffering with FrameBufferObject
        # Without this option : problem with alpha blending when rendering buffered GUI textures
        #Also in context.glContext

    def unset_state(self):
        gl.glPopAttrib()


class ScrollableTextLayoutGroup_KYTTEN_OVERRIDE(pyglet.text.layout.ScrollableTextLayoutGroup):

    def set_state(self):
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_TRANSFORM_BIT | gl.GL_CURRENT_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)
        # To Allow Normal Rendering when Buffering with FrameBufferObject
        # Without this option : problem with alpha blending when rendering buffered GUI textures
        #Also in context.glContext

        # Disable clipping planes to check culling.
        gl.glEnable(gl.GL_CLIP_PLANE0)
        gl.glEnable(gl.GL_CLIP_PLANE1)
        gl.glEnable(gl.GL_CLIP_PLANE2)
        gl.glEnable(gl.GL_CLIP_PLANE3)
        # Left
        gl.glClipPlane(gl.GL_CLIP_PLANE0, (gl.GLdouble * 4)(
                    1, 0, 0, -(self._clip_x - 1)))
        # Top
        gl.glClipPlane(gl.GL_CLIP_PLANE1, (gl.GLdouble * 4)(
                    0, -1, 0, self._clip_y))
        # Right
        gl.glClipPlane(gl.GL_CLIP_PLANE2, (gl.GLdouble * 4)(
                    -1, 0, 0, self._clip_x + self._clip_width + 1))
        # Bottom
        gl.glClipPlane(gl.GL_CLIP_PLANE3, (gl.GLdouble * 4)(
                    0, 1, 0, -(self._clip_y - self._clip_height)))
        gl.glTranslatef(self.translate_x, self.translate_y, 0)


def GetKyttenLayoutGroups(group):
    if not group in  KYTTEN_LAYOUT_GROUPS:
        top_group = TextLayoutGroup_KYTTEN_OVERRIDE(group)
        background_group = pyglet.graphics.OrderedGroup(0, top_group)
        foreground_group = pyglet.text.layout.TextLayoutForegroundGroup(1, top_group)
        foreground_decoration_group = pyglet.text.layout.TextLayoutForegroundDecorationGroup(2, top_group)

        KYTTEN_LAYOUT_GROUPS[group] = (top_group,
                                       background_group,
                                       foreground_group,
                                       foreground_decoration_group)
        KYTTEN_LAYOUT_GROUP_REFCOUNTS[group] = 0
    KYTTEN_LAYOUT_GROUP_REFCOUNTS[group] += 1
    return KYTTEN_LAYOUT_GROUPS[group]

def ReleaseKyttenLayoutGroups(group):
    KYTTEN_LAYOUT_GROUP_REFCOUNTS[group] -= 1
    if not KYTTEN_LAYOUT_GROUP_REFCOUNTS[group]:
        del KYTTEN_LAYOUT_GROUP_REFCOUNTS[group]
        del KYTTEN_LAYOUT_GROUPS[group]

pyglet_IncrementalTextLayout = pyglet.text.layout.IncrementalTextLayout

class KyttenIncrementalTextLayout(pyglet_IncrementalTextLayout):
    def _init_groups(self, group):
        # Scrollable layout never shares group because of translation.
        self.top_group = ScrollableTextLayoutGroup_KYTTEN_OVERRIDE(group)
        self.background_group = pyglet.graphics.OrderedGroup(0, self.top_group)
        self.foreground_group = pyglet.text.layout.TextLayoutForegroundGroup(1, self.top_group)
        self.foreground_decoration_group =  pyglet.text.layout.TextLayoutForegroundDecorationGroup(2, self.top_group)

    def _update(self):
        if not self._update_enabled:
            return

        trigger_update_event = (self.invalid_glyphs.is_invalid() or
                                self.invalid_flow.is_invalid() or
                                self.invalid_lines.is_invalid())

        # Special care if there is no text:
        if not self.glyphs:
            for line in self.lines:
                line.delete(self)
            del self.lines[:]
            self.lines.append(_Line(0))
            font = self.document.get_font(0, dpi=self._dpi)
            self.lines[0].ascent = font.ascent
            self.lines[0].descent = font.descent
            self.lines[0].paragraph_begin = self.lines[0].paragraph_end = True
            self.invalid_lines.invalidate(0, 1)

        self._update_glyphs()
        self._update_flow_glyphs()
        self._update_flow_lines()
        '''
        #not useful updated in: self.view_y = self.view_y property
        #self._update_visible_lines()
        #self._update_vertex_lists()
        #self.top_group.top = self._get_top(self.lines)
        '''
        # Reclamp view_y in case content height has changed and reset top of
        # content.
        self.view_y = self.view_y
        self.top_group.top = self._get_top(self._get_lines())

        if trigger_update_event:
            self.dispatch_event('on_layout_update')

    def select_all(self):
        self.set_selection(0, len(self.document.text))

    def get_selection_text(self):
        return self.document.text[self.selection_start: self.selection_end]

    def get_selection(self):
        return (self.selection_start, self.selection_end)

class KyttenTextLayout(pyglet.text.layout.TextLayout):

    def __init__(self, *args, **kwargs):
        self.clamp_height = kwargs.pop('clamp_height', False)
        pyglet.text.layout.TextLayout.__init__(self, *args, **kwargs)

    def _get_lines(self):
        len_text = len(self._document.text)
        glyphs = self._get_glyphs()
        owner_runs = runlist.RunList(len_text, None)
        self._get_owner_runs(owner_runs, glyphs, 0, len_text)
        lines = [line for line in self._flow_glyphs(glyphs, owner_runs,
                                                    0, len_text)]
        self.content_width = 0
        self._flow_lines(lines, 0, len(lines))
        self._height = -lines[-1].y if lines else 0

        if self.clamp_height is not False:
            for idx, line in enumerate(lines):
                if line.y < -self.clamp_height:
                    return lines[:idx]

        return lines

pyglet_text_Label = pyglet.text.Label
class KyttenLabel(pyglet.text.Label):
    def __init__(self, text, *args, **kwargs):
        pyglet.text.Label.__init__(self, string_to_unicode(text), *args, **kwargs)

    def _set_text(self, text):
        self.document.text = string_to_unicode(text)
    text = property(pyglet.text.Label._get_text, _set_text)

    def _set_y(self, y):
        if self._boxes:
            self._y = y
            self._update()
        else:
            dy = y - self._y
            l_dy = lambda y: float(y + dy)
            for vertex_list in self._vertex_lists:
                vertices = vertex_list.vertices[:]
                vertices[1::2] = map(l_dy, vertices[1::2])
                vertex_list.vertices[:] = vertices
            self._y = y
    y = property(pyglet.text.Label._get_y, _set_y)

    def _set_x(self, x):
        if self._boxes:
            self._x = x
            self._update()
        else:
            dx = x - self._x
            l_dx = lambda x: float(x + dx)
            for vertex_list in self._vertex_lists:
                """
                vertices = vertex_list.vertices[:]
                vertices[::2] = map(l_dx, vertices[::2])

                vertex_list.vertices[:] = vertices"""
                vertex_list.vertices[::2] = map(l_dx, vertex_list.vertices[::2])
            self._x = x
    x = property(pyglet.text.Label._get_x, _set_x)

    def _init_groups(self, group):
        if not group:
            return # use the default groups
        self.top_group, self.background_group, self.foreground_group,  self.foreground_decoration_group = GetKyttenLayoutGroups(group)

    def teardown(self):
        pyglet.text.Label.delete(self)
        group = self.top_group.parent
        if group is not None:
            ReleaseKyttenLayoutGroups(group)
            self.top_group = self.background_self = self.foreground_group = self.foreground_decoration_group = None

class KyttenCaret(pyglet.text.caret.Caret):
    def __init__(self, layout, batch=None, color=(0, 0, 0)):
        # temporarily swap foreground_decoration_group & layout.background_group to avoid Caret display bugs
        # line 126: batch.add(2, gl.GL_LINES, layout.foreground_decoration_group, 'v2f', ('c4B', colors))
        layout.foreground_decoration_group, layout.background_group  = layout.background_group , layout.foreground_decoration_group
        pyglet.text.caret.Caret.__init__(self, layout, batch, color)
        layout.foreground_decoration_group, layout.background_group  = layout.background_group , layout.foreground_decoration_group

    def select_to_point(self, x, y):
        __doc__ = pyglet.text.caret.Caret.select_to_point.__doc__

        lineno = self._layout.get_line_from_point(x, y)
        line = self._layout.lines[lineno]
        _x = x - self._layout.top_group.translate_x

        self._position = line.x
        if _x >= self._position:
            self._position = self._layout.get_position_on_line(lineno, x)

        self._update(line=lineno)
        self._next_attributes.clear()

class KyttenInputLabel(KyttenLabel):
    def _get_left(self):
        if self._multiline:
            width = self._width
        else:
            width = self.content_width
            if self.width and width > self.width:
                # align to right edge, clip left
                return self._x + self.width - width

        if self._anchor_x == 'left':
            return self._x
        elif self._anchor_x == 'center':
            return self._x - width // 2
        elif self._anchor_x == 'right':
            return self._x - width
        else:
            assert False, 'Invalid anchor_x'

    def _update(self):
        pyglet.text.Label._update(self)

        # Iterate through our vertex lists and break if we need to clip
        remove = []
        if self.width and not self._multiline:
            for vlist in self._vertex_lists:
                num_quads = len(vlist.vertices) / 8
                remove_quads = 0
                has_quads = False
                for n in xrange(0, num_quads):
                    x1, y1, x2, y2, x3, y3, x4, y4 = vlist.vertices[n*8:n*8+8]
                    tx1, ty1, tz1, tx2, ty2, tz2, \
                       tx3, ty3, tz3, tx4, ty4, tz4 = \
                       vlist.tex_coords[n*12:n*12+12]
                    if x2 >= self._x:
                        has_quads = True
                        m = n - remove_quads  # shift quads left
                        if x1 < self._x:  # clip on left side
                            percent = (float(self._x) - float(x1)) / \
                                      (float(x2) - float(x1))
                            x1 = x4 = max(self._x, x1)
                            tx1 = tx4 = (tx2 - tx1) * percent + tx1
                        vlist.vertices[m*8:m*8+8] = \
                            [x1, y1, x2, y2, x3, y3, x4, y4]
                        vlist.tex_coords[m*12:m*12+12] = \
                             [tx1, ty1, tz1, tx2, ty2, tz2,
                              tx3, ty3, tz3, tx4, ty4, tz4]
                    else:
                        # We'll delete quads entirely not visible
                        remove_quads = remove_quads + 1
                if remove_quads == num_quads:
                    remove.append(vlist)
                elif remove_quads > 0:
                    vlist.resize((num_quads - remove_quads) * 4)
        for vlist in remove:
            vlist.delete()
            self._vertex_lists.remove(vlist)

