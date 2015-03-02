#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/images.py
# Copyrighted (C) 2013 by "Parashurama"

from __future__ import unicode_literals, print_function, absolute_import, division
from .compat import *
import pyglet
import json
import os

def  LoadImage(filepath, *args, **kwargs):
    """
    Simple wrapper around pyglet.image.load. Used to add the attributes needed by kytten.
        - id  : opengl texture ID (can be 0, which disable texturing)
        - size: texture size (width, height)
        - texcoords : texture coordinates of region to display , formatting [s0,t0, s1, t1]
    It also load optional image data from <image name>.info such as :
        - header_bar: x0,y0 : bottom_left ; x1, y1 = top_right
            Dragging bar region coordinates: [x0, y0, x1, y1],  defaults to [0,0,None,None] (all widget area)
            None means widget's max dimension and negative value are relative so [0, -40, None, None] means [0, height-40, width, height]
            exemple with texture size :(256, 256)
            exemple with basic value: [0, -40, None, None],  header_bar area is [0, 216, 256, 256]
            exemple with negative value: [0, -40, None, -20],  header_bar area is [0, 216, 256, 236]
        - content_padding : minimum internal padding around content. [left, right, top, bottom]
        - border_padding : used for the 9-patches formatting. [left, right, top, bottom]
    """
    image = pyglet.image.load(filepath, *args, **kwargs).get_texture()

    s0,t0,_, s1,t0,_, s1, t1, _, s0, t1, _ =  image.tex_coords

    #bottom-left, top-right opengl texture coordinates wich is different from pyglet texture 'tex_coords' (12 float tuple)
    image.texcoords = (s0,t0,s1,t1)

    image.size = (float(image.width), float(image.height))
    image.border_padding=(0,0,0,0)
    image.content_padding=(0,0,0,0)
    image.header_bar=(0,0,None,None)

    # Parse image info if present to override image attributes
    try:                 # strip extension
        info_file= open(os.path.splitext(filepath)[0]+'.info', 'rb')
    except IOError:
        pass
    else:
        image_attributes = json.loads(info_file.read().decode("utf-8"))
        for attribute, value in image_attributes.items():
            setattr(image,attribute,value)
    return image

