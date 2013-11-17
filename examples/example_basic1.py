#! /usr/bin/env python
# *-* coding: UTF-8 *-*
# Copyrighted (C) 2013 by "Parashurama"

import pyglet
import string
import sys
import os

sys.path.extend(['.','..']) # allow import from parent folder (1 level up)
import kytten

def HackFunction(window):# Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
        window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)


def generator_wrapper(gen):
    def _wrapper(*args):
        try:next(gen)
        except StopIteration:pass

    def _send_wrapper(value):
        try:gen.send(value)
        except StopIteration:pass
    #expose generator send method
    _wrapper.send = _send_wrapper
    return _wrapper


def dummy(*args, **kwargs):
    pass

def ShowFormattedDocument(*args):
    kytten.GetObjectfromName('FormattedDocument').Show()
    text = """
    Most Python implementations (including {color (75, 0, 128, 255)}CPython{color (0, 0, 0, 255)}) can function as a command line interpreter,\
    for which the user enters statements sequentially and receives the results immediately. In short, Python acts as a shell."""
    text2 = """
    Rather than requiring all desired functionality to be built into the language's core, Python was designed to be highly extensible. Python can also be embedded in existing applications that need a programmable interface.
    This design of a small core language with a large standard library and an easily extensible interpreter was intended by Van Rossum from the very start because of his frustrations with ABC (which espoused the opposite mindset)"""

    kytten.GetObjectfromName('FormattedDocument_doc').set_text(text, 'attr')

    def get_next_char():
        for char in text2:
            kytten.GetObjectfromName('FormattedDocument_doc').append_text(char)
            kytten.GetObjectfromName('FormattedDocument_doc').ensure_line_visible(-1) # Ensure that last line is visible
            if (yield None): # If receive value that evaluate to True: abort generator
                break
        pyglet.clock.unschedule(next_char_on_page)

    kytten.GetObjectfromName('FormattedDocument').next_char_on_page = next_char_on_page = generator_wrapper(get_next_char())
    pyglet.clock.schedule_interval(next_char_on_page,0.02)

def HideFormattedDocument(*args):
    kytten.GetObjectfromName('FormattedDocument').next_char_on_page.send(True) # Send value to abort generator
    kytten.GetObjectfromName('FormattedDocument').Hide()

def ShowMenuForm(btn):
    kytten.GetObjectfromName('MenuForm').Show()

def ShowFoldableMenu(btn):
    kytten.GetObjectfromName('FoldableMenuDisplay').Show()

def on_spin_stats_points(spinctrl, value):
    kytten.GetObjectfromName('label_remaining_points').set_text( 'RemainingPoints: {}'.format(StatSpinControls.remaining_credit ) )

def on_input_initial_credit(text):
    try: credit = int(text)
    except ValueError: pass
    else:
        StatSpinControls.set_credit(credit)
        on_spin_stats_points(None, None)

def on_select_dropdown0(*args):
    print ("selected ", args)

