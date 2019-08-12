"""
This contains utility functions for use with the zebra printer
"""

import logging

from .driver import DEFAULT_FONTS

__author__ = 'Stephen Brown (Little Fish Solutions LTD)'

log = logging.getLogger(__name__)


def set_printer_settings(zebra, connect=True):
    log.info('Setting Zebra printer settings')

    if connect:
        zebra.connect()

    zebra.set_print_width(815)
    zebra.set_label_length(316)
    zebra.set_inverted(False)
    zebra.set_mirrored(False)
    zebra.set_label_home(0, 0)
    zebra.send_message()

    if connect:
        zebra.disconnect()


# Some useful debug things:
def print_position_guide(zebra, connect=True):
    log.info('Printing Zebra position guide')

    if connect:
        zebra.connect()

    zebra.font = '0'
    zebra.char_size = (20, 20)

    for i in range(20):
        zebra.pos = (i * 50, 30)
        zebra.write_text(zebra.pos[0])

    for i in range(20):
        zebra.pos = (30, i * 50)
        zebra.write_text(zebra.pos[1])

    zebra.send_message()

    if connect:
        zebra.disconnect()


def print_font0_size_guide(zebra, connect=True):
    log.info('Printing Zebra font0 size guide')

    if connect:
        zebra.connect()

    zebra.font = '0'
    zebra.char_size = (50, 50)
    zebra.pos = (450, 30)
    zebra.write_text('Font: 0')

    for i in range(1, 20):
        size = 10 + i * 10
        zebra.char_size = (size, size)
        zebra.pos = (30, i * 50 - 25)
        zebra.write_text('char_size: (%s, %s)' % (size, size))

    zebra.send_message()

    if connect:
        zebra.disconnect()


def print_font_guide(zebra, connect=True):
    log.info('Printing Zebra font guide')

    if connect:
        zebra.connect()

    zebra.font = '0'
    zebra.char_size = (4, 4)

    for i in range(6):
        zebra.pos = (30, i * 50 + 15)
        zebra.font = DEFAULT_FONTS[i]
        zebra.write_text('%s:abcd' % zebra.font)

    for i in range(5):
        zebra.pos = (250, i * 65 + 15)
        zebra.font = DEFAULT_FONTS[(i + 6)]
        zebra.write_text('%s:abcd' % zebra.font)

    for i in range(5):
        zebra.pos = (550, i * 50 + 15)
        zebra.font = DEFAULT_FONTS[(i + 11)]
        zebra.write_text('%s:abcd' % zebra.font)

    zebra.send_message()

    if connect:
        zebra.disconnect()
