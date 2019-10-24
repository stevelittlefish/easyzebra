"""
This contains utility functions for use with the zebra printer
"""

import logging
from abc import ABC, abstractmethod

from .driver import DEFAULT_FONTS

__author__ = 'Stephen Brown (Little Fish Solutions LTD)'

log = logging.getLogger(__name__)


class ZebraLabel(ABC):
    """
    Base class for all labels.

    Zebra Label classes are basically designs for labels, and instances are designs for
    a specific product or situation.  These objects allow you to either just build the ZPL
    or to print the label directly to the printer.

    This class may produce more than 1 label too - any number of labels can be printed.
    """

    @abstractmethod
    def build_zpl(self, zebra):
        """
        This method must build the ZPL in the zebra printer driver but not send it.  After this
        is called the zebra driver will have the ZPL in its buffer where it can either be sent
        or retrieved.

        :param zebra: Zebra printer object
        """
        pass

    def print_label(self, zebra, connect=True, host_override=None):
        """
        Print the label
        
        :param zebra: Zebra printer driver
        :param connect: If True, this will connect and disconnect, otherwise it will attempt to
                        use an existing connection (so you can connect once, send a batch of
                        labels and then disconnect manually)
        :param host_override: Set this to override the default Zebra printer host
        """
        if connect:
            zebra.connect()

        self.build_zpl(zebra)

        zebra.send_message(host_override=host_override)

        if connect:
            zebra.disconnect()

    def get_zpl(self, zebra):
        """
        Get the ZPL for this label.  Note that if other labels have been built before this one and
        the zebra printer buffer is not cleared, then multiple labels will be concatenated and
        returned by this function.

        :param zebra: The Zebra printer object
        """
        self.build_zpl(zebra)
        return zebra.get_message()


class ZebraLabelList(ZebraLabel):
    """
    Allows multiple labels to be grouped together and treated as a single label
    """
    def __init__(self, labels=[]):
        self.labels = labels[:]

    def append(self, label):
        self.labels.append(label)

    def build_zpl(self, zebra):
        first = True

        for label in self.labels:
            if first:
                first = False
            else:
                zebra.next_label()

            label.build_zpl(zebra)


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
