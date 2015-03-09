#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# examples/example_basic0.py
# Copyrighted (C) 2014 by "Parashurama"
from __future__ import absolute_import, unicode_literals, division, print_function
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

def on_click_show_quadrant(btn):
    # If a widget has a registered name, access it with this function.
    kytten.GetObjectfromName('QuadrantDialog').Show()

def on_click_show_text_widgets(btn):
    kytten.GetObjectfromName('TextDialog').Show()

def on_click_show_document(btn):
    kytten.GetObjectfromName('DocumentDialog').Show()


def on_escape_quit_dialog(dialog):
    dialog.Hide()

def on_escape_quit_document_dialog(dialog):
    try:kytten.GetObjectfromName('formatted_document').next_char_on_page.send(True) # Send value to abort generator
    except AttributeError:# Text not appended to document.
        pass
    dialog.Hide()

def on_exit(btn):
    raise SystemExit

def document_add_entry():
    import random
    R = random.randint(0, 256) ; G = random.randint(0, 256) ; B = random.randint(0, 256)
    text = """    {{color ({R}, {G}, {B}, 255)}}NewEntry{{color (0, 0, 0, 255)}}\n """.format(R=R, G=G, B=B)

    # Append text to Document.
    kytten.GetObjectfromName('formatted_document').append_text(text, 'attr')

    # Ensure last line is visible.
    kytten.GetObjectfromName('formatted_document').ensure_line_visible(-1)

def document_write_text():
    def get_next_char():
        for char in DOCUTEXT2:
            kytten.GetObjectfromName('formatted_document').append_text(char)
            kytten.GetObjectfromName('formatted_document').ensure_line_visible(-1) # Ensure that last line is visible
            if (yield None): # If receive value that evaluate to True: abort generator
                break
        pyglet.clock.unschedule(next_char_on_page)

    kytten.GetObjectfromName('formatted_document').next_char_on_page = next_char_on_page = generator_wrapper(get_next_char())
    pyglet.clock.schedule_interval(next_char_on_page,0.02)

def func_call_wrapper(func, *args, **kwargs):
    def _wrapper(*_args):
        func(*args, **kwargs)
    return _wrapper

def generator_wrapper(gen):
    def _wrapper(*args):
        try:next(gen)
        except StopIteration:pass

    def _send_wrapper(value):
        try:gen.send(value)
        except StopIteration:pass

    _wrapper.send = _send_wrapper # expose generator send method
    return _wrapper


BLOOD_RED_COLOR = [106, 25, 25,255]

RICHTEXT =  "{color (255, 255, 0, 255)}This is a {color (75, 0, 128, 255)}{bold True}RichText Widget.{bold False} You can {italic True}{font_size 25}format{font_size None}{italic False} {color (255, 255, 0, 255)}{font_size 32}{italic True}it{font_size None}{italic False}{color (50, 50, 50, 255)} as you want and it uses much less {color (255, 0, 0, 255)}{font_size 18}ressources{font_size None}{color (0, 0, 0, 255)} than a full document widget."

DOCUTEXT2 = "\n    Rather than requiring all desired functionality to be built into the language's core, Python was designed to be highly extensible.\n    Python can also be embedded in existing applications that need a programmable interface.\n    This design of a small core language with a large standard library and an easily extensible interpreter was intended by Van Rossum from the very start because of his frustrations with ABC (which espoused the opposite mindset)."
# Create a pyglet attributed document
DOCUTEXT = pyglet.text.decode_attributed("""
The core philosophy of the language is summarized by the document "PEP 20 (The Zen of Python)", which includes aphorisms such as:[32]

    {color (255, 0, 0, 255)}Beautiful{color (0, 0, 0, 255)} is better than ugly.
    {color (255, 128, 0, 255)}Explicit{color (0, 0, 0, 255)} is better than implicit.
    {color (128, 72, 0, 255)}Simple{color (0, 0, 0, 255)} is better than complex.
    {color (0, 255, 0, 255)}Complex{color (0, 0, 0, 255)} is better than complicated.
    {color (75, 0, 128, 255)}Readability{color (0, 0, 0, 255)} counts.
    {color (0, 128, 128, 255)}{link 'add_text_callback'}{bold True}Clickable Link{bold False}{link false}(adds a new Entry){color (0, 0, 0, 255)}
    {color (128, 0, 128, 255)}{link 'write_text_callback'}{bold True}Write Text{bold False}{link false}(adds a new Entry){color (0, 0, 0, 255)}\n""")
