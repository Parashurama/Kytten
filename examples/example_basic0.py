import os
import sys
import pyglet

from pyglet.gl import *

 # allow import from parent folder (1 level up)
sys.path.extend(['.','..'])
import kytten



def HackFunction(window):# Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
        window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)

if __name__ == '__main__':
    # Subclass pyglet.window.Window
    window = pyglet.window.Window( 640, 480, caption='Kytten Test', resizable = True, vsync = False )

    kytten.SetWindow(window) # important to correctly initialize kytten before trying to create Gui widgets

    Theme = kytten.Theme('../theme', override={
        #"gui_color": [64, 128, 255, 255],
        "text_color": [0,100,255,255],
        "font_size": 16
    })

    dialog = kytten.Dialog(
            kytten.TitleFrame('Kytten Test',
                kytten.VerticalLayout([
                    kytten.Label("Select dialog to show"),
                    kytten.Menu(options=["Document", "Form", "Scrollable"] ),
                ]),
            ),
            window=window, batch=kytten.KyttenManager, group=kytten.KyttenManager.foregroup,
            anchor=kytten.ANCHOR_TOP_LEFT,
            theme=Theme)

    # Allow pyglet to run as fast as it can
    HackFunction(window)

    @window.event
    def on_draw():
        window.clear()
        kytten.KyttenRenderGUI()

    pyglet.app.run()
