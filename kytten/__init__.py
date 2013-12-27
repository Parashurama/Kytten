#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/__init__.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
'''
kytten - a skinnable, easily constructed GUI toolkit for pyglet

Inspired by simplui (Tristam MacDonald) and many other GUI projects.
Thanks to Gary Herron and Steve Johnson for debugging assistance!
'''
from __future__ import unicode_literals, print_function

# GUI public constants

from .layout import VALIGN_TOP, VALIGN_CENTER, VALIGN_BOTTOM
from .layout import HALIGN_LEFT, HALIGN_CENTER, HALIGN_RIGHT
from .layout import ANCHOR_TOP_LEFT, ANCHOR_TOP, ANCHOR_TOP_RIGHT, \
                   ANCHOR_LEFT, ANCHOR_CENTER, ANCHOR_RIGHT, \
                   ANCHOR_BOTTOM_LEFT, ANCHOR_BOTTOM, ANCHOR_BOTTOM_RIGHT

# GUI public classes

from .button import Button, ButtonStyle, ImageButton, DraggableImageButton
from .togglebutton import ToggleGroup, ToggleButton, ToggleImageButton
from .spin_button import SpinControl, SpinControlGroup
from .checkbox import Checkbox
from .dialog import Dialog, PopupMessage, PopupConfirm, PropertyDialog, ToolTip, GuiElement, GuiTheme
from .document import Document
from .file_dialogs import FileLoadDialog, FileSaveDialog, DirectorySelectDialog
from .frame import Frame, TitleFrame, GuiFrame, Wrapper, SectionHeader, FoldingSection
from .layout import GridLayout, HorizontalLayout, VerticalLayout, FreeLayout, FreeForm, InteractiveLayout
from .menu import Menu, Dropdown, MenuList
from .scrollable import Scrollable
from .slider import Slider
from .text_input import Input, MultilineInput
from .theme import Theme
from .widgets import Widget, Spacer, Label, Control, Image
from .color_selector import ColorSelector, ColorWheel
from .base import GetObjectfromId, GetObjectfromName, ReferenceName, DisplayGroup, GetActiveDialogs
from .base import InvalidWidgetNameError
from .manager import GuiManager, PageManager
from .selectable_image import Selectable
from .images import LoadImage

def SetWindow(window, manager=None, isBuffered=True):
    global KyttenManager, KyttenRenderGUI
    from .theme import DEFAULT_EMPTY_THEME

    if manager is not None and not isinstance(manager, GuiManager):
        raise TypeError('Invalid Gui Manager instance. Only GuiManager instance or subclass are supported.')
    base.KyttenManager = manager is not None or GuiManager(window, isBuffered=isBuffered)

    KyttenManager = base.KyttenManager
    KyttenRenderGUI = base.KyttenManager.Render

    # Initialize Elements
    from .base import __int__
    from .theme import KyttenTexture
    __int__.BlankTexture = KyttenTexture( [ 255 ]*16, 'ubyte', (2,2))

    from .dialog import DragNDrop
    DragNDrop( Frame(),
        window=window, batch=KyttenManager, group=KyttenManager.foregroup,
        offset=(0,0), theme=DEFAULT_EMPTY_THEME, name='DRAGGABLE', anchor=ANCHOR_BOTTOM_LEFT, always_on_top=False)