if __name__ == '__main__':
    # Subclass pyglet.window.Window
    window = pyglet.window.Window( 640, 480, caption='Example Basic 2', resizable = True, vsync = False )

    # important to correctly initialize kytten before trying to create Gui widgets
    kytten.SetWindow(window)

    GUI_Style1=kytten.GuiTheme( window=window, batch=kytten.KyttenManager,
                                group=kytten.KyttenManager.foregroup, movable=True,
                                always_on_top=False, theme='theme', override={"text_color": [0,25,20,255], "font_size":16})

    GUI_Style2=kytten.GuiTheme( theme=GUI_Style1, override={"text_color": BLOOD_RED_COLOR, "font_size":16, "bold":True})

    # Load Images from file
    Images = {}
    Images["quadrant"] = kytten.LoadImage("images/quadrant_view.png")
    Images["menubutton_default"] = kytten.LoadImage("images/menubutton_default.png")
    Images["menubutton_hover"] = kytten.LoadImage("images/menubutton_hover.png")
    Images["menubutton_clicked"] = kytten.LoadImage("images/menubutton_clicked.png")

    # create callbacks for links in Document.
    document_callbacks = {}
    document_callbacks['add_text_callback'] = [func_call_wrapper(document_add_entry)]
    document_callbacks['write_text_callback'] = [func_call_wrapper(document_write_text)]

                                    # Set Button texture, in default, clicked and hover mode.
    MenuButton  = kytten.ButtonStyle( Images['menubutton_default'], Images['menubutton_hover'], Images['menubutton_clicked'],
                                      text_style={'text_padding':(10,10,0,0), 'text_color':BLOOD_RED_COLOR},# Button text style
                                      is_expandable=(True, False),# Expand in Width:True, Height:False. is_expandable can also be True or False.
                                      has_border=False, # Has button border
                                      square=False, # force widget width==height.
                                      size=None) # set button size

    # Create a simple Dialog with a Title and the default graphic.
    dialog = kytten.Dialog(
                kytten.VerticalLayout([
                    # Create an ImageButton, with style MenuButton.
                    # ImageButton can also be instanced directly with parameters
                    kytten.ImageButton(style=MenuButton, text="Show Quadrant", on_click=on_click_show_quadrant),
                    kytten.ImageButton(style=MenuButton, text="Show Text Widgets", on_click=on_click_show_text_widgets),
                    kytten.ImageButton(style=MenuButton, text="Show Document", on_click=on_click_show_document),
                    kytten.ImageButton(style=MenuButton, text="Exit", on_click=on_exit),
                ], align=kytten.HALIGN_LEFT),
            title='Simple Menu 0', anchor=kytten.ANCHOR_CENTER, theme=GUI_Style1, movable=False)


    # Create a simple Dialog with a custom graphic.
    panel = kytten.Dialog(kytten.Label("This is a long Label"),
                          graphic=Images["quadrant"], graphic_flag='stretch', anchor=kytten.ANCHOR_TOP_RIGHT, theme=GUI_Style2,
                          name="QuadrantDialog", always_on_top=True, on_escape=on_escape_quit_dialog, movable=False)

    text_dialog = kytten.Dialog(
                kytten.VerticalLayout([
                    kytten.Label("This is an auto-clamped label which has a very long text but doesn't display it all.",
                                  autoclampwidth=350,               # label clamp visible text at specified width.
                                  style={"color":[255,220,0,255]}), # text_syle ex: "italic":True, "bold":False, "font":"Arial", "font_size":16
                    None,
                    kytten.Label(u"This is a Multiline Label. It can be as long as you want, \nbut it can not be directly clamped in a scrollable area.",
                                    multiline=True,
                                    width=350,      #line wrap width
                                    color=[0,128,200,255]), # text_color, can also specified in text_style like above.
                    None,
                    kytten.Input("This is a simple text input"),
                    None,
                    kytten.RichText(RICHTEXT,   width=450,        # line wrap width
                                                formatted="attr", # pyglet formated argument
                                                clamp_height=125, # Doesn't display below height
                                                background_color=[64,128,128,128]),

                ], align=kytten.HALIGN_LEFT),
            anchor=kytten.ANCHOR_TOP_LEFT, theme=GUI_Style1, name="TextDialog", always_on_top=True, on_escape=on_escape_quit_dialog)

    document_dialog = kytten.Dialog(
                kytten.VerticalLayout([
                    kytten.Label("Below is a Document Widget.", style={"color":[255,220,0,255]}),
                    kytten.Document(DOCUTEXT,
                                    width=450,  # width is required for line wrap
                                    height=400, # if height is specified, the document is placed in a scrollable area
                                                # if the text height is larger than specified height
                                    name='formatted_document')
                ], align=kytten.HALIGN_LEFT),
            anchor=kytten.ANCHOR_TOP_LEFT, theme=GUI_Style1, name="DocumentDialog", always_on_top=True, on_escape=on_escape_quit_document_dialog)

    # Set document clickable links callbacks in Document Widget (require a dict-like argument)
    kytten.GetObjectfromName('formatted_document').set_links(document_callbacks)

    # Hide dialogs. Dialogs are visible by default when they are created
    panel.Hide()
    text_dialog.Hide()
    document_dialog.Hide()

    # Allow pyglet to run as fast as it can
    HackFunction(window)
    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()

    pyglet.app.run()
