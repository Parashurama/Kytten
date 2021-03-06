#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/dialog.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function, absolute_import, division
from .compat import *
import pyglet
import weakref
import time
import types
import pyglet.gl as gl
import pyglet.window.mouse as mouse


from .widgets import Widget, Spacer, Control, Label, DialogAssert, LayoutAssert, FreeLayoutAssert, DragNDropLayoutType
from .button import Button
from .frame import Wrapper, Frame, SectionHeader, GuiFrame, TransparentFrame, TitleFrame, Frame
from .layout import GetRelativePoint, ANCHOR_CENTER, HALIGN_LEFT, HALIGN_CENTER, VALIGN_TOP, VALIGN_CENTER

from .layout import ANCHOR_TOP_LEFT, ANCHOR_TOP, ANCHOR_TOP_RIGHT, \
                   ANCHOR_LEFT, ANCHOR_CENTER, ANCHOR_RIGHT, \
                   ANCHOR_BOTTOM_LEFT, ANCHOR_BOTTOM, ANCHOR_BOTTOM_RIGHT

from .layout import VerticalLayout, HorizontalLayout, GridLayout, FreeLayout
from .text_input import Input
from .base import DereferenceName, ReferenceDialog, DereferenceDialog, GetActiveDialogs, ActionOnAllDialogs, internals, GetObjectfromName, Virtual, InvalidWidgetNameError
from .tools import patch_instance_method
from .theme import Theme

event_dispatcher_events_override = set(['on_mouse_press','on_mouse_release','on_mouse_motion','on_mouse_drag','on_mouse_scroll',
                                    'on_key_press','on_key_release'])

ANCHOR_DEFAULT_FLAG_REF = {ANCHOR_TOP_LEFT:'NW',    ANCHOR_TOP:None,    ANCHOR_TOP_RIGHT:'NE',
                           ANCHOR_LEFT:None,        ANCHOR_CENTER:None, ANCHOR_RIGHT:None,
                           ANCHOR_BOTTOM_LEFT:'SW', ANCHOR_BOTTOM:None, ANCHOR_BOTTOM_RIGHT:'SE' }

DIALOG_TRANSPARENT_FRAME = 1<<1
DIALOG_NO_CREATE_FRAME = 1<<2

def SetMinMaxDialogOffsets(anchor, screen, g_width, g_height, m_width, m_height):
    width, height = screen.width, screen.height
    valign, halign = anchor

    if   valign == VALIGN_TOP:
        min_y = -height+g_height
        max_y = 0
    elif valign == VALIGN_CENTER:
        min_y = -height//2+g_height//2
        max_y =  height//2-m_height//2
    else: # VALIGN_BOTTOM
        min_y = 0
        max_y = height-g_height

    if   halign == HALIGN_LEFT:
        min_x = 0
        max_x = width-g_width
    elif halign == HALIGN_CENTER:
        min_x = -width//2+g_width//2
        max_x =  width//2-m_width//2
    else: # HALIGN_RIGHT
        min_x = -width+g_width
        max_x = 0

    return (min_x, min_y, max_x, max_y)


def get_default_anchor_flag(anchor):
    return ANCHOR_DEFAULT_FLAG_REF[anchor]

def check_for_always_on_top_dialog(event_type, *args):
    x=args[0]; y=args[1]

    for member in internals.kytten_floating_dialogs:
        if member.visible is True and member.hit_test(x, y) and member.dispatch_event(event_type, *args):
            return pyglet.event.EVENT_HANDLED

def PatchWindowsEventHandler(window):

    @patch_instance_method(window, "dispatch_event")
    def dispatch_event(self, event_type, *args):
        """
        Override Event dispatcher for dialog: give priority to overhanging dialogs (always on top)
        """
        if event_type in event_dispatcher_events_override:
            if check_for_always_on_top_dialog(event_type, *args):
                return pyglet.event.EVENT_HANDLED

class DialogEventManager(Control):
    def __init__(self, name=None):
        '''
        Creates a new event manager for a dialog.

        @param content The Widget which we wrap
        '''
        Control.__init__(self, name=name, noId=True)
        self.controls = weakref.WeakSet()
        self.control_areas = {}
        self.control_map = {}
        self.hover = None
        self.focus = None
        self.wheel_hint = None
        self.wheel_target = None
        self.last_clicked_time =0.
        self.mouse_in = False
        self.drag_n_drop_layouts = []

    def get_value(self, name):
        widget = self.get_widget(name)
        if widget is not None:
            return widget.get_value()

    def get_values(self):
        retval = {}
        for widget in self.controls:
            if widget.is_input() and widget.name is not None:
                retval[widget.name] = widget.get_value()
        return retval

    def get_widget(self, name):
        return self.control_map.get(name)

    def hit_control(self, x, y, control):
        left, right, top, bottom = self.control_areas[str(control)]
        if x >= left and x < right and y >= bottom and y < top:
            return control.hit_test(x, y)
        else:
            return False

    def on_update(self, dt):
        '''
        We update our layout only when it's time to construct another frame.
        Since we may receive several resize events within this time, this
        ensures we don't resize too often.

        @param dialog The Dialog containing the controls
        @param dt Time passed since last update event (in seconds)
        '''

        for control in self.controls:
            control.dispatch_event('on_update', dt)

    def set_focus(self, focus):
        '''
        Sets a new focus, dispatching lose and gain focus events appropriately

        @param focus The new focus, or None if no focus
        '''

        if self.visible is False or self.focus == focus:
            return

        if self.focus is not None:
            self.focus.dispatch_event('on_lose_focus')

        self.focus = focus

        if focus is not None:
            self.focus.dispatch_event('on_gain_focus')

        return self.EventHandled()

    def set_hover(self, hover):
        '''
        Sets a new highlight, dispatching lose and gain highlight events
        appropriately

        @param hover The new highlight, or None if no highlight
        '''
        if self.visible is False or self.hover == hover:
            return

        if self.hover is not None:
            self.hover.dispatch_event('on_lose_highlight')
            if self.hover.hover_flag : self.hover.dispatch_event('on_lose_hover')

        pyglet.clock.unschedule(self.check_hover)

        self.hover = hover
        if hover is not None:
            hover.dispatch_event('on_gain_highlight')
            pyglet.clock.schedule_once(self.check_hover, self.hover_delay, hover)

        return self.EventHandled()

    def check_hover(self, dt, hover):
        if self.hover is hover and hover.visible and not hover.hover_disabled:
            hover.dispatch_event('on_gain_hover')

    def set_wheel_hint(self, control):
        self.wheel_hint = control

    def set_wheel_target(self, control):
        self.wheel_target = control

    def release_wheel_target(self, widget=None):
        if widget is None:
            self.wheel_target = None
        elif self.wheel_target is widget:
            self.wheel_target = None

    def teardown(self):
        Control.teardown(self)
        self.controls = weakref.WeakSet()
        self.control_areas = {}
        self.control_map = {}
        self.focus = None
        self.hover = None
        self.wheel_hint = None
        self.wheel_target = None

    def update_controls(self):
        '''Update our list of controls which may respond to user input.'''
        controls = self._get_controls()
        if not controls: return
        self.controls = weakref.WeakSet()
        self.control_areas = {}
        self.control_map = {}
        for control, left, right, top, bottom in controls:
            self.controls.add(control)
            self.control_areas[str(control)] = (left, right, top, bottom)
            if control.name is not None:
                self.control_map[control.name] = control

        if self.hover is not None and self.hover not in self.controls:
            self.set_hover(None)
        if self.focus is not None and self.focus not in self.controls:
            self.set_focus(None)

    def EventHandled(self):
        self.to_refresh=True
        return pyglet.event.EVENT_HANDLED

