#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/button.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import pyglet
import weakref
from .widgets import Control, InteractiveLayoutAssert
from .override import KyttenLabel
from .base import  GetObjectfromName, CVars, string_to_unicode
from .theme import DefaultTextureGraphicElement

class Button(Control):
    '''
    A simple text-labeled button.
    '''
    def __init__(self, text="", name=None, on_click=None, on_double_click=None, group=None, on_gain_hover=None, on_lose_hover=None, disabled=False):
        '''
        Creates a new Button.  The provided text will be used to caption the button.

        @param text  Label for the button
        @param name  WidgetName for the button
        @param on_click  Callback for the button
        @param on_double_click  Callback for the button
        @param group  WidgetGroup for the button
        @param on_gain_hover  Callback for the button
        @param on_lose_hover  Callback for the button
        @param disabled True  if the button should be disabled
        '''
        Control.__init__(self, name=name, on_gain_hover=on_gain_hover, group=group, on_lose_hover=on_lose_hover, disabled=disabled)
        self.text = string_to_unicode(text)
        self.on_click = on_click
        self.on_double_click_func = on_double_click
        self.label = None
        self.button = None
        self.highlight = None
        self.is_pressed = False

    def set_text(self, text):
        '''
        Set Text for the button
        '''
        self.text=string_to_unicode(text)
        self._force_refresh()

    def delete(self):
        '''
        Clean up our graphic elements
        '''
        Control.delete(self)
        if self.button is not None:
            self.button.delete()
            self.button = None
        if self.label is not None:
            self.label.delete()
            self.label = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def layout(self, x, y):
        '''
        Places the Button.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        '''
        Control.layout(self, x, y)
        self.button.update(self.x, self.y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(self.x, self.y, self.width, self.height)
        x, y, width, height = self.button.get_content_region()
        font = self.label.document.get_font()
        self.label.x = x + width/2 - self.label.content_width/2
        self.label.y = y + height/2 - font.ascent/2 - font.descent

    def on_gain_highlight(self):
        '''
        If mouse hovers the button, display highlight
        '''
        Control.on_gain_highlight(self)

        saved_dialog = self.scrollable_parent if self.scrollable_parent is not None else self.saved_dialog
        path = ['button', 'down'] if self.is_pressed else ['button', 'up']

        if self.highlight is None and self.is_highlight():
            self.highlight = self.saved_dialog.theme[path]['highlight']['image'].generate(
                color=self.saved_dialog.theme[path]['highlight_color'],
                batch=saved_dialog.batch,
                group=saved_dialog.highlight_group)
            self.highlight.update(self.x, self.y, self.width, self.height)

    def on_lose_highlight(self):
        '''
        When the mouse leaves the button, delete highlight
        '''
        Control.on_lose_highlight(self)
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def on_mouse_press(self, x, y, button, modifiers):
        '''
        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button pressed
        @param modifiers Modifiers to apply to button
        '''
        if not self.is_pressed and not self.is_disabled():
            self.is_pressed = True

            self._force_refresh()

    def on_mouse_release(self, x, y, button, modifiers):
        '''
        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button pressed
        @param modifiers Modifiers to apply to button
        '''
        if self.is_pressed is True:
            self.is_pressed = False

            self._force_refresh()

            # Now, if mouse is still inside us, signal on_click
            if self.on_click is not None and self.hit_test(x, y):
                self.on_click(self)
                return pyglet.event.EVENT_HANDLED

    def on_mouse_double_click(self, x, y, button, modifiers):
        '''
        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button pressed
        @param modifiers Modifiers to apply to button
        '''
        if self.on_double_click_func is not None:
            self.on_double_click_func(self, x, y, button, modifiers)

    def size(self, dialog):
        '''
        Sizes the Button.  If necessary, (re)creates the graphic elements.

        @param dialog Dialog which contains the Button
        '''
        if dialog is None:
            return
        Control.size(self, dialog)
        if self.is_pressed:
            path = ['button', 'down']
        else:
            path = ['button', 'up']
        if self.is_disabled():
            color = dialog.theme[path]['disabled_color']
        else:
            color = dialog.theme[path]['gui_color']
        if self.button is None:
            self.button = dialog.theme[path]['image'].generate(
                color,
                dialog.batch, dialog.bg_group)
        if self.highlight is None and self.is_highlight():
            self.highlight = dialog.theme[path]['highlight']['image'].\
                generate(dialog.theme[path]['highlight_color'],
                         dialog.batch,
                         dialog.highlight_group)
        if self.label is None:
            self.label = KyttenLabel(self.text,
                font_name=dialog.theme[path]['font'],
                font_size=dialog.theme[path]['font_size'],
                color=dialog.theme[path]['text_color'],
                batch=dialog.batch, group=dialog.fg_group)

        # Treat the height of the label as ascent + descent
        font = self.label.document.get_font()
        height = font.ascent - font.descent # descent is negative
        self.width, self.height = self.button.get_needed_size(
            self.label.content_width, height)

    def teardown(self):
        '''
        Destroy the button definitively
        '''
        self.on_click = None
        Control.teardown(self)

class ButtonStyle(object):
    '''
    A simple class to manage styles for ImageButton
    '''
    def __init__(self,  default,
                        hover=None,
                        clicked=None,
                        size=None, square=True,
                        has_border=True,
                        text_style={},
                        is_expandable=False,
                        on_click=None,
                        on_gain_hover=None,
                        on_lose_hover=None ):
        '''
        Create a new ButtonStyle. The provided data will used to style other ImageButtons

        @param default  Default image for the button
        @param hover  Image for the mouse is hovering above the button. If not provided, defaults image is used
        @param clicked  Image when the button is clicked. If not provided, defaults image is used
        @param size  Set button Size
        @param square  Button shape is square
        @param has_border  Boolean. To Display GuiStyle borders
        @param text_style  Text style for the button
        @param on_click Callback  for the button
        @param on_gain_hover  Callback for the button
        @param on_lose_hover  Callback for the button
        '''
        self.default_image = default

        if hover: self.hover_image = hover
        else :    self.hover_image = default

        if clicked: self.clicked_image = clicked
        else :      self.clicked_image = default

        self.on_click = on_click
        self.on_gain_hover_func = on_gain_hover
        self.on_lose_hover_func = on_lose_hover

        self.square  = square
        self.text_style = text_style
        self.fixed_size = size
        self.has_border = has_border
        self.expandable = is_expandable

class ImageButton(Button):
    '''
    A simple class to manage styles for ImageButton
    '''
    padding = 8
    expandable = False
    def  __init__(self, image=None,
                        color=(255,255,255,255),
                        style=None,
                        size=None,
                        text='',
                        name=None,
                        on_click=None,
                        on_double_click=None,
                        on_gain_hover=None,
                        on_lose_hover=None,
                        disabled=False,
                        text_style={},
                        padding=8,
                        group=None,
                        square=True,
                        has_border=False):
        '''
        Create a new ButtonStyle. The provided data will used to style other ImageButtons

        @param image  Default image for the button
        @param color  Colorize Texture for the button
        @param style  ButtonStyle to use on button
        @param size  Set button Size
        @param text  Label for the button
        @param name  WidgetName for the button
        @param on_click  Callback for the button
        @param on_gain_hover  Callback for the button
        @param on_lose_hover  Callback for the button
        @param disabled  True if the button should be disabled
        @param text_style  Text style for the button
        @param padding
        @param group  DisplayGroup
        @param square  Button shape is square
        @param has_border  True to display GuiStyle borders
        '''
        Button.__init__(self, name=name, text=text, on_click=on_click, on_double_click=on_double_click, group=group, on_gain_hover=on_gain_hover, on_lose_hover=on_lose_hover, disabled=disabled)
        self.bitmap = None

        if style is not None:
            self.set_button_style(style, False)
            if image: self.default_image=image
            self.text_style = self.text_style.copy()
            self.text_style.update(text_style)
        else:
            self.default_image = image
            self.hover_image = image
            self.clicked_image = image
            self.fixed_size = size
            self.square = square
            self.has_border = has_border
            self.text_style = text_style

        self.padding=padding
        self.image = self.default_image
        self.color = color

        if on_click is not None: self.on_click=on_click
        if on_gain_hover is not None: self.on_gain_hover_func = on_gain_hover
        if on_lose_hover is not None: self.on_lose_hover_func = on_lose_hover

    def set_button_style(self, button_style, force_refresh=True):
        '''
        Assign Button Style to ImageButton
        '''
        self.default_image = button_style.default_image
        self.hover_image = button_style.hover_image
        self.clicked_image = button_style.clicked_image
        self.fixed_size = button_style.fixed_size
        self.square = button_style.square
        self.has_border = button_style.has_border
        self.expandable = button_style.expandable
        self.on_click = button_style.on_click
        self.on_gain_hover_func = button_style.on_gain_hover_func
        self.on_lose_hover_func = button_style.on_lose_hover_func
        self.text_style=button_style.text_style.copy()

        if force_refresh is True: self._force_refresh()

    def set_color(self, color=(255,255,255,255)):
        '''
        Set texture color to button
        '''
        self.color = color

        self._force_refresh()

    def set_bitmaps(self, default_image=None, hover_image=None, clicked_image=None):
        '''
        Set button bitmaps
        '''
        if default_image is not None: self.default_image = default_image
        if hover_image   is not None: self.hover_image   = hover_image
        if clicked_image is not None: self.clicked_image = clicked_image

        self.image = default_image

        self._force_refresh()

    def layout(self,x, y):

        Control.layout(self, x, y)

        if self.has_border is True: # Has a Border
            self.button.update(self.x, self.y, self.width, self.height)
            x, y, width, height = self.button.get_content_region()

        # put the graphic into the button center
        if self.bitmap is not None:
            x = self.x + (self.width - self.bitmap.width) // 2
            y = self.y + (self.height - self.bitmap.height) // 2

            widget_width, widget_height = self.bitmap.width, self.bitmap.height
            self.bitmap.update(x,y)
        else:
            x = self.x
            y = self.y
            widget_width, widget_height = self.width, self.height

        if self.label is not None:
            font = self.label.document.get_font()
            TEXT_ANCHOR = self.text_style.get('text_anchor', CVars.ANCHOR_CENTER)
            LEFT, RIGHT, TOP, BOTTOM = self.text_style.get('text_padding', (0,0,0,0))

            if   TEXT_ANCHOR is CVars.ANCHOR_CENTER:
                self.label.x = x + widget_width//2 - self.label.content_width//2
                self.label.y = y + widget_height//2 - (font.ascent + font.descent )//2
            elif TEXT_ANCHOR is CVars.ANCHOR_BOTTOM_RIGHT:
                self.label.x = x + widget_width - self.label.content_width - RIGHT
                self.label.y = y + BOTTOM
            elif TEXT_ANCHOR is CVars.ANCHOR_RIGHT:
                self.label.x = x + widget_width - self.label.content_width - RIGHT
                self.label.y = y + widget_height//2 - (font.ascent + font.descent )//2
            elif TEXT_ANCHOR is CVars.ANCHOR_TOP_RIGHT:
                self.label.x = x + widget_width - self.label.content_width - RIGHT
                self.label.y = y + widget_height - (font.ascent + font.descent ) - TOP
            elif TEXT_ANCHOR is CVars.ANCHOR_TOP:
                self.label.x = x + widget_width//2 - self.label.content_width//2
                self.label.y = y + widget_height - (font.ascent + font.descent ) - TOP
            elif TEXT_ANCHOR is CVars.ANCHOR_TOP_LEFT:
                self.label.x = x + LEFT
                self.label.y = y + widget_height - (font.ascent + font.descent ) - TOP
            elif TEXT_ANCHOR is CVars.ANCHOR_LEFT:
                self.label.x = x + LEFT
                self.label.y = y + widget_height//2 - (font.ascent + font.descent )//2
            elif TEXT_ANCHOR is CVars.ANCHOR_BOTTOM_LEFT:
                self.label.x = x + LEFT
                self.label.y = y + BOTTOM
            elif TEXT_ANCHOR is CVars.ANCHOR_BOTTOM:
                self.label.x = x + widget_width//2 - self.label.content_width//2
                self.label.y = y + BOTTOM
            else:
                raise TypeError

    def size(self, dialog):
        Control.size(self, dialog)

        content_width, content_height = 0, 0

        if self.is_pressed:  path = ['button', 'down']
        else:                path = ['button', 'up']

        if self.has_border is True: # Has a Border

            if self.is_disabled(): color = dialog.theme[path]['disabled_color']
            else: color = dialog.theme[path]['gui_color']

            if self.button is None:
                self.button = dialog.theme[path]['image'].generate( color, dialog.batch, dialog.bg_group)

        if self.text and self.label is None: #if label is None and button has text, recreate label
            self.label = KyttenLabel(self.text,
                                     font_name=self.text_style.get('font', None) or dialog.theme[path]['font'],
                                     font_size=self.text_style.get('font_size', None) or dialog.theme[path]['font_size'],
                                     color=self.text_style.get('text_color', None) or dialog.theme[path]['text_color'],
                                     bold = self.text_style.get('bold', False),
                                     batch=dialog.batch, group=dialog.fg_group)

        if self.label is not None: #if button has text, get label size
            font = self.label.document.get_font()
            height = font.ascent - font.descent # descent is negative
            left_padding, right_padding, top_padding, bottom_padding = self.text_style.get('text_padding', (0,0,0,0))

            content_width = max(content_width, self.label.content_width + left_padding + right_padding)
            content_height= max(content_height, height + top_padding + bottom_padding)

        if self.visible is True and self.image is not None:
            if self.bitmap is None:
                self.bitmap = DefaultTextureGraphicElement(texture=self.image, batch=dialog.batch, group=dialog.bg_group, color=self.color)


            if self.fixed_size:
                if self.square is True or self.image.height == self.image.width:
                    self.bitmap.height=self.bitmap.width=float(self.fixed_size)

                else :
                    if   self.image.width > self.image.height:
                        self.bitmap.height=self.image.height*self.fixed_size/float(self.image.width)
                        self.bitmap.width=float(self.fixed_size)

                    elif self.image.width < self.image.height:
                        self.bitmap.width=self.image.width*self.fixed_size/float(self.image.height)
                        self.bitmap.height=float(self.fixed_size)
                    else:
                        self.bitmap.height=self.bitmap.width=float(self.fixed_size)
            else:
                self.bitmap.width  = float(self.image.width)
                self.bitmap.height = float(self.image.height)

            content_width = max(content_width, self.bitmap.width)
            content_height= max(content_height, self.bitmap.height)

            self.bitmap.width, self.bitmap.height  = self.bitmap.get_needed_size(content_width, content_height)


            if self.square is True :
                self.width = self.height = content_width = content_height = max(self.bitmap.width, self.bitmap.height)
            else:
                self.width, self.height = content_width,content_height  = self.bitmap.width,self.bitmap.height

        if self.has_border is True:
            self.width, self.height = self.button.get_needed_size(content_width, content_height)

            self.width+=self.padding * 2
            self.height+=self.padding * 2
        else:
            self.width, self.height = content_width, content_height

    def is_expandable(self):
        return self.expandable

    def expand(self, width, height):
        if self.expandable:
            self.width, self.height = width, height
            self.bitmap.update(self.x, self.y, self.width, self.height)

    def on_gain_highlight(self):
        self.image = self.hover_image

        Control.on_gain_highlight(self)

        self._force_refresh()

    def on_lose_highlight(self):
        self.image = self.default_image
        Control.on_lose_highlight(self)

        self._force_refresh()

    def on_mouse_press(self, x, y, button, modifiers):
        self.image = self.clicked_image
        Button.on_mouse_press(self, x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if not self.highlight_flag:  self.image = self.default_image
        else:                        self.image = self.hover_image
        Button.on_mouse_release(self, x, y, button, modifiers)

    def delete(self):
        Button.delete(self)
        if self.bitmap is not None:
            self.bitmap.delete()
            self.bitmap=None


class DraggableImageButton(ImageButton):
    _old_parent=None
    _is_dragging=False
    _is_copying=False

    def __init__(self, image=None, style=None, copy=True, *args, **kwargs):
        ImageButton.__init__(self, image=image, style=style, *args, **kwargs)
        self._is_copying=copy

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        DRAGGABLE=weakref.proxy(GetObjectfromName('DRAGGABLE'))

        if not self._is_dragging:
            self._old_parent=self._parent

            if   self._is_copying is True:

                NEW = DraggableImageButton( image=self.default_image,copy=True)
                NEW.set_button_style(self)

                if  isinstance(self._old_parent, InteractiveLayoutAssert):
                    self._old_parent_layout_info = self._parent.remove(self, False)
                    self._parent.add( NEW , self._old_parent_layout_info[1])
                else:
                    self._old_parent_layout_info, index = self._parent.remove(self)
                    self._parent.add( *( self._old_parent_layout_info[:-1]+(NEW,) ) )

            elif self._is_copying is False:

                if  isinstance(self._parent, InteractiveLayoutAssert):
                    item,index = self._old_parent_layout_info = self._parent.remove(self)
                else:
                    (anchor, x, y, item), index = self._old_parent_layout_info = self._parent.remove(self)

                self._parent.dispatch_event('on_drag_object', self._parent, self, index)

            else:# self._is_copying is None # Emulate Dragging
                self.delete()

            DRAGGABLE.set_content(self)
            DRAGGABLE.offset=(self.x,self.y)
            DRAGGABLE.needs_layout = True
            self._old_parent.saved_dialog.dont_pop_to_top=True
            self._old_parent.saved_dialog.set_focus(None)
            DRAGGABLE.set_focus(self)
            DRAGGABLE.pop_to_top()

            self._is_dragging=True

            return pyglet.event.EVENT_HANDLED

        X,Y = DRAGGABLE.offset
        DRAGGABLE.set_focus(self)
        DRAGGABLE.offset=(X+dx,Y+dy)
        DRAGGABLE.set_needs_layout()

        return pyglet.event.EVENT_HANDLED

    def on_mouse_release(self, x, y, button, modifiers):
        if self._is_dragging:
            DRAGGABLE=GetObjectfromName('DRAGGABLE')
            NEW_POSITION = DRAGGABLE.check_position(int(self.x +self.width/2.),int(self.y+self.height/2.))

            Widget=None

            if NEW_POSITION is None :
                if not self._is_copying:
                    if isinstance(self._old_parent, InteractiveLayoutAssert):
                        self._old_parent.set( *self._old_parent_layout_info)
                    else:
                        self._old_parent.set_widget( *self._old_parent_layout_info)
                    self._old_parent.saved_dialog.pop_to_top()
                    self._old_parent.saved_dialog.set_focus(self)
                    self._old_parent.dispatch_event('on_drop_object', self._old_parent, self, self._old_parent_layout_info[1])
                    self.delete()

                else:
                    self.teardown()

            else:
                New_Parent, position, widget = NEW_POSITION
                New_Parent.dispatch_event('on_drop_object', New_Parent, self, position)

                Widget, _ = New_Parent.remove(widget, False)
                New_Parent.add(self, position)
                New_Parent.saved_dialog.pop_to_top()
                self._is_copying=False
                self.delete()

            DRAGGABLE.set_focus(None)
            DRAGGABLE.set_needs_layout()
            DRAGGABLE.delete_content()
            DRAGGABLE._emul_dragging=False

            self._old_parent=None
            self._old_parent_layout_info=None
            self._is_dragging=False

            if isinstance(Widget, DraggableImageButton):
                Widget._is_copying=None
                Widget.on_mouse_drag( x, y, 0, 0, button, modifiers)
                DRAGGABLE._emul_dragging=True

            return pyglet.event.EVENT_HANDLED

    def on_gain_hover(self,*args):
        if self._is_dragging is True: return True
        Control.on_gain_hover(self,*args)

    def on_lose_hover(self,*args):
        if self._is_dragging is True: return True
        Control.on_lose_hover(self,*args)

DraggableImageButton.register_event_type('on_mouse_drag')
DraggableImageButton.register_event_type('on_mouse_release')
