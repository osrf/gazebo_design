#!/usr/bin/env python
#
# Copyright 2008 Jose Fonseca
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import gtk
import gtk.gdk

import xdot


class MyDotWindow(xdot.DotWindow):

    def __init__(self):
        xdot.DotWindow.__init__(self)
        self.widget.connect('clicked', self.on_url_clicked)

    def on_url_clicked(self, widget, url, event):
        print("clicked!")
        dialog = gtk.MessageDialog(
                parent = self,
                buttons = gtk.BUTTONS_OK,
                message_format="%s clicked" % url)
        dialog.connect('response', lambda dialog, response: dialog.destroy())
        dialog.run()
        return True



dotcode = """
digraph G {

  world [URL="http://en.wikipedia.org/wiki/World"]

  // frames

  mframe  [shape=box URL="toto"]
  j1frame [shape=box]
  j2frame [shape=box]
  j3frame [shape=box]

  l1frame [shape=box]
  l1j1frame [shape=box]
  l1j2frame [shape=box]

  l2frame [shape=box]
  l2j1frame [shape=box]

  l3frame [shape=box]
  l3j2frame [shape=box]
  l3j3frame [shape=box]

  l4frame [shape=box]
  l4j3frame [shape=box]

  // entities
  world
  robo
  link1
  link2
  link3
  link4

  joint1
  joint2
  joint3

  subgraph entities {

    edge [color = blue] // [arrowhead = none]
    robo -> world
    link1 -> robo
    link2 -> robo
    link3 -> robo
    link4 -> robo
    joint1 -> robo
    joint2 -> robo
    joint3 -> robo

    mframe -> robo
    l1frame -> link1
    l1j1frame -> link1
    l1j2frame -> link1

    l2frame -> link2
    l2j1frame -> link2

    l3frame -> link3
    l3j2frame -> link3
    l3j3frame -> link3

    l4frame -> link4
    l4j3frame -> link4

    j1frame -> joint1
    j2frame -> joint2
    j3frame -> joint3
  }

  subgraph joints {
    edge [color = DarkGreen arrowhead = dot  style = dotted]

    joint1 -> link2
    joint1 -> link1

    joint2 -> link3
    joint2 -> link1

    joint3 -> link4
    joint3 -> link3

  }

  subgraph frames {
    edge [color = red style = dashed]

    mframe -> world

    l1frame -> mframe
    l1j2frame -> l1frame
    l1j1frame -> l1frame

    j1frame -> l1j1frame
    j2frame -> l1j2frame
    l2frame -> j1frame

    l4j3frame -> l4frame
    l4frame -> j3frame

    j3frame -> l3j3frame
    l3j3frame -> l3frame
    l3j2frame ->l3frame
    l3frame -> j2frame

    l2j1frame ->l2frame


  }


}
"""


def main():
    window = MyDotWindow()
    window.set_dotcode(dotcode)
    window.connect('destroy', gtk.main_quit)
    gtk.main()


if __name__ == '__main__':
    main()
