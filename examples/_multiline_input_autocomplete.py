#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# examples/_multiline_input_autocomplete.py
# Copyrighted (C) 2014 by "Parashurama"
from __future__ import absolute_import, unicode_literals, division, print_function
import kytten
import pyglet
import pyglet.window.key as key

# taken from http://world-english.org
# list of most common words in English
with open("ressources/most_common_words_in_english.txt", "r") as f:
    AUTOCOMPLETE_KEYWORDS = f.read().split()


def Default_auto_complete(input_widget, word, position):
    # could be improved with a trie if the word count is high enough
    matching_words = [w for w in AUTOCOMPLETE_KEYWORDS if w.startswith(word) ] if word is not None else None

    if not (word and matching_words) or word in matching_words:
        return kytten.GetObjectfromName('Input_Autocomplete').Hide()

    kytten.GetObjectfromName('Input_Autocomplete').input_widget = input_widget
    kytten.GetObjectfromName('Input_Autocomplete').set_offset(position)
    kytten.GetObjectfromName('Input_Autocomplete_menu').set_options(sorted(matching_words))
    ShowAutocomplete_Menu()

def Default_on_tabulation(input_widget):
    autocomplete_options = kytten.GetObjectfromName('Input_Autocomplete_menu')
    if not autocomplete_options.visible:
        input_widget.dispatch_event("on_text", " "*4)
        return pyglet.event.EVENT_HANDLED

    if autocomplete_options.menu_options:
        kytten.GetObjectfromName('Input_Autocomplete').input_widget.dispatch_event("on_auto_complete", autocomplete_options.menu_options[0].text)
        HideAutocomplete_Menu()
        return pyglet.event.EVENT_HANDLED

def select_auto_complete_option(menu, word, pos):
    kytten.GetObjectfromName('Input_Autocomplete').input_widget.dispatch_event("on_auto_complete", word)
    HideAutocomplete_Menu()

def ShowAutocomplete_Menu():
    autocomplete = kytten.GetObjectfromName('Input_Autocomplete_menu')

    def _wrapper_key_press(symbol, modifiers):
        if (symbol == key.ENTER and not autocomplete.selected_index):
            HideAutocomplete_Menu()
        else:
            return autocomplete.on_key_press(symbol, modifiers)

    def _wrapper_text_motion(motion, select=False):
        if   motion in (key.MOTION_UP,key.MOTION_DOWN):
            return pyglet.event.EVENT_HANDLED

    def _wrapper_mouse_press(x, y, button, modifiers):
        HideAutocomplete_Menu()

    if not kytten.GetObjectfromName('Input_Autocomplete').visible:
        kytten.GetObjectfromName('Input_Autocomplete').Show()
        input_widget = kytten.GetObjectfromName('Input_Autocomplete').input_widget

        if input_widget is not None:
            input_widget.push_handlers(on_key_press=_wrapper_key_press, on_text_motion=_wrapper_text_motion, on_mouse_press=_wrapper_mouse_press)

def HideAutocomplete_Menu():
    if kytten.GetObjectfromName('Input_Autocomplete').visible:
        kytten.GetObjectfromName('Input_Autocomplete').Hide()
        kytten.GetObjectfromName('Input_Autocomplete_menu')
        input_widget = kytten.GetObjectfromName('Input_Autocomplete').input_widget

        if input_widget is not None:
            input_widget.pop_handlers()
