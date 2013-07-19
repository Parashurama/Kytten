#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/frame.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"

# Classes which wrap one Widget.

# Wrapper: a base class for Widgets which contain one other Widget.
# Frame: positions its contained Widget within a graphic, which it stretches
#        to cover the Widget's area, or the space within which it is contained.
# TitleFrame: like Frame, but has a title region on top as well.

import weakref
from .widgets import Widget, Control, Graphic, Label, Spacer
from .layout import HorizontalLayout, VerticalLayout, GetRelativePoint
from .layout import VALIGN_BOTTOM, HALIGN_LEFT, HALIGN_CENTER, HALIGN_RIGHT
from .layout import ANCHOR_CENTER
from .base import DisplayGroup, Log
from .theme import Repeat_NinePatchTextureGraphicElement, Stretch_NinePatchTextureGraphicElement, DefaultTextureGraphicElement

class Wrapper(Widget):
    """
    Wrapper is simply a wrapper around a widget.  While the default
    Wrapper does nothing more interesting, subclasses might decorate the
    widget in some fashion, i.e. Panel might place the widget onto a
    panel, or Scrollable might provide scrollbars to let the widget
    be panned about within its display area.
    """
    def __init__(self, content=None, name=None,
                 is_expandable=False, anchor=ANCHOR_CENTER, offset=(0, 0), group=None):
        """
        Creates a new Wrapper around an included Widget.

        @param content The Widget to be wrapped.
        """
        Widget.__init__(self, name=name, group=group)
        self.content = content
        self.hidden_content=None

        self.expandable = is_expandable
        self.anchor = anchor
        self.content_offset = offset
        self.to_refresh=True

        if self.content is not None: self.content.__parent__=weakref.proxy(self)

    def _get_controls(self):
        """Returns Controls contained by the Wrapper."""
        if self.content: return self.content._get_controls()

    def set_content(self, content):
        if self.content is not None:
            self.content.delete()

        self.content = content
        content.__parent__=weakref.proxy(self)

        if self.hidden_content is not None:
            self.hidden_content.delete()
            self.hidden_content=None

    def delete_content(self):
        if self.content is not None:
            self.content.delete()
            self.content = None

        if self.hidden_content is not None:
            self.hidden_content.delete()
            self.hidden_content = None

    def delete(self):
        """Deletes graphic elements within the Wrapper."""
        if self.content is not None:
            self.content.delete()

        if self.hidden_content is not None:
            self.hidden_content.delete()
        Widget.delete(self)

    def expand(self, width, height):
        if self.content is not None:
            if self.content.is_expandable():
                self.content.expand(width, height)
            self.width = width
            self.height = height

    def is_expandable(self):
        return self.expandable

    def layout(self, x, y):
        """
        Assigns a new position to the Wrapper.

        @param x X coordinate of the Wrapper's lower left corner
        @param y Y coordinate of the Wrapper's lower left corner
        """
        Widget.layout(self, x, y)
        if self.content is not None:
            x, y = GetRelativePoint(
                self, self.anchor,
                self.content, self.anchor, self.content_offset)
            self.content.layout(x, y)

    def set(self, dialog, content):
        """
        Sets a new Widget to be contained in the Wrapper.

        @param dialog The Dialog which contains the Wrapper
        @param content The new Widget to be wrapped
        """
        if self.content is not None:
            self.content.delete()

        self.content = content
        dialog.set_needs_layout()

    def size(self, dialog):
        """
        The default Wrapper wraps up its Widget snugly.

        @param dialog The Dialog which contains the Wrapper
        """
        if dialog is None:
            return
        Widget.size(self, dialog)

        if self.content is not None:
            self.content.size(dialog)

            self.width, self.height = self.content.width, self.content.height
        else:
            self.width = self.height = 0
    """
    def Set(self):
        Widget.Set(self)
        self.to_refresh=True"""

    def Hide(self):
        if self.visible:

            if self.content:
                self.content.Hide()

            self.delete()
            if self.saved_dialog:
                self.saved_dialog.set_needs_layout()
            else: # Top Level Wrapper
                if hasattr(self,'set_needs_layout'): self.set_needs_layout()

            Widget.Hide(self)

            self.visible=False

    def Show(self):
        if not self.visible:

            if self.content:
                self.content.Show()

            elif self.hidden_content:
                self.hidden_content.Show()

            if self.saved_dialog:
                self.saved_dialog.set_needs_layout()
            else: # Top Level Wrapper
                if hasattr(self,'set_needs_layout'): self.set_needs_layout()

            Widget.Show(self)

            self.visible=True

    def __rereference_obj__(self, *args):
        #if not self.visible: return

        self.content = self.hidden_content
        self.hidden_content = None

        if Log.isLogging(): print "ReReference in Wrapper", self, self.content, self.hidden_content#, self.content.name

        if self.saved_dialog:
            self.saved_dialog.set_needs_layout()
        else: # Top Level Wrapper
            if hasattr(self,'set_needs_layout'): self.set_needs_layout()

    def __dereference_obj__(self, *args):
        #if not self.visible: return

        self.hidden_content = self.content
        self.content = None

        if Log.isLogging(): print "DeReference in Wrapper", self, self.hidden_content, self.hidden_content.name

        if self.saved_dialog:
            self.saved_dialog.set_needs_layout()
        else: # Top Level Wrapper
            if hasattr(self,'set_needs_layout'): self.set_needs_layout()

    def delete(self):
        if self.content is not None:
            if not self.visible: self.content.visible=False
            self.content.delete()

    def teardown(self):
        if self.content is not None:
            self.content.teardown()
            self.content = None

        if self.hidden_content is not None:
            self.hidden_content.teardown()
            self.hidden_content = None

        Widget.teardown(self)

