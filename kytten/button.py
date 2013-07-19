#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/button.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"

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
        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

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
        self.size(self.saved_dialog)
        if self.highlight is not None:
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

            # Delete the button to force it to be redrawn
            self.delete()
            if self.saved_dialog is not None:
                self.saved_dialog.set_needs_layout()


    def on_mouse_release(self, x, y, button, modifiers):
        '''
        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button pressed
        @param modifiers Modifiers to apply to button
        '''
        if self.is_pressed:
            self.is_pressed = False

            # Delete the button to force it to be redrawn
            self.delete()
            if self.saved_dialog is not None:
                self.saved_dialog.set_needs_layout()

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
    A simple class to manage styles for ImagesButton
    '''
    def __init__(self,  default,
                        hover=None,
                        clicked=None,
                        size=None, square=True,
                        no_border=True,
                        text_style={},
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
        @param no_border  Boolean. To Display GuiStyle borders
        @param text_style  Text style for the button
        @param on_click Callback  for the button
        @param on_gain_hover  Callback for the button
        @param on_lose_hover  Callback for the button
        '''
        self.default_image = default

        if hover : self.hover_image = hover
        else : self.hover_image = default

        if clicked : self.clicked_image = clicked
        else : self.clicked_image = default

        self.on_click = on_click
        self.on_gain_hover_func = on_gain_hover
        self.on_lose_hover_func = on_lose_hover

        self.text_style=text_style
        self.fixed_size = size
        self.square = square
        self.no_border = no_border

    def SetStyle(self, button):
        '''
        Assign Style to ImageButton
        '''
        button.default_image = self.default_image
        button.hover_image = self.hover_image
        button.clicked_image = self.clicked_image
        button.fixed_size = self.fixed_size
        button.square = self.square
        button.no_border = self.no_border
        button.on_click = self.on_click
        button.on_gain_hover_func = self.on_gain_hover_func
        button.on_lose_hover_func = self.on_lose_hover_func
        button.text_style=self.text_style

