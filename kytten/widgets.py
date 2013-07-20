#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/widgets.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"


# Simple widgets belong in this file, to avoid cluttering the directory with
# many small files.  More complex widgets should be placed in separate files.

# Widget: the base GUI element.  A fixed area of space.
# Control: a Widget which accepts events.
# Test: a Widget which draws a crossed box within its area.
# Spacer: a Widget which can expand to fill available space.  Useful to
#         push other Widgets in a layout to the far right or bottom.
# Graphic: a Widget with a texture drawn over its surface.  Can be expanded.
# Label: a Widget which wraps a simple text label.

import pyglet
import weakref
from pyglet import gl
from .override import KyttenLabel, KyttenEventDispatcher
from .base import GenId, ReferenceName, DereferenceName, GetObjectfromName, DisplayGroup, Log, string_to_unicode
from .theme import DefaultTextureGraphicElement

class Widget(object):
    '''
    The base of all Kytten GUI elements.  Widgets correspond to areas on the
    screen and may (in the form of Controls) respond to user input.
    A simple Widget can be used as a fixed-area spacer.

    Widgets are constructed in two passes: first, they are created and
    passed into a Dialog, or added to a Dialog or one of its children,
    then the Dialog calls their size() method to get their size and their
    layout() method to place them on the screen.  When their size is gotten
    for the first time, they initialize any requisite graphic elements
    that could not be done at creation time.
    '''
    def __init__(self, width=0, height=0, name=None, group=None, spacer=False):
        '''
        Creates a new Widget.

        @param width Initial width
        @param height Initial height
        '''
        self.x = self.y = 0
        self.width = width
        self.height = height
        self.saved_dialog = None
        self.visible=True
        self.destroyed=False

        #self.is_unset=True
        #self.to_hide=False
        self.__parent__=None
        #self.parent_entry=None

        if  isinstance(group, str) : GetObjectfromName(group).add(self)
        elif isinstance(group, DisplayGroup): group.add(self)

        #if not spacer: self.id=GenId(self)
        self.id=GenId(self)
        self.name=name
        if self.name: ReferenceName(self,self.name)

    def _get_controls(self):
        '''
        Return this widget if it is a Control, or any children which
        are Controls.
        '''
        return []

    def delete(self):
        '''
        Deletes any graphic elements we have constructed.  Note that
        we may be asked to recreate them later.
        '''

        pass

    def ensure_visible(self):
        if self.saved_dialog is not None:
            self.saved_dialog.ensure_visible(self)

    def expand(self, width, height):
        '''
        Expands the widget to fill the specified space given.

        @param width Available width
        @param height Available height
        '''
        assert False, "Widget does not support expand"

    def hit_test(self, x, y):
        '''
        True if the given point lies within our area.

        @param x X coordinate of point
        @param y Y coordinate of point
        @returns True if the point is within our area
        '''
        return x >= self.x and x < self.x + self.width and \
               y >= self.y and y < self.y + self.height

    def is_expandable(self):
        '''
        Returns true if the widget can expand to fill available space.
        '''
        return False

    def is_focusable(self):
        '''
        Return true if the widget can be tabbed to and accepts keyboard
        input
        '''
        return False

    def is_input(self):
        '''
        Returns true if the widget accepts an input and can return a value
        '''
        return False

    def layout(self, x, y):
        '''
        Assigns a new location to this widget.

        @param x X coordinate of our lower left corner
        @param y Y coordinate of our lower left corner
        '''
        self.x, self.y = x, y

    def size(self, dialog):
        '''
        Constructs any graphic elements needed, and recalculates our size
        if necessary.

        @param dialog The Dialog which contains this Widget
        '''
        if dialog != self and dialog is not None:

            if isinstance(dialog, weakref.ProxyType): dialog = dialog
            else: dialog = weakref.proxy(dialog)

            if isinstance( dialog, ScrollableAssert):
                self.saved_dialog = dialog.saved_dialog
            else:
                self.saved_dialog = dialog

    def teardown(self):
        '''
        Removes all resources and pointers to other GUI widgets.
        '''
        self.delete()
        self.saved_dialog = None
        self.__parent__=None
        if self.destroyed is False:
            self.destroyed = True
            if self.name is not None:
                DereferenceName(self.name)
        else:
            print "widget", self, "destroyed again"

    def Hide(self):
        '''
        Hide Widget and delete graphic resources. Also dereference itself from its parent.
        '''
        if Log.isLogging(): print "ShouldHide",self, self.name, self.visible

        if self.visible is True:
            self.visible=False
            self.delete()

            if self.__parent__ is not None:

                self.__parent__.__dereference_obj__(self) # Parent is Layout Instance (except GridLayout Not yet implemented)

                if self.__parent__.saved_dialog is not None:
                    self.__parent__.saved_dialog.set_needs_layout()

                elif hasattr(self.__parent__,'set_needs_layout'): # Top Level Wrapper
                    self.__parent__.set_needs_layout()

    def Show(self):
        '''
        Show Widget and recreate graphic resources as needed. Also reference itself to its parent.
        '''
        if Log.isLogging(): print "ShouldShow",self, self.name, self.visible

        if self.visible is False:
            self.visible=True

            if self.__parent__ is not None:
                self.__parent__.__rereference_obj__(self) # Parent is Layout Instance (except GridLayout Not yet implemented)

                if self.__parent__.saved_dialog is not None:
                    self.__parent__.saved_dialog.set_needs_layout()

                elif hasattr(self.__parent__,'set_needs_layout'): # Top Level Wrapper
                    self.__parent__.set_needs_layout()


    def ToggleVisibility(self):
        '''
        Toggle widget visibility.
        '''
        if not self.visible: self.Show()
        else: self.Hide()

    def _self(self):
        '''
        Return a strong reference to itself. Used mainly with weak references
        '''
        return self