if __name__ == '__main__':

    config = pyglet.gl.Config(  sample_buffers=4, samples=16 )

    window = pyglet.window.Window(1440,800, caption='Aeternia', vsync=True, resizable=True)   #, config=configy

    kytten.SetWindow(window)
    Images = {}
    Images['menubutton_default'] =kytten.LoadImage('images/menubutton_default.png')
    Images['menubutton_hover'] = kytten.LoadImage('images/menubutton_hover.png')
    Images['menubutton_clicked'] = kytten.LoadImage('images/menubutton_clicked.png')
    Images['Menu1'] = kytten.LoadImage('images/menu1.png')
    Images['Menu0'] = kytten.LoadImage('images/menu0.png')

    # Must reference existing folder or another already loaded theme.
    Theme = kytten.Theme('../theme', override={
        "gui_color": [0, 50, 0, 255],
        "text_color": [0,50,0,255],
        "font_size": 16
    })

    GUI_Style1=kytten.GuiTheme( window=window, batch=kytten.KyttenManager,
                                group=kytten.KyttenManager.foregroup, movable=True,
                                always_on_top=False, theme=Theme )

    #Used to control SpinButtons (optional)
    StatSpinControls=kytten.SpinControlGroup(value = 0, minv =-2, maxv=5, step=1, credit = 10, text_style=kytten.TextStyle(font_size=11) )
    #Used to control ToggleButtons
    Choice=kytten.ToggleGroup()

    # Used to Style Image Button
    MenuButton = kytten.ButtonStyle( Images['menubutton_default'], Images['menubutton_hover'], Images['menubutton_clicked'], size=None,
                                     square=False, has_border=False, is_expandable=True, text_style={'text_padding':(10,10,0,0)})

    MenuForm = kytten.GuiElement( kytten.VerticalLayout([
                                        kytten.HorizontalLayout([
                                            kytten.Label("Enter Initial credit: "),
                                            kytten.Input(text="10", max_length=3, length=4, restricted=string.digits, on_input=on_input_initial_credit)
                                        ]),
                                        None,
                                        kytten.Label(text='RemainingPoints: {}'.format(StatSpinControls.remaining_credit ), name="label_remaining_points"),
                                        kytten.HorizontalLayout([
                                            kytten.Label( "Strength :\nAgility :\nDexterity :\nCleverness :\nConstitution :\nWillpower :", multiline=True, width=190),
                                            kytten.VerticalLayout([
                                                kytten.SpinControl(name='Stat'+str(n), on_spin=on_spin_stats_points, ctrlgroup=StatSpinControls) for n in range(6)
                                                ], align=kytten.HALIGN_LEFT, padding=9 )
                                        ],align=kytten.VALIGN_TOP, padding=20, name='Statistics'),
                                        kytten.HorizontalLayout([
                                            kytten.Dropdown(["None", "Plants", "Creatures", "Planets"], max_height=80, on_select=on_select_dropdown0),
                                            kytten.Button("Placeholder"),
                                            kytten.Checkbox("Plural"),
                                        ]),
                                        kytten.HorizontalLayout([
                                            kytten.ToggleButton("btn0", toggle=Choice),
                                            kytten.ToggleButton("btn2", toggle=Choice),
                                            kytten.ToggleButton("btn1", toggle=Choice),
                                        ]),
                                        kytten.MultilineInput("Multiline Input", width = 250, height = 100)
                                    ], align = kytten.HALIGN_LEFT, padding=15),# height=250),
                        graphic=Images['Menu1'], gui_style=GUI_Style1, name='MenuForm', offset=(0,0),
                        anchor=kytten.ANCHOR_CENTER, always_on_top=True, movable=True, on_escape=lambda x: kytten.GetObjectfromName('MenuForm').Hide() )


    FoldableMenuDisplay =  kytten.GuiElement(
            kytten.Scrollable(
                kytten.VerticalLayout([
                    kytten.FoldingSection("Abilities",
                        kytten.VerticalLayout([
                            kytten.Label(text="Capacity" ),
                            kytten.Label(text="WalkingSpeed" ),
                            kytten.Label(text="RunningSpeed" ),
                            kytten.Label(text="Initiative" ),
                            kytten.Label(text="Apprenticing" ),
                            ], align=kytten.HALIGN_LEFT, padding=10 ), align=kytten.HALIGN_LEFT  ),
                    kytten.FoldingSection("Physical Ability",
                        kytten.VerticalLayout([
                            kytten.Label(text="PhysicalPower" ),
                            kytten.Label(text="Stamina" ),
                            kytten.Label(text="AttackSpeed" ),
                            kytten.Label(text="AttackAccuracy" ),
                            kytten.Label(text="Reflexes" )
                        ], align=kytten.HALIGN_LEFT, padding=10 ), align=kytten.HALIGN_LEFT  ),
                    kytten.FoldingSection("Mystical Ability",
                        kytten.VerticalLayout([
                            kytten.Label(text="MagicalPower"),
                            kytten.Label(text="Mana"),
                            kytten.Label(text="SpellSpeed"),
                            kytten.Label(text="SpellAccuracy"),
                            kytten.Label(text="Perception" )
                        ], align=kytten.HALIGN_LEFT, padding=10 ), align=kytten.HALIGN_LEFT, is_open=False  ),
                    kytten.FoldingSection("Resistances",
                        kytten.VerticalLayout([
                            kytten.Label(text="PhysicalResistance"),
                            kytten.Label(text="MentalResistance"),
                            kytten.Label(text="MagicalResistance"),
                            kytten.Label(text="FrostResistance"),
                            kytten.Label(text="FireResistance"),
                            kytten.Label(text="ElectricityResistance"),
                            kytten.Label(text="PoisonResistance"),
                            kytten.Label(text="MassiveDamageResistance")
                        ], align=kytten.HALIGN_LEFT, padding=10 ), align=kytten.HALIGN_LEFT, is_open=False  ),
                        kytten.Document(' ',width=340)
                ], align=kytten.HALIGN_LEFT, padding=25 ),
            height=600, width= 340, is_fixed_size=True, child_anchor=kytten.ANCHOR_TOP_LEFT),
                        graphic=Images['Menu1'], gui_style=GUI_Style1, name='FoldableMenuDisplay', offset=(0,0),
                        anchor=kytten.ANCHOR_CENTER, always_on_top=True, movable=True, on_escape=lambda x: kytten.GetObjectfromName('FoldableMenuDisplay').Hide() )


    FormattedDocument = kytten.GuiElement( kytten.Document("", width=600, height=300, text_color=(0,0,0,255), font_size = 17, name='FormattedDocument_doc' ),
                        graphic=Images['Menu1'], gui_style=GUI_Style1, name='FormattedDocument', offset=(0,0),
                        anchor=kytten.ANCHOR_CENTER, always_on_top=True, movable=True, on_escape=HideFormattedDocument )

    GameExitMenu = kytten.GuiElement( kytten.VerticalLayout([
            kytten.Label('Press ESCAPE to quit pop-up menu'),
            kytten.ImageButton(style=MenuButton, text='Display Document', on_click=ShowFormattedDocument),
            kytten.ImageButton(style=MenuButton, text='Show MenuForm' , on_click=ShowMenuForm, name='btn_show_form'),
            kytten.ImageButton(style=MenuButton, text='Show FoldableMenu' , on_click=ShowFoldableMenu, name='btn_show_foldablemenu'),
            kytten.ImageButton(style=MenuButton, text='ShowLabel' , on_click=dummy, name='btn_show_label', disabled=True),
        ],align=kytten.HALIGN_CENTER, padding=25),
      graphic=Images['Menu1'], gui_style=GUI_Style1, name='GameExitMenu', offset=(0,0),
      anchor=kytten.ANCHOR_CENTER, always_on_top=False, movable=False)

    FoldableMenuDisplay.Hide()
    FormattedDocument.Hide()
    MenuForm.Hide()

    # Allow pyglet to run as fast as it can
    HackFunction(window)

    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()

    pyglet.app.run()



