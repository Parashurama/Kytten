#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# examples/example_advanced1.py
# Copyrighted (C) 2014 by "Parashurama"
from __future__ import absolute_import, unicode_literals, division, print_function
import pyglet
import string
import sys
import os
import copy
import pyglet.gl as gl

sys.path.extend(['.','..']) # allow import from parent folder (1 level up)
import kytten
from kytten import PageManager

from _multiline_input_autocomplete import Default_auto_complete, Default_on_tabulation, select_auto_complete_option

def HackFunction(window):# Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
        window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)


def on_click_prev_page(btn):
    PageManager.prev_page()

def on_click_next_page(btn):
    PageManager.next_page()

def on_click_exit(btn):
    raise SystemExit

def dummy_contructor(*args):
    print("dummy_contructor")

def create_message(text='Nothing to see here!'):
    def on_hover_button_tooltip(btn):
        # Create a tooltip dialog.
        # it will be automatically be destroyed once the mouse leave the parent widget, in this case the ImageButton.
        main_page = kytten.ToolTip( parent_widget=btn, text=text, text_style={"color":[255,255,255,255]},
                        graphic=Images['popup_menu'],
                        name='tooltip')

    return on_hover_button_tooltip

def build_readme_dialog(*args):
    with open("../README", "rb") as f:
        README_TEXT = f.read()

    navigator = kytten.Dialog(
                    kytten.VerticalLayout([
                        kytten.Document(README_TEXT, width = 700, height=600)
                    ]), anchor=kytten.ANCHOR_CENTER, theme=GUI_Style1,
                    graphic=Images['popup_menu'], name='readme_dialog', movable=False)

def build_console_dialog(*args):

    navigator = kytten.Dialog(
                    kytten.VerticalLayout([
                        kytten.MultilineInput("This is very much like a primitive text editor\n It support TAB autocompletion, Copy/Cut/Paste from/to the clipboard.",
                                                width = 700, height=600, auto_complete=Default_auto_complete, on_tabulation=Default_on_tabulation,
                                                name='multiline_input_widget')
                    ]), anchor=kytten.ANCHOR_CENTER, theme=GUI_Style1,
                    graphic=Images['popup_menu'], name='console_dialog', movable=False)


    kytten.Dialog( kytten.Scrollable(
                        kytten.MenuList([''], on_select=select_auto_complete_option, align=kytten.HALIGN_LEFT, padding=10, name='Input_Autocomplete_menu' )
                    ,height=200),
                graphic=Images['popup_menu'], theme=GUI_Style1, name='Input_Autocomplete', offset=(0,0),  offset_modifier=(0,-1),
                anchor=kytten.ANCHOR_BOTTOM_LEFT, movable=False, always_on_top=True)