class ImageButton(Button):
    '''
    A simple class to manage styles for ImagesButton
    '''
    padding = 8

    def  __init__(self, image=None,
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
                        no_border=True):
        '''
        Create a new ButtonStyle. The provided data will used to style other ImageButtons

        @param image  Default image for the button
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
        @param padding
        @param square  Button shape is square
        @param no_border  True to display GuiStyle borders
        '''

        Button.__init__(self, name=name, text=text, on_click=on_click, on_double_click=on_double_click, group=group, on_gain_hover=on_gain_hover, on_lose_hover=on_lose_hover, disabled=disabled)
        self.bitmap = None

        self.image_arg=style
        if isinstance( style, ButtonStyle ):
            style.SetStyle(self)
            if image:
                self.default_image=image
        else:
            self.default_image = image
            self.hover_image = image
            self.clicked_image = image
            self.fixed_size = size
            self.square = square
            self.no_border = no_border

        self.padding=padding
        self.text_style = text_style
        self.image = self.default_image
        self.colors = [255,255,255,255]

        if on_click: self.on_click=on_click
        if on_gain_hover: self.on_gain_hover_func = on_gain_hover
        if on_lose_hover: self.on_lose_hover_func = on_lose_hover

    def set_color(self, colors=[255,255,255,255]):
        self.colors = colors

        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def set_bitmaps(self, default_image=None, hover_image=None, clicked_image=None):
        if default_image : self.default_image = default_image
        if hover_image   : self.hover_image = hover_image
        if clicked_image : self.clicked_image = clicked_image

        self.image = default_image

        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def layout(self,x, y):

        Control.layout(self, x, y)

        if not self.no_border: # Has a Border
            self.button.update(self.x, self.y, self.width, self.height)
            x, y, width, height = self.button.get_content_region()

        # put the graphic into the button center (take padding into account)
        if self.bitmap:
            x= self.x + self.padding + (  (self.width - self.padding * 2 - self.bitmap.width) / 2)
            y= self.y + self.padding + (  (self.height - self.padding * 2 - self.bitmap.height) / 2)

            self.bitmap.update(x,y)
        else:
            x= self.x + self.padding
            y= self.y + self.padding

        if self.label:
            font = self.label.document.get_font()
            TEXT_ANCHOR = self.text_style.get('text_anchor', None)
            if   TEXT_ANCHOR in (None, CVars.ANCHOR_CENTER):
                self.label.x = x + self.width/2 - self.label.content_width/2-self.padding
                self.label.y = y + self.height/2 - (font.ascent + font.descent )/2-self.padding

            elif TEXT_ANCHOR is CVars.ANCHOR_BOTTOM_RIGHT:
                self.label.x = x + self.width - self.label.content_width-5
                self.label.y = y + (font.ascent + font.descent )+self.padding
            elif TEXT_ANCHOR is CVars.ANCHOR_TOP_RIGHT:
                self.label.x = x + self.width - self.label.content_width-self.padding
                self.label.y = y + self.height - (font.ascent + font.descent )-self.padding
            else:
                raise TypeError

    # kytten size request override to take graphic size into account
    def size(self, dialog):
        Control.size(self, dialog)

        if self.is_pressed:  path = ['button', 'down']
        else:                path = ['button', 'up']

        if not self.no_border: # Has a Border

            if self.is_disabled(): color = dialog.theme[path]['disabled_color']
            else: color = dialog.theme[path]['gui_color']

            if self.button is None:
                self.button = dialog.theme[path]['image'].generate( color, dialog.batch, dialog.bg_group)

        if self.text and self.label is None:
            self.label = KyttenLabel(self.text,
                font_name=self.text_style.get('font', None) or dialog.theme[path]['font'],
                font_size=self.text_style.get('font_size', None) or dialog.theme[path]['font_size'],
                color=self.text_style.get('text_color', None) or dialog.theme[path]['text_color'],
                bold = self.text_style.get('bold', False),
                batch=dialog.batch, group=dialog.fg_group)

        if self.visible and self.bitmap is None:

            if self.image is not None:
                self.bitmap = DefaultTextureGraphicElement(texture=self.image, batch=dialog.batch, group=dialog.bg_group, color=self.colors)

            else:
                font = self.label.document.get_font()
                height = font.ascent - font.descent # descent is negative
                self.width, self.height = self.label.content_width+self.padding * 2, height+self.padding * 2# ADD padding
                return

            if self.fixed_size :
                if self.square or self.image.height == self.image.width:
                    self.bitmap.height=self.bitmap.width=float(self.fixed_size)

                else :# max(self.image.width,self.image.height) > self.fixed_size:

                    if   self.image.width > self.image.height:
                        self.bitmap.height=self.image.height*self.fixed_size/float(self.image.width)
                        self.bitmap.width=float(self.fixed_size)

                    elif self.image.width < self.image.height:
                        self.bitmap.width=self.image.width*self.fixed_size/float(self.image.height)
                        self.bitmap.height=float(self.fixed_size)
                    else:
                        self.bitmap.height=self.bitmap.width=float(self.fixed_size)

                #else:
                    #self.bitmap.width = self.image.width
                    #self.bitmap.height = self.image.height
            else:
                self.bitmap.width = self.image.width
                self.bitmap.height = self.image.height

            if self.square:
                self.width = self.height =\
                self.bitmap_width = self.bitmap_height = max(self.bitmap.width, self.bitmap.height) + self.padding * 2
            else:
                self.width = self.bitmap_width = self.bitmap.width + self.padding * 2
                self.height = self.bitmap_height = self.bitmap.height + self.padding * 2


        if not self.no_border:
            if self.label:
                font = self.label.document.get_font()
                height = font.ascent - font.descent # descent is negative

                self.width, self.height = self.button.get_needed_size(
                    max( self.label.content_width, self.bitmap_width ),
                    max( height,self.bitmap_height))
            else:
                self.width, self.height = self.button.get_needed_size(self.bitmap_width ,self.bitmap_height)

    def on_gain_highlight(self):
        self.image = self.hover_image
        Button.on_gain_highlight(self)

        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def on_lose_highlight(self):
        self.image = self.default_image
        Button.on_lose_highlight(self)

        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

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
    def __init__(self, image=None, style=None, copy=True, *args, **kwargs):
        ImageButton.__init__(self, image=image, style=style, *args, **kwargs)
        self.isDragging=False
        self.isCopying=copy

        self.__old__parent__=None
        self.set_handler('on_mouse_drag', self.on_mouse_drag)
        self.set_handler('on_mouse_release', self.on_mouse_release)

    def on_mouse_press(self, *args):
        self.saved_dialog.set_focus(self)
        ImageButton.on_mouse_press(self, *args)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        DRAGGED_ITEM=weakref.proxy(GetObjectfromName('draggable_items'))

        if not self.isDragging:
            self.__old__parent__=self.__parent__

            if self.isCopying is True:

                NEW = DraggableImageButton( image=self.default_image,
                                            style=self.image_arg,
                                            copy=True,
                                            padding=self.padding,
                                            on_click=self.on_click,
                                            on_gain_hover=self.on_gain_hover_func)

                if  isinstance(self.__old__parent__, InteractiveLayoutAssert):

                    if hasattr(self.__parent__, 'slaved') and self.__parent__.slaved: # for InteractivePaletteLayout
                        self.__old__parent_layout_info__ = self.__parent__.__parent__.remove(self, False)
                        self.__parent__.__parent__.add( NEW , self.__old__parent_layout_info__[1])

                    else:
                        self.__old__parent_layout_info__ = self.__parent__.remove(self, False)
                        self.__parent__.add( NEW , self.__old__parent_layout_info__[1])
                else:
                    self.__old__parent_layout_info__, index = self.__parent__.remove(self)

                    self.__parent__.add( *( self.__old__parent_layout_info__[:-1]+(NEW,) ) )

            elif self.isCopying is False:

                if hasattr(self.__parent__, 'slaved') and self.__parent__.slaved:


                    self.__old__parent_layout_info__ = self.__parent__.__parent__.remove(self)

                    if hasattr(self.__parent__.__parent__, 'on_drag_object') and self.__parent__.__parent__.on_drag_object is not None:
                        raise NotImplementedError('')
                        self.__parent__.__parent__.on_drag_object(self)

                else:
                    if  isinstance(self.__parent__, InteractiveLayoutAssert):
                        item,index = self.__old__parent_layout_info__ = self.__parent__.remove(self)
                    else:
                        (anchor, x, y, item), index = self.__old__parent_layout_info__ = self.__parent__.remove(self)

                    if hasattr(self.__parent__, 'on_drag_object') and self.__parent__.on_drag_object is not None:
                        self.__parent__.on_drag_object(self.__parent__, self, index)

            else:
                #item,index = self.__old__parent_layout_info__
                #self.__parent__.on_drag_object(self.__parent__, self, index)

                self.delete()

            DRAGGED_ITEM.set_content(self)
            DRAGGED_ITEM.offset=(self.x,self.y)
            DRAGGED_ITEM.needs_layout = True
            self.__old__parent__.saved_dialog.dont_pop_to_top=True
            self.__old__parent__.saved_dialog.set_focus(None)
            DRAGGED_ITEM.set_focus(self)
            DRAGGED_ITEM.pop_to_top()

            self.isDragging=True

            return pyglet.event.EVENT_HANDLED


        X,Y = DRAGGED_ITEM.offset
        DRAGGED_ITEM.set_focus(self)##################################
        DRAGGED_ITEM.offset=(X+dx,Y+dy)
        DRAGGED_ITEM.needs_layout = True

        return pyglet.event.EVENT_HANDLED

    def on_mouse_release(self, x, y, button, modifiers):
        if self.isDragging:
            DRAGGED_ITEM=GetObjectfromName('draggable_items')
            NEW_POSITION = DRAGGED_ITEM.check_position(int(self.x +self.width/2.),int(self.y+self.height/2.))

            Widget=None

            if NEW_POSITION is None :
                '''
                if not self.isCopying:
                    if isinstance(self.__old__parent__, InteractiveLayout):
                        self.__old__parent__.set( *self.__old__parent_layout_info__)

                    else:
                        self.__old__parent__.add( *self.__old__parent_layout_info__)
                    self.__old__parent__.saved_dialog.pop_to_top()
                    self.__old__parent__.saved_dialog.set_focus(self)

                else:
                '''
                self.teardown()

            else:
                New_Parent, position, widget = NEW_POSITION


                if hasattr(New_Parent, 'slaved') and New_Parent.slaved: # for InteractivePaletteLayout
                    if New_Parent.__parent__.on_drop_object is not None:
                        New_Parent.__parent__.on_drop_object(New_Parent, self, position)

                    Widget, position = New_Parent.__parent__.remove(widget._self(), False)
                    New_Parent.__parent__.add(self, position)

                else:
                    if New_Parent.on_drop_object is not None:
                        New_Parent.on_drop_object(New_Parent, self, position)

                    Widget, _ = New_Parent.remove(widget, False)
                    New_Parent.add(self, position)

                self.delete()
                New_Parent.saved_dialog.pop_to_top()
                self.isCopying=False

            DRAGGED_ITEM.set_focus(None)
            DRAGGED_ITEM.delete_content()
            DRAGGED_ITEM.EmulDragging=False
            DRAGGED_ITEM.needs_layout = True

            self.__old__parent__=None
            self.__old__parent_layout_info__=None

            self.isDragging=False

            if isinstance(Widget, DraggableImageButton):
                Widget.isCopying='Bypass'
                Widget.on_mouse_drag( x, y, 0, 0, button, modifiers)
                DRAGGED_ITEM.EmulDragging=True

            return pyglet.event.EVENT_HANDLED

    def on_gain_hover(self,*args):
        #print "on_gain_hover", self.__class__.__name__
        if self.isDragging: return True
        Control.on_gain_hover(self,*args)

        #self.hover_flag=True
        #if self.on_gain_hover_func: self.on_gain_hover_func(self)

    def on_lose_hover(self,*args):
        #print "on_lose_hover", self.__class__.__name__
        if self.isDragging: return True
        Control.on_lose_hover(self,*args)

        #self.hover_flag=False
        #if self.on_lose_hover_func: self.on_lose_hover_func(self)

DraggableImageButton.register_event_type('on_mouse_drag')
DraggableImageButton.register_event_type('on_mouse_release')
