#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# examples/example_advanced2.py
# Copyrighted (C) 2014 by "Parashurama"
from __future__ import unicode_literals, print_function
import random
import pyglet
import string
import sys
import os

sys.path.extend(['.','..']) # allow import from parent folder (1 level up)
import kytten

from kytten import PageManager

def HackFunction(window):# Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
        window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)

def dummy(*args, **kwargs):
    pass

def dummy_contructor(*args):
    print("dummy_contructor")

# Callback on Widget Drop.
def SlotsDropObject(*args):
    pass

# Callback on Button Drag.
def SlotsDragObject(*args):
    pass

# This control if the Drop is effectued.
def ValidateSlotsDropObject(*args):
    return True # if not True drop is not effectued

# Callback on Button Hover.
def slot_hover(btn):
    pass

def build_slots_dialogs(*args):
    # Create 100 empty slots. None in InteractiveLayout means using default_slots image/texture.
    SLOTS = [ kytten.InteractiveLayout([None]*10, padding=3, default_slot=Images['slot'],
                                        name='slotline{}'.format(i),
                                        on_drop_object=SlotsDropObject,
                                        on_drag_object=SlotsDragObject,
                                        validate_drop_widget=ValidateSlotsDropObject ) for i in range(10) ]
    documentation = """\
    These dialogs demonstrate the capabilities of kytten dialogs. \
Both bottom and top-right dialogs are atttached to the top left dialog.
    Try to drag one dialog, the others will follow.
    This behaviour is set with the 'attached_to' parameter in Dialog constructor \
and controlled with the 'anchor' and 'anchor_flag' parameters.
    @param anchor are classic kytten anchors: ANCHOR_* except ANCHOR_CENTER for obvious reasons
    @param anchor_flag are direction ('SW', 'SE', 'NW', 'NE') or None for default value,  although some combination are invalid. See code source in 'dialog.py' line 574 or future documentation.

    Also each colored button is draggable. Try to move one into the smaller grid and back."""

    kytten.Dialog(
        kytten.Scrollable(
            kytten.VerticalLayout([
                kytten.InteractiveLayout([None]*3, padding=3, default_slot=Images['slot'],
                    name='slotlinex{}'.format(i),
                    on_drop_object=SlotsDropObject,
                    on_drag_object=SlotsDragObject,
                    validate_drop_widget=ValidateSlotsDropObject ) for i in range(3) ],
                align=kytten.HALIGN_LEFT, padding=3),
            width=256, height=256, is_fixed_size=True),
        name="diagram_dialog", theme=GUI_Style1, anchor=kytten.ANCHOR_CENTER,
        display_group='Slots')

    kytten.Dialog(  kytten.Document(documentation, width=377, height=256),
                    name="attributes_dialog", theme=GUI_Style1, anchor=kytten.ANCHOR_RIGHT,
                    display_group='Slots', attached_to='diagram_dialog')

    kytten.Dialog( kytten.Scrollable(
                        kytten.VerticalLayout(SLOTS, padding=3),
                        height=250, width=700 ),
                 gui_style=GUI_Style1, name='slot_dialog', offset=(0,0),
                 anchor=kytten.ANCHOR_BOTTOM_LEFT, movable=False, anchor_flag='SE', always_on_top=True,
                 attached_to='diagram_dialog', display_group='Slots' )
    randint = random.randint

    def rnd_color():
        return [128+randint(0,16)*8, 128+randint(0,16)*8, 128+randint(0,16)*8, 255]

    # Randomly create DraggableImageButton in Slots.
    for slot in [ randint(0,99) for i in range(35)]:
        layout = SLOTS[slot/10]
        layout.set(kytten.DraggableImageButton(Images['slot_button'], padding=0, on_gain_hover=slot_hover, on_double_click=dummy, color=rnd_color()), slot%10)


def on_click_show_slots(btn):
    PageManager.goto_page(1)

def on_click_exit(btn):
    raise SystemExit

if __name__ == '__main__':
    window = pyglet.window.Window(1440,800, caption='Example Advanced 2', vsync=True, resizable=True)   #, config=configy

    kytten.SetWindow(window)

    Images = {}
    Images['menubutton_default'] =kytten.LoadImage('images/menubutton_default.png')
    Images['menubutton_hover'] = kytten.LoadImage('images/menubutton_hover.png')
    Images['menubutton_clicked'] = kytten.LoadImage('images/menubutton_clicked.png')
    Images['slot'] = kytten.LoadImage('images/slot.png')
    Images['slot_button'] = kytten.LoadImage('images/slot_button.png')

    # Must reference existing folder or another already loaded theme.
    theme = kytten.Theme('theme', override={
        "text_color": [0,50,0,255],
        "font_size": 16
    })

    GUI_Style1=kytten.GuiTheme( window=window, batch=kytten.KyttenManager,
                                group=kytten.KyttenManager.foregroup, movable=True,
                                always_on_top=False, theme=theme)

    # A display group can be used as a shortcut to show/hide multiple widgets/dialogs in one call.
    # ex: Widget(foo=bar, group='display_group_name') for all widgets/layouts except dialogs:
    # ex: Dialog(foo=bar, display_group='display_group_name')
    # used like this: kytten.GetObjectfromName('display_group_name').Hide()
    # will hide all widgets with this group name.
    kytten.DisplayGroup(name='Slots')

    # Used to Style Image Button
    MenuButton = kytten.ButtonStyle( Images['menubutton_default'], Images['menubutton_hover'], Images['menubutton_clicked'], size=None,
                                     square=False, has_border=False, is_expandable=True, text_style={'text_padding':(10,10,0,0)})


    # Create a simple Dialog with a Title and the default graphic.
    dialog = kytten.Dialog(
                kytten.VerticalLayout([
                    kytten.ImageButton(style=MenuButton, text="Show Slots", on_click=on_click_show_slots),
                    kytten.ImageButton(style=MenuButton, text="Show Text Widgets", on_click=dummy),
                    kytten.ImageButton(style=MenuButton, text="Show Document", on_click=dummy),
                    kytten.ImageButton(style=MenuButton, text="Exit", on_click=on_click_exit),
                ], align=kytten.HALIGN_LEFT),
            title='Simple Menu 0', anchor=kytten.ANCHOR_CENTER, theme=GUI_Style1, movable=False, name='main_menu')



    PageManager.RegisterPage(0, to_show=['main_menu'],
                             constructor=dummy_contructor,
                             callback=None)

    PageManager.RegisterPage(1, to_show=['slot_dialog', 'diagram_dialog', 'attributes_dialog'],
                             constructor=build_slots_dialogs,
                             callback=None)




    PageManager.goto_page(0)
    # Allow pyglet to run as fast as it can
    HackFunction(window)

    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()

    pyglet.app.run()