class Control(Widget, KyttenEventDispatcher):
    '''
    Controls are widgets which can accept events.

    Dialogs will search their children for a list of controls, and will
    then dispatch events to whichever control is currently the focus of
    the user's attention.
    '''
    on_gain_hover_func=None
    on_lose_hover_func=None
    def __init__(self, name=None, on_gain_hover=None, on_lose_hover=None, value=None, width=0, height=0, disabled=False, noId=False, group=None):
        '''
        Creates a new Control.

        @param id Controls may have ids, which can be used to identify
                  them to the outside application.
        @param value Controls may be assigned values at start time.  The
                     values of all controls which have ids can be obtained
                     through the containing Dialog.
        @param x Initial X coordinate of lower left corner
        @param y Initial Y coordinate of lower left corner
        @param width Initial width
        @param height Initial height
        @param disabled True if control should be disabled
        '''
        Widget.__init__(self, width, height, name, spacer=noId, group=group)
        KyttenEventDispatcher.__init__(self)

        self.value = value
        self.disabled_flag = disabled
        self.highlight_flag = False
        self.focus_flag = False
        self.hover_flag = False
        self.tooltip = None

        if on_gain_hover is not None: self.on_gain_hover_func=on_gain_hover
        if on_lose_hover is not None: self.on_lose_hover_func=on_lose_hover

    def _get_controls(self):
        '''
        Creates a new Control.
        '''
        return [(self, self.x, self.x + self.width,    # control, left, right,
                       self.y + self.height, self.y)]  # top, bottom

    def disable(self):
        '''
        Disable Control.
        '''
        if self.disabled_flag is True: return

        self.disabled_flag = True
        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def enable(self):
        '''
        Enable Control.
        '''
        if self.disabled_flag is False: return

        self.disabled_flag = False
        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def get_cursor(self, x, y):
        return self.cursor

    def is_disabled(self):
        return self.disabled_flag

    def is_focus(self):
        return self.focus_flag

    def is_highlight(self):
        return self.highlight_flag

    def on_gain_focus(self):
        self.focus_flag = True

    def on_gain_highlight(self):
        self.highlight_flag = True

    def on_lose_focus(self):
        self.focus_flag = False

    def on_lose_highlight(self):
        self.highlight_flag = False

    def on_gain_hover(self,*args):
        self.hover_flag=True
        if self.on_gain_hover_func is not None:
            self.on_gain_hover_func(self)

    def on_lose_hover(self,*args):
        self.hover_flag=False
        if self.on_lose_hover_func is not None:
            self.on_lose_hover_func(self)

    def on_mouse_double_click(self, *args):
        pass

