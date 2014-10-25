# a_test.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

# Test dialog using the Kytten GUI

import os
import sys
import pyglet
# Disable error checking for increased performance
pyglet.options['debug_gl'] = False
from pyglet import gl

VERSION = '5.9'

sys.path.extend(['.','..']) # allow import from parent folder (1 level up)
import kytten

import kytten
from background import Background

# Callback functions for dialogs which may be of interest
def on_escape(dialog):
    dialog.teardown()

def create_document_dialog():
    document = pyglet.text.decode_attributed('''
With {bold True}kytten{bold False}, you can harness the power of
{underline (255, 255, 255, 255)}pyglet{underline None}'s documents in a
scrollable window!

{font_name "Courier New"}Change fonts{font_name Lucia Grande},
{italic True}italicize your text,{italic False} and more!

{align "center"}Center yourself!{align "left"}{}
{align "right"}Or go right.{align "left"}

{color (128, 255, 128, 255)}
Express
{color (255, 128, 128, 255)}
yourself
{color (128, 128, 255, 255)}
colorfully!
{color (255, 255, 255, 255}
''')

    dialog = kytten.Dialog(
            kytten.Document(document, width=300, height=150),
        anchor=kytten.ANCHOR_CENTER,
        theme=gui_theme2, on_escape=on_escape)

def create_form_dialog():
    dialog = None
    def on_enter(dialog):
        print("Form submitted!")
        for key, value in dialog.get_values().items():
            print("  %s=%s" % (key, value))
        on_escape(dialog)
    def on_submit(btn):
        on_enter(dialog)
    def on_cancel(btn):
        print("Form canceled.")
        on_escape(dialog)
    dialog = kytten.Dialog(
            kytten.Scrollable(
                kytten.VerticalLayout([
                    kytten.SectionHeader("Personnel Data",
                                         align=kytten.HALIGN_LEFT),
                    kytten.Document("Try tabbing through fields, "
                                    "if offscreen they'll be moved "
                                    "automatically",
                                    width=500),
                    kytten.GridLayout([
                        [kytten.Label("Name"), kytten.Input("Lynx", name="name",
                                                            max_length=20)],
                        [kytten.Label("Job"), kytten.Input("Cat", name="job",
                                                           max_length=80)],
                        [kytten.Label("Hobby"),
                             kytten.Input("Programming", name="hobby")],
                        [kytten.Label("Class"),
                             kytten.Input("Druid", name="class")],
                        [kytten.Label("Disabled"),
                             kytten.Input("Disabled input", name="disabled",
                                          disabled=True)],
                        [kytten.Label("Sign"),
                             kytten.Input("Free to good home", name="sign")],
                        [kytten.Label("Blood Type"),
                             kytten.Input("Red", name="bloodtype")],
                        [kytten.Label("Favored Weapon"),
                             kytten.Input("Claws", name="weapon")],
                    ]),
                    kytten.Checkbox("Full-Time"),
                    kytten.Checkbox("Married", disabled=True),
                    kytten.SectionHeader("Actions",
                                         align=kytten.HALIGN_LEFT),
                    kytten.HorizontalLayout([
                        kytten.Button("Submit", on_click=on_submit),
                        kytten.Button("Disabled", disabled=True),
                        None,
                        kytten.Button("Cancel", on_click=on_cancel),
                    ]),
                ], align=kytten.HALIGN_LEFT),
                height=200, width=360),
        anchor=kytten.ANCHOR_CENTER,
        theme=gui_theme2, on_enter=on_enter, on_escape=on_escape)

def create_scrollable_dialog():
    def on_select(dropdown, choice, index):
        print("Kytten is %s" % choice)

    def on_set(slider, value):
        print("Kytten rating is %0.0f" % value)

    dialog = kytten.Dialog(
            kytten.Scrollable(
                kytten.VerticalLayout([
                    kytten.Label("Rate Kytten from 1 to 10:"),
                    kytten.Slider(7.0, 1.0, 10.0, steps=9, on_set=on_set),
                    kytten.Label("This slider is disabled:"),
                    kytten.Slider(1.0, 1.0, 10.0, steps=9, on_set=on_set,
                                  disabled=True),
                    kytten.Label("Kytten is..."),
                    kytten.Menu(options=["Awesome",
                                         "Cute",
                                         "-Disabled Option",
                                         "Excellent",
                                         "Fantastic",
                                         "Great",
                                         "Supercalifragilistiexpialidocious",
                                         "Terrific"],
                                align=kytten.HALIGN_LEFT, on_select=on_select),
                ], align=kytten.HALIGN_LEFT),
            width=200, height=150),
        anchor=kytten.ANCHOR_CENTER,
        theme=gui_theme2, on_escape=on_escape)

