#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# examples/example_basic0.py
# Copyrighted (C) 2014 by "Parashurama"
from __future__ import absolute_import, unicode_literals, division, print_function
import os
import sys
import pyglet
import string

 # allow import from parent folder (1 level up)
sys.path.extend(['.','..'])
import kytten

def HackFunction(window):# Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
        window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)


def on_spin_stats_points(spinctrl, value):
    kytten.GetObjectfromName('label_remaining_points').set_text( 'RemainingPoints: {}'.format(StatSpinControls.remaining_credit ) )

def on_select_dropdown0(*args):
    print ("selected ", args)

def on_check_plural(checkbox, state):
    print("on_check_plural ", state)

def on_input_initial_credit(widget, text):
    try: credit = int(text)
    except ValueError: pass
    else:
        StatSpinControls.set_credit(credit)
        on_spin_stats_points(None, None)

def on_set_luminosity(slider, value):
    print("on_slide_luminosity {:.2%}".format(value))

def on_set_multiplier(slider, value):
    print("on_set_multiplier {}".format(value))

def on_click_placeholder(btn):
    print("on_click_placeholder fake button", value)

def on_text_multiline_input(minput, text):
    print("on_text_multiline_input", text)

def on_click_toggle_mode(btn):
    print("on_click_toggle_mode set mode", btn.text)

STATS_LABELS = ["Strength", "Agility", "Dexterity", "Cleverness", "Constitution", "Willpower"]
MENUS_LIST = ["None", "Plants", "Creatures", "Planets", "Rocks", "Elements", "Colors", "Waves", "Sounds"]
INITIAL_CREDIT = 10

if __name__ == '__main__':
    # Initialize pyglet.window.Window or Subclass
    window = pyglet.window.Window( 800, 800, caption='Example Basic 1', resizable=True, vsync=False )

    kytten.SetWindow(window) # important to correctly initialize kytten before trying to create Gui widgets

    # Load KyttenTheme
    Theme = kytten.Theme('theme', override={
        #"gui_color": [64, 128, 255, 255],
        "text_color": [0,35,0,255],
        "font_size": 16
    })

    # for doc: see example_basic0.py
    GUI_Style1=kytten.GuiTheme( window=window, batch=kytten.KyttenManager,
                                group=kytten.KyttenManager.foregroup, movable=True,
                                always_on_top=False, theme=Theme )

    # Duplicate GUiTheme and override some values
    GUI_Style2=kytten.GuiTheme( movable=False, always_on_top=True,
                                theme=GUI_Style1, override={ "gui_color": [210, 225, 255, 220]} )

    #Used to control SpinButtons (optional)
    StatSpinControls=kytten.SpinControlGroup(value=0, minv=-2, maxv=5, step=1, credit=INITIAL_CREDIT, text_style=dict(font_size=11) )

    #Used to control ToggleButtons
    Choice=kytten.ToggleGroup()

    def get_popup(btn):
        kytten.PopupConfirm("This is a PopupConfirm Dialog: Yes or No?", theme=GUI_Style2, anchor=kytten.ANCHOR_CENTER)

    def get_spinctrl(index):
        return kytten.SpinControl(name='stat{}'.format(index), on_spin=on_spin_stats_points, ctrlgroup=StatSpinControls)

    MenuForm = kytten.Dialog(   kytten.VerticalLayout([
                                    kytten.HorizontalLayout([
                                        kytten.Label("Enter Initial credit: "),
                                        kytten.Input(text=str(INITIAL_CREDIT), max_length=3, length=4, restricted=string.digits, on_input=on_input_initial_credit)
                                    ]),
                                    kytten.Label(text='RemainingPoints: {}'.format(StatSpinControls.remaining_credit ), name="label_remaining_points"),
                                    kytten.GridLayout([
                                        (kytten.Label("{} :".format(stat_label)), get_spinctrl(idx) ) for idx, stat_label in enumerate(STATS_LABELS)],
                                        anchor=kytten.ANCHOR_LEFT),

                                    kytten.HorizontalLayout([
                                        kytten.Dropdown(MENUS_LIST, max_height=120, on_select=on_select_dropdown0),
                                        kytten.Button("Placeholder", on_click=get_popup),
                                        kytten.Checkbox("Plural", on_click=on_check_plural),
                                    ]),
                                    kytten.Slider(0.5, 0, 1, width=150, on_set=on_set_luminosity),
                                    kytten.Slider(50, 0, 100, steps=25, width=150, on_set=on_set_multiplier),
                                    kytten.HorizontalLayout([
                                        kytten.ToggleButton("btn0", toggle=Choice, on_click=on_click_toggle_mode),
                                        kytten.ToggleButton("btn1", toggle=Choice, on_click=on_click_toggle_mode),
                                        kytten.ToggleButton("btn2", toggle=Choice, on_click=on_click_toggle_mode),
                                    ]),
                                    kytten.MultilineInput("Multiline Input", width = 250, height = 100, on_input=on_text_multiline_input)
                                ], align = kytten.HALIGN_LEFT, padding=15),
                        title="Most common Widgets.", theme=GUI_Style1, name='MenuForm', offset=(0,0),
                        anchor=kytten.ANCHOR_CENTER, always_on_top=True, movable=True, on_escape=lambda x: kytten.GetObjectfromName('MenuForm').Hide() )

    # Dialog is visible by default
    #MenuForm.Hide()
    #MenuForm.Show()

    # Allow pyglet to run as fast as it can
    HackFunction(window)

    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()

    pyglet.app.run()