# Controls can potentially accept most of the events defined for the window,
# but in practice we'll only pass selected events from Dialog.  This avoids
# a large number of unsightly empty method declarations.
for event_type in pyglet.window.Window.event_types:
    Control.register_event_type(event_type)

Control.register_event_type('on_gain_focus')
Control.register_event_type('on_gain_highlight')
Control.register_event_type('on_lose_focus')
Control.register_event_type('on_lose_highlight')
Control.register_event_type('on_update')
Control.register_event_type('on_gain_hover')
Control.register_event_type('on_lose_hover')
Control.register_event_type('on_show')
Control.register_event_type('on_hide')
Control.register_event_type('on_mouse_double_click')

class Spacer(Widget):
    '''
    A Spacer is an empty widget that expands to fill space in layouts.
    Use Widget if you need a fixed-sized spacer.
    '''
    def __init__(self, width=0, height=0, spacer=True):
        '''
        Creates a new Spacer.  The width and height given are the minimum
        area that we must cover.

        @param width Minimum width
        @param height Minimum height
        '''
        Widget.__init__(self, spacer=spacer)
        self.min_width, self.min_height = width, height

    def expand(self, width, height):
        '''
        Expand the spacer to fill the maximum space.

        @param width Available width
        @param height Available height
        '''
        self.width, self.height = width, height

    def is_expandable(self):
        '''Indicates the Spacer can be expanded'''
        return True

    def size(self, dialog):
        '''Spacer shrinks down to the minimum size for placement.

        @param dialog Dialog which contains us'''
        if dialog is None:
            return

        Widget.size(self, dialog)

        self.width, self.height = self.min_width, self.min_height

class Graphic(Widget):
    '''
    Lays out a graphic from the theme, i.e. part of a title bar.
    '''
    def __init__(self, path, is_expandable=False, group=None, color=None):
        Widget.__init__(self, group=group)
        self.path = path
        self.expandable=is_expandable
        self.graphic = None
        self.min_width = self.min_height = 0
        self.color=color

    def delete(self):
        if self.graphic is not None:
            self.graphic.delete()
            self.graphic = None

    def expand(self, width, height):
        if self.expandable:
            self.width, self.height = width, height
            self.graphic.update(self.x, self.y, self.width, self.height)

    def is_expandable(self):
        return self.expandable

    def layout(self, x, y):
        self.x, self.y = x, y
        self.graphic.update(x, y, self.width, self.height)

    def size(self, dialog):
        if dialog is None:
            return
        Widget.size(self, dialog)
        if self.graphic is None:

            if self.color: color=self.color
            else: color=dialog.theme[self.path]['gui_color']

            template = dialog.theme[self.path]['image']
            self.graphic = template.generate(
                color,
                dialog.batch,
                dialog.fg_group)
            self.min_width = self.graphic.width
            self.min_height = self.graphic.height
        self.width, self.height = self.min_width, self.min_height


class Image(Widget):
    '''
    Lays out a graphic widget from a texture.
    '''
    def __init__(self, texture, color=[255,255,255,255], flag='default', size=None, name=None, is_expandable=False, group=None):
        '''
        Creates a new Image.  The texture is the image that will be displayed.
        The Texture object must expose the following attributes:
            - id  : opengl texture ID (can be 0, which disable texturing)
            - size: texture size (width, height)
            - texcoords : texture coordinates of region to display , formatting (s0,t0, s1, t1)

        @param texture Texture object to be displayed
        @param color Color to apply to Texture
        @param flag
        @param size  Image widget size
        @param name  WidgetName for the widget
        @param is_expandable True to enable expansion if possible
        @param group  WidgetGroup for the widget
        '''
        Widget.__init__(self, name=name, group=group)
        self.texture    = texture
        self.expandable = is_expandable
        self.graphic    = None
        self.min_width  = self.min_height = 0
        self.texture    = texture
        self.color      = color
        self.flag       = flag

        self.width, self.height = size or self.texture.size

    def set_bitmap(self, texture, size=None):
        '''
        Set a new texture for the Image.
        The Texture object must expose the following attributes:
            - id  : opengl texture ID (can be 0, which disable texturing)
            - size: texture size (width, height)
            - texcoords : texture coordinates of region to display , formatting (s0,t0, s1, t1)

        @param texture Texture object to be displayed
        @param size  Image widget size
        '''
        self.texture = texture

        self.width, self.height = size or self.texture.size

        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def delete(self):
        if self.graphic is not None:
            self.graphic.delete()
            self.graphic = None

    def expand(self, width, height):
        if self.expandable:
            self.width, self.height = width, height
            self.graphic.update(self.x, self.y, self.width, self.height)

    def is_expandable(self):
        return self.expandable

    def copy(self):
        """
        Returns copy of Image widget with identical atributes.
        """
        return Image(texture=self.texture,
                     color=self.color,
                     flag=self.flag,
                     size=self.size )

    def layout(self, x, y):
        self.x, self.y = x, y

        self.graphic.update(x, y, self.width, self.height)

    def size(self, dialog):
        if dialog is None:
            return
        Widget.size(self, dialog)
        if self.graphic is None:

            self.graphic =  DefaultTextureGraphicElement( texture=self.texture, color=self.color, size=(self.width, self.height), position=(self.x,self.y),  batch=dialog.batch,  group=dialog.bg_group)

            self.min_width = self.graphic.width
            self.min_height = self.graphic.height

        self.width, self.height = self.min_width, self.min_height

