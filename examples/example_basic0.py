#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# examples/example_basic0.py
# Copyrighted (C) 2014 by "Parashurama"
from __future__ import unicode_literals, print_function

import os
import sys
import pyglet

 # allow import from parent folder (1 level up)
sys.path.extend(['.','..'])
import kytten


def HackFunction(window):# Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
        window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)

def on_click_show_panel(btn):
    # If a widget has a registered name, access it with this function.
    kytten.GetObjectfromName('PanelDialog').Show()

def on_escape_quit_dialog(dialog):
    dialog.Hide()

def on_exit(btn):
    raise SystemExit

if __name__ == '__main__':
    # Subclass pyglet.window.Window
    window = pyglet.window.Window( 640, 480, caption='Example Basic 0', resizable = True, vsync = False )

    # important to correctly initialize kytten before trying to create Gui widgets
    kytten.SetWindow(window)

    # Create GuiTheme with classic needed parameters
    # @param window pyglet.Window instance for event handling
    # @param batch  pyglet batch (here kytten.KyttenManager) and pyglet_group
    # @param group  pyglet group (kytten.KyttenManager.foregroup)
    # @param theme  either other GuiTheme instance, kytten Theme instance or path/to/theme/folder
    # @param override used to override theme values.
    # others arguments are default values to create dialogs
    GUI_Style1=kytten.GuiTheme( window=window, batch=kytten.KyttenManager,
                                group=kytten.KyttenManager.foregroup, movable=True,
                                always_on_top=False, theme='theme', override={"text_color": [0,25,20,255], "font_size":16})

    # Load Image from file
    image= kytten.LoadImage("images/background1.jpg")

    # Create a simple Dialog with a Title and the default graphic.
    dialog = kytten.Dialog(
                kytten.VerticalLayout([
                    kytten.Button("Show Panel", on_click=on_click_show_panel),
                    kytten.Button("Exit", on_click=on_exit),
                ], align=kytten.HALIGN_LEFT),
            title='Simple Menu 0', anchor=kytten.ANCHOR_CENTER, theme=GUI_Style1, movable=False)


    # Create a simple Panel and the default graphic.
    panel = kytten.Dialog(
                kytten.VerticalLayout([
                    kytten.Label("This is an Image"),
                    kytten.Image(image, size=(256, 256)),
                ], align=kytten.HALIGN_LEFT),
            anchor=kytten.ANCHOR_CENTER, theme=GUI_Style1, name="PanelDialog", always_on_top=True, on_escape=on_escape_quit_dialog)

    # Hide panel dialog. Dialogs are visible by default when they are created
    panel.Hide()

    # Allow pyglet to run as fast as it can
    HackFunction(window)

    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()

    pyglet.app.run()