def create_folding_dialog():
    document1 = pyglet.text.decode_attributed("""
Click on the section headers below to open them up.
Jellicle Cats is, of course, copyrighted by T. S. Eliot.
""")
    document2 = pyglet.text.decode_attributed("""
Jellicle cats come out tonight{}
Jellicle cats come one, come all{}
The Jellicle moon is shining bright{}
Jellicles come to the Jellicle ball
""")
    document3 = pyglet.text.decode_attributed("""
Jellicle cats are black and white{}
Jellicle cats are rather small{}
Jellicle cats are merry and bright{}
And pleasant to hear when we caterwaul
""")
    document4 = pyglet.text.decode_attributed("""
Jellicle cats have cheerful faces{}
Jellicle cats have bright black eyes{}
We like to practice our airs and graces{}
And wait for the Jellicle moon to rise
""")

    dialog = kytten.Dialog(
            kytten.Scrollable(
                kytten.VerticalLayout([
                    kytten.SectionHeader("Jellicle Cats"),
                    kytten.Document(document1, width=300),
                    kytten.FoldingSection("Verse 1",
                        kytten.VerticalLayout([
                            kytten.Document(document2, width=300),
                        ])),
                    kytten.FoldingSection("Verse 2",
                        kytten.VerticalLayout([
                            kytten.Document(document3, width=300),
                        ]), is_open=False),
                    kytten.FoldingSection("Verse 3",
                        kytten.VerticalLayout([
                            kytten.Document(document4, width=300),
                        ]), is_open=False),
                ], align=kytten.HALIGN_LEFT),
            height=400),
        anchor=kytten.ANCHOR_CENTER,
        theme=gui_theme2, on_escape=on_escape)

def create_dropdown_dialog():
    def on_select(dropdown, choice, index):
        print("Selected: %s" % choice)

    dialog = kytten.Dialog(
            kytten.VerticalLayout([
                kytten.Label("Select a letter:"),
                kytten.Dropdown(['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon',
                                 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa',
                                 'Lambda', 'Mu', 'Nu', 'Xi', 'Omicron',
                                 'Pi', 'Rho', 'Sigma', 'Tau', 'Upsilon',
                                 'Phi', 'Chi', 'Psi', 'Omega'],
                                on_select=on_select),
                kytten.Label("This dropdown is disabled"),
                kytten.Dropdown(['Disabled', 'Enabled'], disabled=True),
            ]),
        anchor=kytten.ANCHOR_CENTER,
        theme=gui_theme2, on_escape=on_escape)

def create_file_load_dialog():
    dialog = None

    def on_select(dropdown, filename, index):
        print("File load: %s" % filename)
        on_escape(dialog)

    dialog = kytten.FileLoadDialog(  # by default, path is current working dir
        extensions=['.png', '.jpg', '.bmp', '.gif'],
        anchor=kytten.ANCHOR_CENTER,
        theme=gui_theme2, on_escape=on_escape, on_select=on_select)

def create_file_save_dialog():
    dialog = None

    def on_select(filename, index):
        print("File save: %s" % filename)
        on_escape(dialog)

    dialog = kytten.FileSaveDialog(  # by default, path is current working dir
        extensions=['.png', '.jpg', '.bmp', '.gif'],
        anchor=kytten.ANCHOR_CENTER,
        theme=gui_theme2, on_escape=on_escape, on_select=on_select)

def create_directory_select_dialog():
    dialog = None

    def on_select(dropdown, filename, index):
        print("Directory: %s" % filename)
        on_escape(dialog)

    dialog = kytten.DirectorySelectDialog(
        anchor=kytten.ANCHOR_CENTER,
        theme=gui_theme2, on_escape=on_escape, on_select=on_select)

def on_select(dropdown, choice, index):
    if choice == 'Document':
        create_document_dialog()
    elif choice == 'Form':
        create_form_dialog()
    elif choice == 'Scrollable':
        create_scrollable_dialog()
    elif choice == 'Folding':
        create_folding_dialog()
    elif choice == 'Dropdown':
        create_dropdown_dialog()
    elif choice == 'File Load':
        create_file_load_dialog()
    elif choice == 'File Save':
        create_file_save_dialog()
    elif choice == 'Directory Select':
        create_directory_select_dialog()
    else:
        print("Unexpected menu selection: %s" % choice)

if __name__ == '__main__':
    window = pyglet.window.Window( 640, 480, caption='Kytten Test %s' % VERSION, resizable=True, vsync=False)
    kytten.SetWindow(window)

    gui_theme=kytten.GuiTheme( window=window, batch=kytten.KyttenManager,
                                group=kytten.KyttenManager.foregroup, movable=True,
                                always_on_top=False, theme='theme', override={"text_color":[0,75,25,255], "font_size": 14})

    gui_theme2=kytten.GuiTheme( theme=gui_theme, override={"font_size": 12})

    fps = pyglet.clock.ClockDisplay()

    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()
        fps.draw()

    # Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
        window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)

    # Set up a background which changes when user hits left or right arrow
    background = Background(batch=kytten.KyttenManager, group=kytten.KyttenManager.backgroup)
    window.push_handlers(background)

    # Set up a Dialog to choose test dialogs to show
    dialog = kytten.Dialog(
            kytten.VerticalLayout([
                kytten.Label("Select dialog to show"),
                kytten.Menu(options=["Document", "Form", "Scrollable",
                                     "Folding", "Dropdown",
                                     "File Load", "File Save",
                                     "Directory Select"],
                            on_select=on_select),
            ]),
        title="Kytten Demo", anchor=kytten.ANCHOR_TOP_LEFT,
        theme=gui_theme)

    # Change this flag to run with profiling and dump top 20 cumulative times
    if True:
        pyglet.app.run()
    else:
        import cProfile
        cProfile.run('pyglet.app.run()', 'kytten.prof')
        import pstats
        p = pstats.Stats('kytten.prof')
        p.strip_dirs()
        p.sort_stats('cumulative')
        p.print_stats(20)
