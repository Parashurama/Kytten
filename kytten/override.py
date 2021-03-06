#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/override.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function, absolute_import, division

import pyglet
import pyglet.gl as gl
from pyglet.text import runlist
from types import MethodType

from .tools import tostring, patch_instance_method

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
        lines =  pyglet.text.layout.TextLayout._get_lines(self)
        if self.clamp_height is not False:
            for idx, line in enumerate(lines):
                if line.y < -self.clamp_height:
                    return lines[:idx]
        return lines

pyglet_text_Label = pyglet.text.Label
class KyttenLabel(pyglet.text.Label):
    def __init__(self, text, *args, **kwargs):
        pyglet.text.Label.__init__(self, tostring(text), *args, **kwargs)

    def _set_text(self, text):
        self.document.text = tostring(text)
    text = property(pyglet.text.Label._get_text, _set_text)

    def _set_y(self, y):
        if self._boxes:
            self._y = y
            self._update()
        else:
            dy = y - self._y
            l_dy = lambda y: float(y + dy) # Fixes rounding error bug in zoomed out mode in Scrollable
            for vertex_list in self._vertex_lists:
                vertex_list.vertices[1::2] = list(map(l_dy, vertex_list.vertices[1::2]))
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
                vertex_list.vertices[::2] = list(map(l_dx, vertex_list.vertices[::2]))
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

        lineno = self._layout.get_line_from_point(x, y)
        line = self._layout.lines[lineno]
        _x = x - self._layout.top_group.translate_x

        self._position = line.x
        if _x >= self._position:
            self._position = self._layout.get_position_on_line(lineno, x)

        self._update(line=lineno)
        self._next_attributes.clear()