class TextStyle(object):
    def __init__(self, bold=False, italic=False, font_name=None, font_size=None, color=None):
        self.bold=bold
        self.italic=italic
        self.font_name=font_name
        self.font_size=font_size
        self.color=color

class Label(Widget):
    '''
    A wrapper around a simple text label.
    '''
    def __init__(self, text="", name=None, style=None, bold=False, italic=False,
                 font_name=None, font_size=None, color=None, multiline=False, width=None, path=[], group=None):
        Widget.__init__(self, name=name, group=group)

        self.text = string_to_unicode(text)

        if style is not None:
            self.set_text_style(style)
        else:
            self.bold = bold
            self.italic = italic
            self.font_name = font_name
            self.font_size = font_size
            self.color = color

        self.path = path
        self.label = None
        self.is_multiline = multiline
        self.label_width = width

    def delete(self):
        if self.label is not None:
            self.label.teardown()
            self.label = None

    def layout(self, x, y):
        Widget.layout(self, x, y)
        font = self.label.document.get_font()
        self.label.x = int(x)
        self.label.y = int(y + self.height - font.ascent)


    def set_text(self, text):
        '''
        Set Label text
        '''
        self.text = string_to_unicode(text)
        #if self.label is not None:
        #    self.label.text = self.text

        self._update_display()

    def set_text_style(self, style):
        '''
        Set Label text style
        '''
        self.bold = style.bold
        self.italic = style.italic
        self.font_name = style.font_name
        self.font_size = style.font_size
        self.color = style.color

    def set_text_attributes(self, **kwargs):
        '''
        Set Label text attributes.
            - bold True to set font weight to bold
            - italic True to set font style to italic
            - color to set text color. color format: (255,255,255,255)
            - font_size  To set text size
            - font_name To set text font
        '''
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

            # also modify attributes on interal pyglet Label (TextLayout)
            #if self.label is not None:
            #    setattr(self.label, attr, value)

        self._update_display()

    def _update_display(self):
        if self.visible is True:

            self.delete()
            if self.saved_dialog is not None:
                self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        if dialog is None:
            return
        Widget.size(self, dialog)

        if self.label is None:
            self.label = KyttenLabel(
                self.text,
                bold = self.bold,
                italic = self.italic,
                color = self.color or dialog.theme[self.path + ['gui_color']],
                font_name = self.font_name or dialog.theme[self.path + ['font']],
                font_size = self.font_size or dialog.theme[self.path + ['font_size']],
                batch = dialog.batch, group=dialog.fg_group,
                multiline = self.is_multiline,
                width = self.label_width)

        font = self.label.document.get_font()
        self.width = self.label.content_width

        if not self.is_multiline:
            self.height = font.ascent - font.descent
        else:
            self.height = self.label.content_height  - font.descent #font.ascent - font.descent  # descent is negative



class LayoutAssert:
    pass

class FreeLayoutAssert(LayoutAssert):
    pass

class DialogAssert:
    pass

class ScrollableAssert:
    pass

class InteractiveLayoutAssert:
    pass