class Frame(Wrapper):
    """
    Frame draws an untitled frame which encloses the dialog's content.
    """
    def __init__(self, content=None, path=['frame'], image_name='image',
                 is_expandable=False, anchor=ANCHOR_CENTER,
                 use_bg_group=False, color=None, group=None, name=None):
        """
        Creates a new Frame surrounding a widget or layout.
        """
        Wrapper.__init__(self, content,
                         is_expandable=is_expandable, anchor=anchor, group=group, name=name)
        self.frame = None
        self.path = path
        self.image_name = image_name
        self.use_bg_group = use_bg_group
        self.disabled_flag = False
        self.color=color

    def is_disabled(self):
        return self.disabled_flag

    def disable(self):
        self.disabled_flag=True
        self.delete()
        self.set_needs_layout()

    def enable(self):
        self.disabled_flag=False
        self.delete()
        self.set_needs_layout()

    def delete(self):
        """
        Removes the Frame's graphical elements.
        """
        if self.frame is not None:
            self.frame.delete()
            self.frame = None

        Wrapper.delete(self)

    def expand(self, width, height):
        if self.content.is_expandable():
            content_width, content_height = \
                         self.frame.get_content_size(width, height)
            self.content.expand(content_width, content_height)
        self.width, self.height = width, height

    def layout(self, x, y):
        """
        Positions the Frame.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        if not self.visible or not self.content: return

        self.x, self.y = x, y
        self.frame.update(x, y, self.width, self.height)

        # In some cases the frame graphic element may allocate more space for
        # the content than the content actually fills, due to repeating
        # texture constraints.  Always center the content.
        x, y, width, height = self.frame.get_content_region()
        interior = Widget(width, height, spacer=True)
        interior.x, interior.y = x, y
        x, y = GetRelativePoint(interior, self.anchor,
                                self.content, self.anchor, self.content_offset)
        self.content.layout(x, y)

    def size(self, dialog):
        """
        Determine minimum size of the Frame.

        @param dialog Dialog which contains the Frame
        """
        if dialog is None:
            return

        Wrapper.size(self, dialog)

        if not self.visible or not self.content:
            self.width=self.height=0
            return

        if self.frame is None:
            if self.use_bg_group:
                group = dialog.bg_group
            else:
                group = dialog.panel_group
            template = dialog.theme[self.path][self.image_name]

            if not self.color:
                if self.is_disabled(): color = dialog.theme[self.path]['disabled_color']
                else: color = dialog.theme[self.path]['gui_color']
            else: color = self.color

            self.frame = template.generate(
                color,
                dialog.batch,
                group)

        self.width, self.height = self.frame.get_needed_size(
            self.content.width, self.content.height)

class TransparentFrame(Frame):
    def __init__(self, content=None, path=['transparent_frame'], image_name='image',
                 is_expandable=False, anchor=ANCHOR_CENTER,
                 use_bg_group=False):

        Frame.__init__(self, content=content, path=path, image_name=image_name, is_expandable=is_expandable, anchor=anchor, use_bg_group=use_bg_group)
        self._header_bar = (0,0,0,0)
    def header_bar_hit_test(self, x, y):
        #Disable Dragging for Transparent Frame
        return False

class GuiFrame(Frame):
    def __init__(self, content=None, texture=None, is_expandable=False, anchor=ANCHOR_CENTER, use_bg_group=False, group=None, name=None, flag='default'):

        Wrapper.__init__(self, content, is_expandable=is_expandable, anchor=anchor, group=group, name=name)

        self.frame = None
        self.use_bg_group = use_bg_group
        self.disabled_flag = False

        self.set_texture(texture, flag)

    def expand(self, width, height):
        if self.content.is_expandable():
            content_width, content_height = \
                         self.frame.get_content_size(width, height)
            self.content.expand(content_width, content_height)
        self.width, self.height = width, height

    def set_texture(self, texture, flag='default'):
        self._header_bar=texture.header_bar
        self._texture = texture
        self._flag = flag
        if not flag in ('repeat', 'stretch', 'default'):
            raise ValueError("Invalid Texture Flag Declaration in GUIFRame: must be 'repeat','stretch' or 'default' ")

    def size(self, dialog):
        """
        Determine minimum size of the Frame.

        @param dialog Dialog which contains the Frame
        """
        if dialog is None:
            return

        Wrapper.size(self, dialog)

        if not self.visible or not self.content:
            self.width=self.height=0
            return

        if self.frame is None:
            if self.use_bg_group:
                group = dialog.bg_group
            else:
                group = dialog.panel_group

            if   self._flag == 'repeat':
                self.frame = Repeat_NinePatchTextureGraphicElement(texture=self._texture, size=(self.width, self.height), position=(self.x,self.y),  batch=dialog.batch,  group=group)
            elif self._flag == 'stretch':
                self.frame = Stretch_NinePatchTextureGraphicElement(texture=self._texture, size=(self.width, self.height), position=(self.x,self.y),  batch=dialog.batch,  group=group)
            else:
                self.frame = DefaultTextureGraphicElement(texture=self._texture, size=(self.width, self.height), position=(self.x,self.y),  batch=dialog.batch,  group=group)

        self.width, self.height = self.frame.get_needed_size( self.content.width, self.content.height)

    def layout(self, x, y):
        '''
        Positions the Frame.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        '''
        if not self.visible or not self.content: return

        self.x, self.y = x, y
        self.frame.update(x, y, self.width, self.height)

        '''
        # In some cases the frame graphic element may allocate more space for
        # the content than the content actually fills, due to repeating
        # texture constraints.  Always center the content.
        '''
        x, y, width, height = self.frame.get_content_region()

        interior = Widget(width, height, spacer=True)
        interior.x, interior.y = x, y

        x, y = GetRelativePoint(interior, self.anchor,
                                self.content, self.anchor, self.content_offset)

        self.content.layout(x, y)


class TitleFrame(VerticalLayout):
    def __init__(self, title, content):
        VerticalLayout.__init__(self, content=[
                HorizontalLayout([
                    Graphic(path=["titlebar", "left"], is_expandable=True),
                    Frame(Label(title, path=["titlebar"]),
                          path=["titlebar", "center"]),
                    Graphic(path=["titlebar", "right"], is_expandable=True),
                ], align=VALIGN_BOTTOM, padding=0),
                Frame(content, path=["titlebar", "frame"], is_expandable=True),
            ], padding=0)

class SectionHeader(HorizontalLayout):
    def __init__(self, title, align=HALIGN_CENTER):
        if align == HALIGN_LEFT:
            left_expand = False
            right_expand = True
        elif align == HALIGN_CENTER:
            left_expand = True
            right_expand = True
        else:  # HALIGN_RIGHT
            left_expand = True
            right_expand = False

        HorizontalLayout.__init__(self, content=[
                Graphic(path=["section", "left"], is_expandable=left_expand),
                Frame(Label(title, path=["section"]),
                      path=['section', 'center'],
                      use_bg_group=True),
                Graphic(path=["section", "right"], is_expandable=right_expand),
            ], align=VALIGN_BOTTOM, padding=0)

class FoldingSection(Control, VerticalLayout):
    def __init__(self, title, content=None, is_open=True, align=HALIGN_CENTER, color=None):
        Control.__init__(self)
        if align == HALIGN_LEFT:
            left_expand = False
            right_expand = True
        elif align == HALIGN_CENTER:
            left_expand = True
            right_expand = True
        else:  # HALIGN_RIGHT
            left_expand = True
            right_expand = False

        self.is_open = is_open
        self.folding_content = content
        self.book = Graphic(self._get_image_path())
        self.main_color=None

        self.header_group = DisplayGroup()

        self.header = HorizontalLayout([
            Graphic(path=["section", "left"], is_expandable=left_expand, group=self.header_group),
            Frame(HorizontalLayout([
                      self.book,
                      Label(title, path=["section"], group=self.header_group),
                  ]), path=["section", "center"],
                  use_bg_group=True, group=self.header_group),
            Graphic(path=["section", "right"], is_expandable=right_expand, group=self.header_group),
            ], align=VALIGN_BOTTOM, padding=0)

        layout = [self.header]
        if self.is_open:
            layout.append(content)

        VerticalLayout.__init__(self, content=layout, align=align)

    def _get_controls(self):
        return VerticalLayout._get_controls(self) + \
               [(self, self.header.x, self.header.x + self.header.width,
                       self.header.y + self.header.height, self.header.y)]

    def _get_image_path(self):
        if self.is_open:
            return ["section", "opened"]
        else:
            return ["section", "closed"]

    def hit_test(self, x, y):
        return self.header.hit_test(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.is_open = not self.is_open
        try:
            if self.is_open:
                self.add(self.folding_content)
                self.folding_content.Show()
            else:
                self.folding_content.Hide()
                self.remove(self.folding_content)
                #self.folding_content.delete()
        except ValueError: # Bug d'affichage
            self.on_mouse_press( x, y, button, modifiers)

        self.book.delete()
        self.book.path = self._get_image_path()

    def delete(self):

        if self.header is not None:
            self.header.delete()

        if self.folding_content:
            self.folding_content.delete()

        if self.book is not None:
            self.book.delete()

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def size(self, dialog):

        if self.is_disabled():  colorpath = 'disabled_color'
        else: colorpath = 'gui_color'

        for member in self.header_group:
            member.color= self.main_color or dialog.theme[member.path][colorpath]

        self.book.path = self._get_image_path()
        self.book.color = self.main_color or dialog.theme[self.book.path][colorpath]

        VerticalLayout.size(self, dialog)

    def disable(self):
        self.disabled_flag=True
        self.delete()

    def enable(self):
        self.disabled_flag=False
        self.delete()

    def teardown(self):
        self.folding_content.teardown()
        self.folding_content = None
        VerticalLayout.teardown(self)