internals.kytten_base_dialog_id = 0
internals.kytten_floating_dialog_id= 1<<32
internals.kytten_floating_dialogs=[]

def GetNextDialogOrderId(dialog):
    if dialog.always_on_top:
        internals.kytten_floating_dialog_id+=1
        return internals.kytten_floating_dialog_id
    else:
        internals.kytten_base_dialog_id+=1
        return internals.kytten_base_dialog_id

class DialogGroup(pyglet.graphics.OrderedGroup):
    '''
    Ensure that all Widgets within a Dialog can be drawn with
    blending enabled, and that our Dialog will be drawn in a particular
    order relative to other Dialogs.
    '''
    def __init__(self, parent=None, dialog=None, always_on_top=False):
        '''
        Creates a new DialogGroup.  By default we'll be on top.

        @param parent Parent group
        '''
        pyglet.graphics.OrderedGroup.__init__( self, GetNextDialogOrderId(dialog), parent )
        self.real_order = self.order
        self.dialog = weakref.proxy(dialog)

        if always_on_top and dialog:
            internals.kytten_floating_dialogs.insert(0, dialog)

    def __lt__(self, other):
        '''
        When compared with other DialogGroups, we'll return our real order
        compared against theirs; otherwise use the OrderedGroup comparison.
        '''
        if isinstance(other, DialogGroup):
            return self.real_order< other.real_order
        else:
            return pyglet.graphics.OrderedGroup.__lt__(other)

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
            self.real_order == other.real_order and
            self.parent == other.parent)

    def __hash__(self):
        return hash((self.order, self.parent))

    def is_on_top(self):
        '''
        Are we the top dialog group?
        '''

        if self.dialog.always_on_top:
            return self.real_order == internals.kytten_floating_dialog_id
        else:
            return self.real_order == internals.kytten_base_dialog_id

    def pop_to_top(self):
        '''
        Put us on top of other dialog groups.
        '''
        if not self.dialog.always_on_top:
             self.real_order = GetNextDialogOrderId(self.dialog)
        else:
            internals.kytten_floating_dialogs.remove(self.dialog._self())
            internals.kytten_floating_dialogs.insert(0, self.dialog._self())
            self.real_order = GetNextDialogOrderId(self.dialog)


    def set_state(self):
        '''
        Ensure that blending is set.
        '''
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_CURRENT_BIT)

    def unset_state(self):
        '''
        Restore previous blending state.
        '''
        gl.glPopAttrib()


