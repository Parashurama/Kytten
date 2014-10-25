#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# examples/example_advanced0.py
# Copyrighted (C) 2014 by "Parashurama"
from __future__ import unicode_literals, print_function

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

def dummy(*args, **kwargs):
    pass

TEXT = ["Python has a large standard library, commonly cited as one of Python's greatest strengths,[57] providing tools suited to many tasks. This is deliberate and has been described as a 'batteries included'[17] Python philosophy. For Internet-facing applications, a large number of standard formats and protocols (such as MIME and HTTP) are supported. Modules for creating graphical user interfaces, connecting to relational databases, arithmetic with arbitrary precision decimals,[58] manipulating regular expressions, and doing unit testing are also included. For software testing, the standard library provides the unittest and doctest modules.",
        "Some parts of the standard library are covered by specifications (for example, the WSGI implementation wsgiref follows PEP 333[59]), but the majority of the modules are not. They are specified by their code, internal documentation, and test suite (if supplied). However, because most of the standard library is cross-platform Python code, there are only a few modules that must be altered or completely rewritten by alternative implementations.",
        "The main Python implementation, named CPython, is written in C meeting the C89 standard.[60] It compiles Python programs into intermediate bytecode,[61] which is executed by the virtual machine.[62] CPython is distributed with a large standard library written in a mixture of C and Python. It is available in versions for many platforms, including Microsoft Windows and most modern Unix-like systems. CPython was intended from almost its very conception to be cross-platform.",
        "Google started a project called Unladen Swallow in 2009 with the aims of increasing the speed of the Python interpreter by 5 times by using the LLVM and improving its multithreading ability to scale to thousands of cores.[68] Later the project lost Google's backing and its main developers. As of 1 February 2012, the modified interpreter was about 2 times faster than CPython",
        "In 2005 Nokia released a Python interpreter for the Series 60 mobile phones called PyS60. It includes many of the modules from the CPython implementations and some additional modules for integration with the Symbian operating system. This project has been kept up to date to run on all variants of the S60 platform and there are several third party modules available. The Nokia N900 also supports Python with GTK widget libraries, with the feature that programs can be both written and run on the device itself",
        "Python's development is conducted largely through the Python Enhancement Proposal (PEP) process. The PEP process is the primary mechanism for proposing major new features, for collecting community input on an issue, and for documenting the design decisions that have gone into Python.[69] Outstanding PEPs are reviewed and commented upon by the Python community and by Van Rossum, the Python project's Benevolent Dictator for Life (leader / language architect)"
        ]

if __name__ == '__main__':
    window = pyglet.window.Window(1440,800, caption='Example Advanced 1', vsync=True, resizable=True)   #, config=configy

    kytten.SetWindow(window)

    Images = {}
    Images['menubutton_default'] =kytten.LoadImage('images/menubutton_default.png')
    Images['menubutton_hover'] = kytten.LoadImage('images/menubutton_hover.png')
    Images['menubutton_clicked'] = kytten.LoadImage('images/menubutton_clicked.png')
    #Images['Menu1'] = kytten.LoadImage('images/menu1.png')
    #Images['Menu0'] = kytten.LoadImage('images/menu0.png')

    # Must reference existing folder or another already loaded theme.
    theme = kytten.Theme('theme', override={
        "text_color": [0,50,0,255],
        "font_size": 16
    })

    GUI_Style1=kytten.GuiTheme( window=window, batch=kytten.KyttenManager,
                                group=kytten.KyttenManager.foregroup, movable=True,
                                always_on_top=False, theme=theme)

    # Used to Style Image Button
    MenuButton = kytten.ButtonStyle( Images['menubutton_default'], Images['menubutton_hover'], Images['menubutton_clicked'], size=None,
                                     square=False, has_border=False, is_expandable=True, text_style={'text_padding':(10,10,0,0)})

    # Create a TabbedForm Each correspon to a Tab with a Button.
    # a TabEntry require a ButtonStyle instance, and a content which can be a Widget or a Layout.
    TabbedMenu = kytten.Dialog( kytten.TabbedForm([
                                            kytten.TabEntry(MenuButton, kytten.Document(TEXT[0], width=750), text="tab0"),
                                            kytten.TabEntry(MenuButton, kytten.Document(TEXT[1], width=750), text="tab1"),
                                            kytten.TabEntry(MenuButton, kytten.Document(TEXT[2], width=750), text="tab2"),
                                            kytten.TabEntry(MenuButton, kytten.Document(TEXT[3], width=750), text="tab3"),
                                            kytten.TabEntry(MenuButton, kytten.Document(TEXT[4], width=750), text="tab4"),
                                            kytten.TabEntry(MenuButton, kytten.Document(TEXT[5], width=750), text="tab5"),
                                    ], width=1000, height=400),
                        title="TabbedMenu", gui_style=GUI_Style1, name='TabbedMenu', offset=(0,0),
                        anchor=kytten.ANCHOR_CENTER, always_on_top=True, movable=True, on_escape=lambda x: kytten.GetObjectfromName('TabbedMenu').Hide() )

    # Allow pyglet to run as fast as it can
    HackFunction(window)

    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()

    pyglet.app.run()