if __name__ == '__main__':
    window = pyglet.window.Window(800,800, caption='Example Advanced 1', vsync=True, resizable=True)   #, config=configy

    kytten.SetWindow(window)

    Images = {}
    Images['menubutton_default'] =kytten.LoadImage('images/menubutton_default.png')
    Images['menubutton_hover'] = kytten.LoadImage('images/menubutton_hover.png')
    Images['menubutton_clicked'] = kytten.LoadImage('images/menubutton_clicked.png')
    Images['radial_menu'] = kytten.LoadImage('images/radial_menu.png')
    Images['radial_button_default'] = kytten.LoadImage('images/radial_button_default.png')
    Images['radial_button_hover'] = kytten.LoadImage('images/radial_button_hover.png')
    Images['radial_button_clicked'] = kytten.LoadImage('images/radial_button_clicked.png')

    Images['popup_menu'] = kytten.LoadImage('images/popup_menu.png')

    # Must reference existing folder or another already loaded theme.
    theme = kytten.Theme('theme', override={
        "gui_color": [85,157,255,255],
        "text_color": [0,20,0,255],
        "font_size": 16
    })

    GUI_Style1=kytten.GuiTheme( window=window, batch=kytten.KyttenManager,
                                group=kytten.KyttenManager.foregroup, movable=True,
                                always_on_top=False, theme=theme)

    # Used to Style Image Button
    RadialButton = kytten.ButtonStyle( Images['radial_button_default'], Images['radial_button_hover'], Images['radial_button_clicked'], size=None,
                                     square=False, has_border=False, is_expandable=False, text_style={'text_padding':(10,10,0,0)})

    navigator = kytten.Dialog(
                    kytten.HorizontalLayout([
                        kytten.Button("Prev", on_click=on_click_prev_page),
                        kytten.Button("Next", on_click=on_click_next_page)
                    ]), anchor=kytten.ANCHOR_BOTTOM, theme=GUI_Style1,
                    name='navigator_dialog', movable=False, always_on_top=True,
                    flags=kytten.DIALOG_TRANSPARENT_FRAME) # This flag is pretty explicit. it also disable dragging support.

    RADIAL_BUTTONS = [( kytten.ANCHOR_CENTER, 0, 100, kytten.ImageButton( style=RadialButton, color=(255,0,0,255),
                                                                          on_gain_hover=create_message(), on_click=lambda x: PageManager.goto_page(1)) ),
                      ( kytten.ANCHOR_CENTER, 100, 0, kytten.ImageButton( style=RadialButton, color=(0,255,0,255),
                                                                          on_gain_hover=create_message("README"), on_click=lambda x: PageManager.goto_page(2)) ),
                      ( kytten.ANCHOR_CENTER, 0, -100, kytten.ImageButton(style=RadialButton, color=(0,0,255,255),
                                                                          on_gain_hover=create_message("CONSOLE"), on_click=lambda x: PageManager.goto_page(3)) ),
                      ( kytten.ANCHOR_CENTER, -100, 0, kytten.ImageButton(style=RadialButton, color=(255,255,0,255),
                                                                          on_gain_hover=create_message(), on_click=lambda x: PageManager.goto_page(4)) ),
                      ( kytten.ANCHOR_CENTER, 0, 0,  kytten.ImageButton(  style=RadialButton, color=(255,128,0,255),
                                                                          on_gain_hover=create_message("Exit"), on_click=on_click_exit) )
                    ]                                                     # set callback for event 'on_gain_hover' on button.

    main_page = kytten.Dialog(
                    kytten.VerticalLayout([
                        kytten.Widget(width=256,height=256, name='anchor_widget'),
                        kytten.FreeForm(RADIAL_BUTTONS,                                             # This layout has no size. It is used to layout widgets anywhere on the screen.
                                        widget_anchor=kytten.GetObjectfromName('anchor_widget') )   # relative to the widget_anchor.
                        ], padding=0),
                    graphic=Images['radial_menu'], graphic_flag='stretch',
                    name='radial_dialog', movable=False, anchor=kytten.ANCHOR_CENTER,
                    theme=GUI_Style1, hover_delay=0.5)
                    # the 'hover_delay' parameter is set on each dialog individually (default is 0.3s)
                    # it is used to send 'on_gain_hover' event to controls.

    PageManager.RegisterPage(0, to_show=['navigator_dialog'], # list of dialog name to show for the page
                             constructor=dummy_contructor, # constructor is executed once.
                             callback=None)                # callback is executed every time the page is displayed.

    PageManager.RegisterPage(1, to_show=['radial_dialog'],
                             constructor=dummy_contructor,
                             callback=None)

    PageManager.RegisterPage(2, to_show=['readme_dialog', 'navigator_dialog'],
                             constructor=build_readme_dialog,
                             callback=None)

    PageManager.RegisterPage(3, to_show=['console_dialog', 'navigator_dialog'],
                             constructor=build_console_dialog,
                             callback=None)

    PageManager.goto_page(1)

    # Allow pyglet to run as fast as it can
    HackFunction(window)

    gl.glClearColor(0.33, 0.61, 1, 1)
    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()

    pyglet.app.run()