class Dialog(Wrapper, DialogEventManager, DialogAssert):
    '''
    Defines a new GUI.  By default it can contain only one element, but that
    element can be a Layout of some kind which can contain multiple elements.
    Pass a Theme in to set the graphic appearance of the Dialog.

    The Dialog is always repositioned in relationship to the window, and
    handles resize events accordingly.
    '''

    def __init__(self, content=[], title=None, graphic=None, graphic_flag="repeat", theme=None, fixed_size=None, offset_modifier=None, flags=0, gui_style=None, *args, **kwargs):

        self.offset_modifier=offset_modifier # (ex: (-1/2.,0) offset x pos by half width towards left )
        self.basic_offset=kwargs.get('offset', (0,0))
        anchor = kwargs.get('anchor', ANCHOR_CENTER)
        theme = gui_style if gui_style is not None else theme
        try:
            attributes = theme.attributes
            theme = theme.get_theme()
        except AttributeError:
            attributes = {}

        if   graphic is not None:
            if not content:
                if fixed_size:  width,height = fixed_size
                else:           width,height = graphic.width, graphic.height,
                content=GuiFrame( content= Widget(width=width, height=height),
                                  texture=graphic, anchor=anchor, flag='default')
            else:
                content=GuiFrame( content= HorizontalLayout([content]),
                                  texture=graphic, anchor=anchor, flag=graphic_flag)
        elif flags & DIALOG_TRANSPARENT_FRAME:
            content=TransparentFrame(content)
        elif not flags & DIALOG_NO_CREATE_FRAME:
            if title is not None:
                content=TitleFrame(title, content)
            else:
                content=Frame(content)
        #else frame already created by user


        Dialog.__init2__(self, content, theme=theme, **dict(attributes, **kwargs) )

    def __init2__(self, content=None,
                       window=None,
                       batch=None,
                       group=None,
                       anchor=ANCHOR_TOP_LEFT,
                       offset=(0, 0),
                       name=None,
                       parent=None,
                       theme=None,
                       movable=True,
                       on_enter=None,
                       on_space=None,
                       on_escape=None,
                       on_resize=None,
                       on_mouse_enter=None,
                       on_mouse_leave=None,
                       always_on_top=False,
                       hover_delay=0.3,
                       attached_to=None,
                       anchor_flag=None,
                       display_group=None):
        '''
        Creates a new dialog.

        @param content The Widget which we wrap
        @param window The window to which we belong; used to set the
                      mouse cursor when appropriate.  If set, we will
                      add ourself to the window as a handler.
        @param batch Batch in which we are to place our graphic elements;
                     may be None if we are to create our own Batch
        @param group Group in which we are to place our graphic elements;
                     may be None
        @param anchor Anchor point of the window, relative to which we
                      are positioned.  If ANCHOR_TOP_LEFT is specified,
                      our top left corner will be aligned to the window's
                      top left corner; if ANCHOR_CENTER is specified,
                      our center will be aligned to the window's center,
                      and so forth.
        @param offset Offset from the anchor point.  A positive X is always
                      to the right, a positive Y to the upward direction.
        @param theme The Theme which we are to use to generate our graphical
                     appearance.
        @param movable True if the dialog is able to be moved
        @param on_enter Callback for when user presses enter on the last
                        input within this dialog, i.e. form submit
        @param on_escape Callback for when user presses escape
        '''
        assert isinstance(theme, dict), "Theme instance must be dict subclass"
        assert window is not None, "Dialog 'window' argument is not set."

        DialogEventManager.__init__(self)
        Wrapper.__init__(self, content=content, name=name, group=display_group)

        self.parent_group=group
        self.window = window
        self.anchor = anchor
        self.real_anchor = anchor

        self.hover_delay = hover_delay
        self.offset = offset
        self.theme = theme
        self.is_movable = movable
        self.on_enter = self._wrap_method(on_enter)
        self.on_space = self._wrap_method(on_space)
        self.on_escape = self._wrap_method(on_escape)
        self.on_resize_func = self._wrap_method(on_resize)

        self.on_mouse_enter_func = self._wrap_method(on_mouse_enter)
        self.on_mouse_leave_func = self._wrap_method(on_mouse_leave)

        if batch is None:
            self.batch = pyglet.graphics.Batch()
            self.own_batch = True
        else:
            self.batch = batch
            self.own_batch = False

        if batch is not None and hasattr(batch, 'AddDialog'):
            batch.AddDialog(self)

        self.to_refresh=True
        self.always_on_top = always_on_top
        self.dont_pop_to_top=False
        self.child_dialogs = weakref.WeakSet()
                                                                                            #string: bytes or unicode
        try: self.parent_dialog = GetObjectfromName(attached_to) if hasattr(attached_to, 'startswith') else None
        except InvalidWidgetNameError:
            raise InvalidWidgetNameError("Invalid 'attached_to' parameter : {0} in Dialog instance {1} named '{2}'".format(attached_to, self, self.name) )

        if self.parent_dialog is not None: self.parent_dialog.child_dialogs.add(self)

        if anchor_flag is not None:
            assert anchor_flag in ('NW', 'NE', 'SW', 'SE')
            self.anchor_flag = anchor_flag
        else:
            self.anchor_flag = get_default_anchor_flag(anchor)

        ReferenceDialog(self)

        self.root_group = DialogGroup(parent=group, dialog=self, always_on_top=always_on_top)
        self.panel_group = pyglet.graphics.OrderedGroup(0, self.root_group)
        self.bg_group = pyglet.graphics.OrderedGroup(1, self.root_group)
        self.fg_group = pyglet.graphics.OrderedGroup(2, self.root_group)
        self.highlight_group = pyglet.graphics.OrderedGroup(3, self.root_group)
        self.needs_layout = True
        self.is_dragging = False

        if window is None:
            self.screen = Widget()
        else:
            width, height = window.get_size()
            self.screen = Widget(width=width, height=height)
            window.push_handlers(self)
            """
    def get_relative_size(self):
        _OFF_WIDTH = 0 ; _OFF_HEIGHT = 0
        OFF_WIDTH = 0 ; OFF_HEIGHT = 0
        _WIDTH = self.width; _HEIGHT = self.height
        WIDTH = self.width; HEIGHT = self.height

        for child_dialog in self.child_dialogs:

            AN_Y, AN_X = ANCHOR = child_dialog.anchor
            AN_0, AN_1 = child_dialog.anchor_flag if child_dialog.anchor_flag is not None else (None, None)

            if AN_Y == VALIGN_TOP:
                if   AN_0 in  ('S', None): HEIGHT=max(HEIGHT, _HEIGHT+child_dialog.height)
                if   AN_1 != 'S':"""

    def get_relative_size(self):
        _OFF_WIDTH = 0 ; _OFF_HEIGHT = 0
        OFF_WIDTH = 0 ; OFF_HEIGHT = 0
        _WIDTH = self.width; _HEIGHT = self.height
        WIDTH = self.width; HEIGHT = self.height

        for child_dialog in self.child_dialogs:
            ANCHOR = child_dialog.anchor

            if ANCHOR_TOP_LEFT == ANCHOR:
                if   child_dialog.anchor_flag == 'NE':
                    HEIGHT=max(HEIGHT, _HEIGHT+child_dialog.height)
                    WIDTH=max(WIDTH, child_dialog.width)

                elif child_dialog.anchor_flag == 'NW':
                    OFF_WIDTH=max(OFF_WIDTH, child_dialog.width)
                    HEIGHT=max(HEIGHT, _HEIGHT+child_dialog.height)

                elif child_dialog.anchor_flag == 'SW':
                    OFF_WIDTH=max(OFF_WIDTH, child_dialog.width)
                    OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height-_HEIGHT)
                    #HEIGHT=max(HEIGHT, child_dialog.height)

            elif ANCHOR_LEFT == ANCHOR:
                OFF_WIDTH=max(OFF_WIDTH, child_dialog.width)
                OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height//2-_HEIGHT//2)
                HEIGHT=max(HEIGHT, _HEIGHT//2+ child_dialog.height//2)#max(HEIGHT, child_dialog.height//2) #

            elif ANCHOR_BOTTOM_LEFT == ANCHOR:
                if   child_dialog.anchor_flag == 'SE':
                    OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height)
                    WIDTH=max(WIDTH, child_dialog.width)

                elif child_dialog.anchor_flag == 'SW':
                    OFF_WIDTH=max(OFF_WIDTH, child_dialog.width)
                    OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height)

                elif child_dialog.anchor_flag == 'NW':
                    OFF_WIDTH=max(OFF_WIDTH, child_dialog.width)
                    HEIGHT=max(HEIGHT, child_dialog.height)

            elif ANCHOR_BOTTOM == ANCHOR:
                OFF_WIDTH=max(OFF_WIDTH, child_dialog.width//2-_WIDTH//2)
                OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height)
                WIDTH=max(WIDTH, _WIDTH//2+child_dialog.width//2)

            elif ANCHOR_BOTTOM_RIGHT == ANCHOR:
                if   child_dialog.anchor_flag == 'SW':
                    OFF_WIDTH=max(OFF_WIDTH, child_dialog.width-_WIDTH)
                    OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height)
                elif child_dialog.anchor_flag == 'SE':
                    OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height)
                    WIDTH=max(WIDTH, _WIDTH+child_dialog.width)
                elif child_dialog.anchor_flag == 'NE':
                    HEIGHT=max(HEIGHT, child_dialog.height)
                    WIDTH=max(WIDTH, _WIDTH+child_dialog.width)

            elif ANCHOR_RIGHT == ANCHOR:
                OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height//2-_HEIGHT//2)
                WIDTH=max(WIDTH, _WIDTH+child_dialog.width)
                HEIGHT=max(HEIGHT, child_dialog.height//2)

            elif ANCHOR_TOP_RIGHT == ANCHOR:
                if   child_dialog.anchor_flag == 'NW':
                    OFF_WIDTH=max(OFF_WIDTH, child_dialog.width-_WIDTH)
                    HEIGHT=max(HEIGHT, _HEIGHT+child_dialog.height)
                elif child_dialog.anchor_flag == 'NE':
                    WIDTH=max(WIDTH, _WIDTH+child_dialog.width)
                    HEIGHT=max(HEIGHT, _HEIGHT+child_dialog.height)
                elif child_dialog.anchor_flag == 'SE':
                    WIDTH=max(WIDTH, _WIDTH+child_dialog.width)
                    OFF_HEIGHT=max(OFF_HEIGHT, child_dialog.height-_HEIGHT)

            elif ANCHOR_TOP == ANCHOR:
                OFF_WIDTH=max(OFF_WIDTH, child_dialog.width//2-_WIDTH//2)
                WIDTH=max(WIDTH, _WIDTH//2+child_dialog.width//2)
                HEIGHT=max(HEIGHT, _HEIGHT+child_dialog.height)

            else:
                raise NotImplementedError('')

        return (WIDTH, HEIGHT),(OFF_WIDTH,OFF_HEIGHT)

    def translate_offset(self, OFFSET, PARENT, DIALOG, SCREEN, ANCHOR):
        (OFFSET_X,OFFSET_Y) = OFFSET

        if   ANCHOR == ANCHOR_TOP_LEFT:
            if   DIALOG.anchor_flag == 'NE':
                return ( OFFSET_X, OFFSET_Y-SCREEN.height+DIALOG.height+PARENT.height)
            elif DIALOG.anchor_flag == 'NW':
                return ( OFFSET_X-DIALOG.width, OFFSET_Y-SCREEN.height+DIALOG.height+PARENT.height)
            elif DIALOG.anchor_flag == 'SW':
                return ( OFFSET_X-DIALOG.width, OFFSET_Y-SCREEN.height+PARENT.height)

        elif ANCHOR == ANCHOR_LEFT:
            return (OFFSET_X-DIALOG.width, OFFSET_Y-SCREEN.height//2+PARENT.height//2)

        elif ANCHOR == ANCHOR_BOTTOM_LEFT:
            if   DIALOG.anchor_flag == 'SE':
                return (OFFSET_X, OFFSET_Y-DIALOG.height)
            elif DIALOG.anchor_flag == 'SW':
                return ( OFFSET_X-DIALOG.width, OFFSET_Y-DIALOG.height)
            elif DIALOG.anchor_flag == 'NW':
                return ( OFFSET_X-DIALOG.width, OFFSET_Y )

        elif ANCHOR == ANCHOR_BOTTOM:
            return (OFFSET_X-SCREEN.width//2+PARENT.width//2,OFFSET_Y-DIALOG.height)

        elif ANCHOR == ANCHOR_BOTTOM_RIGHT:
            if   DIALOG.anchor_flag == 'SW':
                return (OFFSET_X+PARENT.width-SCREEN.width , OFFSET_Y-DIALOG.height)
            elif DIALOG.anchor_flag == 'SE':
                return ( (OFFSET_X)-(SCREEN.width-DIALOG.width)+PARENT.width, OFFSET_Y-DIALOG.height)
            elif DIALOG.anchor_flag == 'NE':
                return ( (OFFSET_X)-(SCREEN.width-DIALOG.width)+PARENT.width,OFFSET_Y )

        elif ANCHOR == ANCHOR_RIGHT:
            return ( (OFFSET_X)-(SCREEN.width-DIALOG.width)+PARENT.width, OFFSET_Y-SCREEN.height//2+PARENT.height//2)

        elif   ANCHOR == ANCHOR_TOP_RIGHT:
            if   DIALOG.anchor_flag == 'NW':
                return (OFFSET_X+PARENT.width-SCREEN.width , OFFSET_Y-SCREEN.height+DIALOG.height+PARENT.height)
            elif DIALOG.anchor_flag == 'NE':
                return ( (OFFSET_X)-(SCREEN.width-DIALOG.width)+PARENT.width, OFFSET_Y-SCREEN.height+DIALOG.height+PARENT.height)
            elif DIALOG.anchor_flag == 'SE':
                return ( (OFFSET_X)-(SCREEN.width-DIALOG.width)+PARENT.width, OFFSET_Y-SCREEN.height+PARENT.height)

        elif ANCHOR == ANCHOR_TOP:
            return (OFFSET_X-SCREEN.width//2+PARENT.width//2, OFFSET_Y-SCREEN.height+DIALOG.height+PARENT.height)

        else:
            raise NotImplementedError('')

    def set_children_offsets(self):
        for child_dialog in self.child_dialogs:
            if not child_dialog.visible: continue
            child_dialog.offset = child_dialog.basic_offset = self.translate_offset((self.x, self.y), self, child_dialog, self.screen, child_dialog.anchor)
            child_dialog.needs_layout = True

    def do_layout(self):
        '''
        We lay out the Dialog by first determining the size of all its
        child Widgets, then laying ourself out relative to the parent window.
        '''
        if not self.screen: self.needs_layout = False ; return

        # Determine size of all components
        self.size(self, 1.0) #scale = 1.0
        EFFECTIVE_SIZE = (self.width,self.height)

        EFFECTIVE_OFFSET=(0,0)
        if self.child_dialogs:
            for child_dialog in self.child_dialogs:
                if not child_dialog.visible: continue
                child_dialog.size(child_dialog, 1.0)#scale = 1.0

            EFFECTIVE_SIZE, EFFECTIVE_OFFSET = self.get_relative_size()

        self.child_group_size = (EFFECTIVE_SIZE[0]+EFFECTIVE_OFFSET[0], EFFECTIVE_SIZE[1]+EFFECTIVE_OFFSET[1])

        # Calculate our position relative to our containing window,
        # making sure that we fit completely on the window.  If our offset
        # would send us off the screen, constrain it.
        if self.child_dialogs:
            g_width, g_height = self.child_group_size
            t_height=EFFECTIVE_SIZE[1] if (0 and self.anchor[1] == VALIGN_CENTER) else g_height
            t_width =EFFECTIVE_SIZE[0] if (0 and self.anchor[0] == HALIGN_CENTER) else g_width
            child_group = Virtual(width=t_width, height=t_height)
            x, y = GetRelativePoint(self.screen, self.anchor, child_group, None, (0, 0))
        else:
            x, y = GetRelativePoint(self.screen, self.anchor, self, None, (0, 0))

        offset_x, offset_y = self.offset

        if self.child_dialogs:
            min_offset_x, min_offset_y, max_offset_x, max_offset_y = SetMinMaxDialogOffsets(self.anchor, self.screen, g_width, g_height, t_width, t_height)

            offset_x = max(min(offset_x, max_offset_x), min_offset_x) + EFFECTIVE_OFFSET[0]
            offset_y = max(min(offset_y, max_offset_y), min_offset_y) + EFFECTIVE_OFFSET[1]
        else:
            min_offset_x, min_offset_y, max_offset_x, max_offset_y = SetMinMaxDialogOffsets(self.anchor, self.screen, self.width, self.height, self.width, self.height)
            offset_x = max(min(offset_x, max_offset_x), min_offset_x)
            offset_y = max(min(offset_y, max_offset_y), min_offset_y)

        self.offset = (offset_x, offset_y)
        x += offset_x
        y += offset_y

        # delete drag_n_drop_layouts references
        del self.drag_n_drop_layouts[:]

        # Perform the actual layout now!
        self.layout(x, y)
        self.update_controls()

        if self.child_dialogs:
            self.set_children_offsets()

        self.needs_layout = False

    def set_graphic(self, graphic, fixed_size=False):

        if graphic is not None:

            if isinstance(self.content, GuiFrame):
                if isinstance(self.content.content, LayoutAssert): # has real content
                    self.content.delete()
                    self.content.set_texture(graphic, 'repeat')

                else: # No real content , ghost widget
                    if fixed_size:  width,height = fixed_size
                    else:           width,height = graphic.width, graphic.height,

                    self.content.delete()
                    self.content.set_texture(graphic, 'default')
                    self.content.set_content(Widget(width=width, height=height))

            elif isinstance(self.content, TransparentFrame):
                content = self.content.content
                self.set_content(GuiFrame( content= HorizontalLayout([content]),
                                           texture=graphic, anchor=self.anchor, flag='repeat') )
            else:
                raise NotImplementedError("'set_graphic' method of kytten.Dialog is not yet implmeented for Frame & TitleFrame")
        else:
            content = self.content.content
            self.set_content(TransparentFrame(content))

        self.set_needs_layout()

    def draw(self):
        assert self.own_batch
        self.batch.draw()

    def header_bar_hit_test(self, x, y):
        if self.content._header_bar is None:
            return True
        ix0,iy0,ix1,iy1=self.content._header_bar

        if ix0<0: ix0=self.width+ix0
        if iy0<0: iy0=self.height+iy0

        if   ix1 is None: ix1=self.width
        elif ix1<0:       ix1=self.width+ix1

        if   iy1 is None: iy1=self.height
        elif iy1<0:       iy1=self.height+iy1

        dx = x-self.x ; dy = y-self.y

        return ( ix0 <= dx < ix1) and ( iy0 <= dy < iy1)

    def enable_exclusive_mode(self):
        mouse_press_func = self.on_mouse_press

        @patch_instance_method(self, "on_mouse_press")
        def mouse_press_wrapper(self, *args):
            if self.visible is True:
                mouse_press_func(*args)
                return True

        @patch_instance_method(self, "hit_test")
        def hit_test_wrapper(self, x, y):
            if self.visible is True:
                return True

    def disable_exclusive_mode(self):
        self._methods_stack["on_mouse_press"].pop()
        self._methods_stack["hit_test"].pop()

    def ensure_visible(self, control):
        '''
        Ensure a control is visible.  For Dialog, this doesn't matter
        since we don't scroll.
        '''
        pass

    def get_root(self):
        return self

    def on_key_press(self, symbol, modifiers):
        '''
        We intercept TAB, ENTER, and ESCAPE events.  TAB  will
        move us between fields, holding shift will reverse the direction
        of our iteration.  ESCAPE may cause us to send an on_escape
        callback.

        Otherwise, we pass key presses to our child elements.

        @param symbol Key pressed
        @param modifiers Modifiers for key press
        '''

        if not self.visible: return

                                                    # MultilineInput
        if symbol == pyglet.window.key.TAB and not hasattr(self.focus, 'on_auto_complete'): #[pyglet.window.key.TAB, pyglet.window.key.ENTER]:
            focusable = [x for x in self.controls if x.is_focusable() and not x.is_disabled()]
            if not focusable:
                return
            dir = -1 if modifiers & pyglet.window.key.MOD_SHIFT else 1

            if self.focus is not None and self.focus in focusable:
                index = focusable.index(self.focus)
            else:
                index = 0 - dir

            new_focus = focusable[(index + dir) % len(focusable)]
            self.set_focus(new_focus)
            new_focus.ensure_visible()

            return pyglet.event.EVENT_HANDLED

        elif self.focus is not None and symbol != pyglet.window.key.ESCAPE:
            if self.focus.dispatch_event("on_key_press", symbol, modifiers):
                return self.EventHandled()

            if symbol == pyglet.window.key.ENTER:
                if self.focus.dispatch_event("on_text", '\n'):
                    return self.EventHandled()

        if symbol == pyglet.window.key.ENTER:
            if self.on_enter is not None and not ( modifiers & pyglet.window.key.MOD_ALT or modifiers & pyglet.window.key.MOD_SHIFT):
                self.on_enter()
                return self.EventHandled()

        elif symbol == pyglet.window.key.ESCAPE:
            if self.on_escape is not None:
                self.on_escape()
                return self.EventHandled()

        elif symbol == pyglet.window.key.SPACE:
            if self.on_space is not None:
                self.on_space()
                return self.EventHandled()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        '''
        Handles mouse dragging.  If we have a focus, pass it in.  Otherwise
        if we are movable, and we were being dragged, move the window.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param dx Delta X
        @param dy Delta Y
        @param buttons Buttons held while moving
        @param modifiers Modifiers to apply to buttons
        '''
        if self.visible is False:
            return pyglet.event.EVENT_UNHANDLED

        if self.focus is not None:
            self.focus.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)
            return self.EventHandled()

        if self.is_movable and self.is_dragging is True:
            if not buttons == 1: return
            if self.parent_dialog: return self.parent_dialog.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

            x, y = self.basic_offset
            self.basic_offset = (int(x + dx), int(y + dy))
            self.set_needs_layout()

            return self.EventHandled()

    def on_mouse_press(self, x, y, button, modifiers):
        '''
        If the focus is set, and the target lies within the focus, pass the
        message down.  Otherwise, check if we need to assign a new focus.
        If the mouse was pressed within our frame but no control was targeted,
        we may be setting up to drag the Dialog around.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button pressed
        @param modifiers Modifiers to apply to button
        '''
        if self.visible is False or not self.hit_test(x, y):
            if self.focus is not None:
                self.set_focus(None)
            return pyglet.event.EVENT_UNHANDLED

        cliked_time = time.time()
        is_double_click = True if cliked_time-self.last_clicked_time< 0.25 else False
        self.last_clicked_time = cliked_time

        if self.focus is not None and self.hit_control(x, y, self.focus):
            if is_double_click is True:
                if not self.focus.dispatch_event('on_mouse_double_click', x, y, button, modifiers):
                    self.focus.dispatch_event('on_mouse_press', x, y, button, modifiers)
            else:
                self.focus.dispatch_event('on_mouse_press', x, y, button, modifiers)
            # pyglet.event.EVENT_HANDLED

        else:
            self.set_focus(self.hover)
            if self.focus is not None:
                self.focus.dispatch_event('on_mouse_press', x, y, button, modifiers)
                # pyglet.event.EVENT_HANDLED

        if not self.root_group.is_on_top() and not self.dont_pop_to_top:
            self.pop_to_top()

        self.dont_pop_to_top=False

        #doesn't have focus
        if self.focus is None and self.header_bar_hit_test(x, y):
            self.is_dragging = True
            if self.parent_dialog is not None:
                self.parent_dialog.is_dragging = True
                return pyglet.event.EVENT_HANDLED

        return self.EventHandled()

    def on_mouse_release(self, x, y, button, modifiers):
        '''
        Button was released.  We pass this along to the focus, then we
        generate an on_mouse_motion to handle changing the highlighted
        Control if necessary.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button released
        @param modifiers Modifiers to apply to button
        '''

        self.is_dragging = False
        if self.parent_dialog is not None:
            self.parent_dialog.is_dragging = False

        if self.visible is False:
            return pyglet.event.EVENT_UNHANDLED

        if not check_for_always_on_top_dialog("on_mouse_motion", x, y, 0, 0):
            self.on_mouse_motion(x, y, 0, 0)

        if self.focus is not None and self.focus.dispatch_event('on_mouse_release', x, y, button, modifiers):
            return pyglet.event.EVENT_HANDLED

        return pyglet.event.EVENT_UNHANDLED

    def on_mouse_motion(self, x, y, dx, dy):
        '''
        Handles mouse motion.  We highlight controls that we are hovering
        over.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param dx Delta X
        @param dy Delta Y
        '''
        if self.visible is False or not self.hit_test(x, y):
            if self.mouse_in is True:
                self.dispatch_event('on_mouse_leave', x, y)
            return pyglet.event.EVENT_UNHANDLED

        if self.hit_test(x, y) and self.mouse_in is False:
            ActionOnAllDialogs(self, 'on_mouse_leave', x, y)
            self.dispatch_event('on_mouse_enter', x, y)

        if self.hover is not None and not self.hit_control(x, y, self.hover):
            self.hover.dispatch_event('on_mouse_motion', x, y, dx, dy)

        new_hover = None
        for control in self.controls:
            if self.hit_control(x, y, control):
                new_hover = control
                break

        ActionOnAllDialogs(self, 'set_hover', None)

        self.set_hover(new_hover)
        if self.hover is not None:
            self.hover.dispatch_event('on_mouse_motion', x, y, dx, dy)

        return pyglet.event.EVENT_HANDLED

    def on_key_release(self, symbol, modifiers):
        '''Pass key release events to the focus

        @param symbol Key released
        @param modifiers Modifiers for key released
        '''
        if self.visible is True and self.focus is not None and self.focus.dispatch_event("on_key_release", symbol, modifiers):
            return pyglet.event.EVENT_HANDLED

        return pyglet.event.EVENT_UNHANDLED

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        '''
        Mousewheel was scrolled.  See if we have a wheel target, or
        failing that, a wheel hint.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param scroll_x Number of clicks horizontally mouse was moved
        @param scroll_y Number of clicks vertically mouse was moved
        '''
        if self.visible is False or not self.hit_test(x,y):
            return pyglet.event.EVENT_UNHANDLED

        if self.wheel_target is not None and self.wheel_target in self.controls:
            self.wheel_target.dispatch_event('on_mouse_scroll', x, y, scroll_x, scroll_y)
            return self.EventHandled()

        elif self.wheel_hint is not None and self.wheel_hint in self.controls:
            self.wheel_hint.dispatch_event('on_mouse_scroll', x, y, scroll_x, scroll_y)
            return self.EventHandled()

    def on_text(self, text):
        if not self.visible: return
        if self.focus is not None and text != '\r' and self.focus.dispatch_event("on_text", text):
            return self.EventHandled()

    def on_text_motion(self, motion):
        if not self.visible: return
        if self.focus is not None and self.focus.dispatch_event("on_text_motion", motion):
            return self.EventHandled()

    def on_text_motion_select(self, motion):
        if not self.visible: return
        if self.focus is not None and self.focus.dispatch_event("on_text_motion_select",motion):
            return self.EventHandled()

    def on_mouse_enter(self, x, y):
        if self.hit_test(x, y) and self.on_mouse_enter_func is not None:
            self.mouse_in = True
            self.on_mouse_enter_func(x, y)

    def on_mouse_leave(self, x, y):
        if self.mouse_in is True and self.on_mouse_leave_func is not None:
            self.mouse_in = False
            self.on_mouse_leave_func(x, y)

    def on_resize(self, width, height):
        '''
        Update our knowledge of the window's width and height.

        @param width Width of the window
        @param height Height of the window
        '''
        if self.screen.width != width or self.screen.height != height:
            self.screen.width, self.screen.height = width, height
            self.needs_layout = True

        if self.on_resize_func is not None and self.visible:
            self.on_resize_func(width, height)


    def on_update(self, dt):
        '''
        We update our layout only when it's time to construct another frame.
        Since we may receive several resize events within this time, this
        ensures we don't resize too often.

        @param dt Time passed since last update event (in seconds)
        '''
        if self.needs_layout:
            self.do_layout()
        DialogEventManager.on_update(self, dt)

    def pop_to_top(self):
        '''
        Pop our dialog group to the top, and force our batch to re-sort
        the groups.  Also, puts our event handler on top of the window's
        event handler stack.
        '''
        self.root_group.pop_to_top()
        self.batch._draw_list_dirty = True  # forces resorting groups
        if self.window is not None:
            self.window.remove_handlers(self)
            self.window.push_handlers(self)

        self.EventHandled()

    def set_position(self, pos):
        if self.anchor == ANCHOR_BOTTOM_LEFT:
            self.set_offset(pos)
        else:
            raise NotImplementedError("Setting Position Only for Dialog with 'ANCHOR_BOTTOM_LEFT'")

    def get_offset(self):
        return self.basic_offset

    def set_offset(self, offset):
        self.basic_offset = (int(offset[0]), int(offset[1]))
        self.offset = (int(offset[0]), int(offset[1]))
        self.set_needs_layout()

    def size(self, dialog, scale):
        Wrapper.size(self, dialog, scale)

        if self.offset_modifier is not None:
            x, y = self.basic_offset
            self.offset=(int(x+self.offset_modifier[0]*self.width),
                         int(y+self.offset_modifier[1]*self.height))
        else:
            self.offset=self.basic_offset

    def Hide(self):
        Wrapper.Hide(self)

        if self.focus is not None:
            self.focus.dispatch_event('on_lose_focus')
            self.focus=None

    def set_needs_layout(self):
        '''
        True if we should redo the Dialog layout on our next update.
        '''
        self.needs_layout = True
        self.EventHandled()

    def teardown(self):
        DialogEventManager.teardown(self)
        if self.content is not None:
            self.content.teardown()
            self.content = None

        if self.window is not None:
            self.window.remove_handlers(self)
            self.window = None
        self.batch._draw_list_dirty = True  # forces resorting groups

        if self.always_on_top is True:
            internals.kytten_floating_dialogs.remove(self)

        if self.screen is not None:
            self.screen.teardown()
            self.screen=None

        self.EventHandled()
        DereferenceDialog(self)

class GuiTheme(object):
    def __init__(self, theme, override={}, override_theme=None, **kwargs):
        if isinstance(theme, GuiTheme):
            self.theme = Theme(theme.get_theme() if override_theme is None else override_theme, override=override)
            self.attributes = dict(theme.attributes, **kwargs)
        else:
            self.theme = Theme(theme, override=override)
            self.attributes = kwargs

    def get_theme(self):
        return self.theme

class ToolTip(Dialog):
    def __init__(self, parent_widget, text='EMPTY', name=None, secondary=None, text_style={}, **kwargs):

        self.parent_widget = weakref.proxy(parent_widget)
        parent_dialog=parent_widget.saved_dialog
        #self.parent_widget.disable() # caused bug : on_click not working after ToolTip is created

        if self.parent_widget.tooltip:
            self.parent_widget.tooltip.tearing_down_tooltip()

        if not text:                        content=None
        elif hasattr(text, 'startswith'):   content=Label(text, style=text_style)#string: bytes or unicode
        else:                               content=text

        Dialog.__init__(self,   content=content,
                                    window=parent_dialog.window,
                                    theme=parent_dialog.theme,
                                    batch=parent_dialog.batch,
                                    group=parent_dialog.parent_group,
                                    anchor=ANCHOR_BOTTOM_LEFT,
                                    #tooltip=True,
                                    offset=(0,0),
                                    always_on_top=True,
                                    movable=False,
                                    name=name,
                                    **kwargs)

        self.parent_widget.tooltip=self
        self.parent_widget.push_handlers('on_lose_hover','on_mouse_press', on_mouse_press=self.tearing_down_tooltip, on_lose_hover=self.tearing_down_tooltip)

        if secondary is not None:
            secondary_doc, secondary_name = secondary
                                        #string: bytes or unicode
            if hasattr(secondary_doc, 'startswith'): content=Label(secondary_doc)
            else:                                    content=secondary_doc

            if name is None:
                raise InvalidWidgetNameError("Tooltip with child Tooltip must have a name.(was None)")

            self.secondary = ToolTipProxy(content=content,
                                    window=parent_dialog.window,
                                    theme=parent_dialog.theme,
                                    batch=parent_dialog.batch,
                                    group=parent_dialog.parent_group,
                                    anchor=ANCHOR_TOP_RIGHT,
                                    offset=(0,0),
                                    attached_to=self.name,
                                    always_on_top=True,
                                    movable=False,
                                    name=secondary_name,
                                    anchor_flag='SE',
                                    graphic = kwargs.get('graphic', None),
                                    gui_style = kwargs.get('gui_style', None))
        else:
            self.secondary = None

    def tearing_down_tooltip(self,*args):
        if self.parent_widget.tooltip is not None:
            self.parent_widget.pop_handlers() #pop tooltip event handlers 'on_lose_hover' and 'on_mouse_press' syntax : self.parent_widget.remove_handler('on_lose_hover', self.tearing_down_tooltip)
            self.parent_widget.tooltip=None
            self.tearing_down_tooltip=None
            #self.parent_widget=None
            self.teardown()

        if self.secondary is not None:
            self.secondary.teardown()
            self.secondary = None

    def do_layout(self):
        '''
        We lay out the Dialog by first determining the size of all its
        child Widgets, then laying ourself out relative to the parent window.
        '''
        if not self.screen: self.needs_layout = False ; return
        # Determine size of all components
        self.size(self, 1.0)#scale = 1.0
        EFFECTIVE_SIZE = (self.width,self.height)

        EFFECTIVE_OFFSET=(0,0)
        if self.child_dialogs:
            for child_dialog in self.child_dialogs:
                if not child_dialog.visible: continue
                child_dialog.size(child_dialog, 1.0)

            EFFECTIVE_SIZE, EFFECTIVE_OFFSET = self.get_relative_size()

        self.child_group_size = (EFFECTIVE_SIZE[0]+EFFECTIVE_OFFSET[0], EFFECTIVE_SIZE[1]+EFFECTIVE_OFFSET[1])

        if self.real_anchor == ANCHOR_CENTER and self.child_dialogs:
            center_x = self.screen.width//2
            center_y = self.screen.height//2
            g_width, g_height = self.child_group_size
            self.set_offset((center_x-g_width//2, center_y-g_height//2))
            self.anchor = ANCHOR_BOTTOM_LEFT

        # Calculate our position relative to our containing window,
        # making sure that we fit completely on the window.  If our offset
        # would send us off the screen, constrain it.
        x = self.parent_widget.x + self.parent_widget.width//2-self.width//2
        y = self.parent_widget.y + self.parent_widget.height//2-self.height//2

        #x, y = GetRelativePoint(self.screen, self.anchor,
        #                        self, None, (0, 0))
        x+=EFFECTIVE_OFFSET[0]
        y+=EFFECTIVE_OFFSET[1]
        max_offset_x = self.screen.width - EFFECTIVE_SIZE[0] - x
        max_offset_y = self.screen.height - EFFECTIVE_SIZE[1] - y

        offset_x, offset_y = self.offset

        if self.child_dialogs:
            offset_x = max(min(offset_x, max_offset_x), 0)
            offset_y = max(min(offset_y, max_offset_y), 0)
        else:
            offset_x = max(min(offset_x, max_offset_x), -x)
            offset_y = max(min(offset_y, max_offset_y), -y)

        self.offset = (offset_x, offset_y)
        x += offset_x
        y += offset_y

        # Perform the actual layout now!
        self.layout(x, y)
        self.update_controls()

        if self.child_dialogs:
            self.set_children_offsets()

        self.needs_layout = False
        for child_dialog in self.child_dialogs:
            child_dialog.needs_layout=True
            child_dialog.on_update(0.0)

    def on_mouse_drag(self,*args):
        pass

    def on_mouse_press(self,x, y, *args):
        pass

    def on_mouse_release(self,*args):
        pass

    def on_mouse_motion(self,*args):
        pass

    def on_mouse_scroll(self,*args):
        pass

class ToolTipProxy(Dialog):

    def on_mouse_drag(self,*args):
        pass

    def on_mouse_press(self,*args):
        pass

    def on_mouse_release(self,*args):
        pass

    def on_mouse_motion(self,*args):
        pass

    def on_mouse_scroll(self,*args):
        pass

class DragNDrop(Dialog):
    _emul_dragging=False

    def __init__(self, *args, **kwargs):
        kwargs['always_on_top'] = True
        Dialog.__init__(self, *args, **kwargs)

    def layout_validate_drop_widget(self, item, pos):
        x, y=pos
        for _, dialog in sorted(((dialog.root_group.real_order,dialog) for dialog in GetActiveDialogs() if (dialog.visible is True and dialog.hit_test(x,y)) ), reverse=True):
            for layout in dialog.drag_n_drop_layouts:
                POSITION = layout.validate_drop_widget(item, pos)
                if POSITION is not None:
                    return POSITION
    def hit_test(self, x, y):
        return True

    def on_mouse_motion(self, x, y, dx, dy):

        if self._emul_dragging is True:
            self.focus.dispatch_event("on_mouse_drag", x,y,dx,dy, mouse.LEFT,16)
            return self.EventHandled()

    def set_hover(self,*args):
        self.hover=None
        return self.EventHandled()

    def on_mouse_press(self, x, y, button, modifiers):
        if self._emul_dragging is True:
            self.focus.dispatch_event("on_mouse_release", x,y, button,modifiers)
            return self.EventHandled()

    def on_mouse_scroll(self,*args):
        pass

class PopupMessage(Dialog):
    '''A simple fire-and-forget dialog.'''

    def __init__(self, text="", **kwargs):
        on_escape = kwargs.pop("on_escape", None)

        def on_ok(dialog=None):
            if on_escape is not None:
                on_escape(self)
            self.teardown()

        return Dialog.__init__(self, VerticalLayout([ Label(text), Button("Ok", on_click=on_ok)]),
                                on_enter=on_ok, on_escape=on_ok, **kwargs)

class PopupConfirm(Dialog):
    '''An ok/cancel-style dialog.  Escape defaults to cancel.'''

    def __init__(self, text="", ok="Ok", cancel="Cancel", **kwargs):
        on_cancel = kwargs.pop("on_cancel", None)
        on_ok = kwargs.pop("on_ok", None)

        def on_ok_click(dialog=None):
            if on_ok is not None:
                on_ok(self)
            self.teardown()

        def on_cancel_click(dialog=None):
            if on_cancel is not None:
                on_cancel(self)
            self.teardown()

        return Dialog.__init__(self, VerticalLayout([
                                        Label(text),
                                        HorizontalLayout([
                                            Button(ok, on_click=on_ok_click),
                                            None,
                                            Button(cancel, on_click=on_cancel_click)
                                        ], align=HALIGN_CENTER),
                                    ]), on_enter=on_ok_click, on_escape=on_cancel_click, **kwargs)


class PropertyDialog(Dialog):
    '''
    An ok/cancel-style dialog for editing properties. Options must be a
    dictionary of name/values. Escape defaults to cancel.

    @ has_remove allows for deleting options and returns
    @ _REMOVE_PRE+option id = True for get_values()
    '''
    _id_count = 0
    REMOVE_PRE = '_X!'
    TYPE_PRE = '_T!'
    ADD_NAME_PRE = '_N!'
    ADD_VALUE_PRE = '_V!'
    INPUT_W = 12
    def __init__(self, title="", properties={}, ok="Ok", cancel="Cancel",
                 on_ok=None, on_cancel=None, has_remove=False,
                 remove="x", has_add=False, add="+", on_add=None, **kwargs):

        def on_ok_click(dialog=None):
            if on_ok is not None:
                on_ok(self)
            self.teardown()

        def on_cancel_click(dialog=None):
            if on_cancel is not None:
                on_cancel(self)
            self.teardown()

        self.remove = remove
        self._has_remove = has_remove
        self._has_add = has_add
        property_table = self._make_properties(properties)
        grid = GridLayout(property_table, padding=8)

        def on_type_select(id, choice):
            item = Checkbox() if choice is 'bool' else Input(length=self.INPUT_W)
            for i, row in enumerate(grid.content):
                for cell in row:
                    if isinstance(cell, Dropdown):
                        if cell.id == id:
                            item_id = grid.get(1,i).id
                            item.id = item_id
                            grid.set(row=i, column=1, item=item)
                            break

        def on_add_click(dialog=None):
            if on_add is not None:
                on_add(self)
            else:
                pd = PropertyDialog
                pd._id_count += 1
                grid.add_row([
                    Input(id=pd.ADD_NAME_PRE+str(pd._id_count),
                        length=self.INPUT_W),
                    Input(id=pd.ADD_VALUE_PRE+str(pd._id_count),
                        length=self.INPUT_W),
                    Dropdown(['unicode', 'bool', 'int', 'float'],
                              id=pd.TYPE_PRE+str(pd._id_count),
                              on_select=on_type_select)
                ])

        if self._has_add:
            add_content = (ANCHOR_TOP_LEFT, 0, 0, Button(add, on_click=on_add_click))
            Dialog.__init__(self, content=\
                VerticalLayout([
                    SectionHeader(title, align=HALIGN_LEFT),
                    grid,
                    FreeLayout(content=[add_content]),
                    Spacer(height=30),
                    HorizontalLayout([
                        Button(ok, on_click=on_ok_click),
                        Button(cancel, on_click=on_cancel_click)])
                ]),
                on_enter=on_ok_click, on_escape=on_cancel_click, **kwargs)
        else:
            Dialog.__init__(self, content=\
                VerticalLayout([
                    SectionHeader(title, align=HALIGN_LEFT),
                    grid,
                    Spacer(height=30),
                    HorizontalLayout([
                        Button(ok, on_click=on_ok_click),
                        Button(cancel, on_click=on_cancel_click)])
                ]),
                on_enter=on_ok_click, on_escape=on_cancel_click, **kwargs)

    def _make_properties(self, properties):
        property_table = [[]]
        for name, value in properties:
            if isinstance(value, bool):
                property = Checkbox(is_checked=value, id=name)
            else:
                property = Input(name=name, text=unicode(value), length=self.INPUT_W)
            if self._has_remove:
                property_table.append([Label(name), property,
                    Checkbox(self.remove,
                        id=PropertyDialog.REMOVE_PRE+name)])
            else:
                property_table.append([Label(name), property])
        return property_table
