# -*- coding: utf-8 -*-
"""
    Python esc/pos network printer API
    ~~~~~~~~~~~~~
    API for managing a network printer via esc/pos protocol.
    :copyright: (c) 2021 by WeRn <wern@lightning-digital.org>.
    :license: MIT, see LICENSE for more details.
"""

__version__ = '1.0.1'

import socket
import time

import six

from commands import PAPER_FULL_CUT, PAPER_PART_CUT
from commands import RT_STATUS_ONLINE, RT_MASK_ONLINE
from commands import RT_STATUS_PAPER, RT_MASK_PAPER, RT_MASK_LOWPAPER, RT_MASK_NOPAPER
from commands import SET_FONT
from commands import TXT_SIZE, TXT_NORMAL
from commands import TXT_STYLE


class NetworkPrinter(object):
    """Network printer
    """

    host: str
    port: int
    timeout: int
    device: socket
    codepage: str

    def __init__(self, host: str, port: int = 9100, timeout: int = 30, autoclose: bool = True, codepage: str = 'cp866'):
        """
        :param host:    Printer's hostname or IP address
        :param port:    Port to write to
        :param timeout: Timeout in seconds for the socket-library
        :param autoclose: Automatic closing of the printer connection
        :param codepage: Default: cp866
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.autoclose = autoclose
        self.codepage = codepage
        self.open()

    def open(self):
        """Open TCP socket with ``socket``-library and set it as escpos device"""
        self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device.settimeout(self.timeout)
        self.device.connect((self.host, self.port))

        if self.device is None:
            print("Could not open socket for {0}".format(self.host))

    def _raw(self, msg):
        """Print any command sent in raw format
        :param msg: arbitrary code to be printed
        :type msg: bytes
        """
        self.device.sendall(msg)

    def _read(self):
        """Read data from the TCP socket"""

        return self.device.recv(16)

    def close(self):
        """Close TCP connection"""
        if self.device is not None:
            try:
                self.device.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            self.device.close()

    def set(self, align="left", font="a", bold=False, underline=0, width=1, height=1, density=9, invert=False, smooth=False,
            flip=False, double_width=False, double_height=False, custom_size=False):
        """Set text properties by sending them to the printer
        :param align: horizontal position for text, possible values are:
            * 'center'
            * 'left'
            * 'right'
            *default*: 'left'
        :param font: font given as an index, a name, or one of the
            special values 'a' or 'b', referring to fonts 0 and 1.
        :param bold: text in bold, *default*: False
        :param underline: underline mode for text, decimal range 0-2,  *default*: 0
        :param double_height: doubles the height of the text
        :param double_width: doubles the width of the text
        :param custom_size: uses custom size specified by width and height
            parameters. Cannot be used with double_width or double_height.
        :param width: text width multiplier when custom_size is used, decimal range 1-8,  *default*: 1
        :param height: text height multiplier when custom_size is used, decimal range 1-8, *default*: 1
        :param density: print density, value from 0-8, if something else is supplied the density remains unchanged
        :param invert: True enables white on black printing, *default*: False
        :param smooth: True enables text smoothing. Effective on 4x4 size text and larger, *default*: False
        :param flip: True enables upside-down printing, *default*: False
        :type font: str
        :type invert: bool
        :type bold: bool
        :type underline: bool
        :type smooth: bool
        :type flip: bool
        :type custom_size: bool
        :type double_width: bool
        :type double_height: bool
        :type align: str
        :type width: int
        :type height: int
        :type density: int
        """

        if custom_size:
            if (
                1 <= width <= 8
                and 1 <= height <= 8
                and isinstance(width, int)
                and isinstance(height, int)
            ):
                size_byte = TXT_STYLE["width"][width] + TXT_STYLE["height"][height]
                self._raw(TXT_SIZE + six.int2byte(size_byte))
        else:
            self._raw(TXT_NORMAL)
            if double_width and double_height:
                self._raw(TXT_STYLE["size"]["2x"])
            elif double_width:
                self._raw(TXT_STYLE["size"]["2w"])
            elif double_height:
                self._raw(TXT_STYLE["size"]["2h"])
            else:
                self._raw(TXT_STYLE["size"]["normal"])

        self._raw(TXT_STYLE["flip"][flip])
        self._raw(TXT_STYLE["smooth"][smooth])
        self._raw(TXT_STYLE["bold"][bold])
        self._raw(TXT_STYLE["underline"][underline])
        self._raw(SET_FONT(six.int2byte(1)))
        self._raw(TXT_STYLE["align"][align])

        if density != 9:
            self._raw(TXT_STYLE["density"][density])

        self._raw(TXT_STYLE["invert"][invert])

    def text(self, txt: str):
        """ Print text

        The text has to be encoded in the currently selected codepage.
        The input text has to be encoded in unicode.

        :param txt: text to be printed
        """
        self._raw(txt.encode(self.codepage))

    def text_ln(self, txt: str):
        """Print text with a newline
        The text has to be encoded in the currently selected codepage.
        The input text has to be encoded in unicode.
        :param txt: text to be printed with a newline
        """
        self.text("{}\n".format(txt))

    def ln(self, count: int = 1):
        """Print a newline or more
        :param count: number of newlines to print
        :raises: :py:exc:`ValueError` if count < 0
        """
        if count < 0:
            raise ValueError("Count cannot be lesser than 0")
        if count > 0:
            self.text("\n" * count)

    def cut(self, mode: str):
        """ Cut paper.

        Without any arguments the paper will be cut completely. With 'mode=PART' a partial cut will
        be attempted. Note however, that not all models can do a partial cut. See the documentation of
        your printer for details.

        .. todo:: Check this function on TM-T88II.

        :param mode: set to 'PART' for a partial cut
        """
        # Fix the size between last line and cut
        # TODO: handle this with a line feed
        self._raw(b"\n\n\n\n\n\n")
        if mode.upper() == "PART":
            self._raw(PAPER_PART_CUT)
        else:  # DEFAULT MODE: FULL CUT
            self._raw(PAPER_FULL_CUT)

    def query_status(self, mode):
        """
        Queries the printer for its status, and returns an array of integers containing it.
        :param mode: Integer that sets the status mode queried to the printer.
            - RT_STATUS_ONLINE: Printer status.
            - RT_STATUS_PAPER: Paper sensor.
        :rtype: array(integer)
        """
        self._raw(mode)
        time.sleep(1)
        status = self._read()
        return status

    def is_online(self):
        """
        Queries the online status of the printer.
        :returns: When online, returns ``True``; ``False`` otherwise.
        :rtype: bool
        """
        status = self.query_status(RT_STATUS_ONLINE)
        if len(status) == 0:
            return False
        return not (status[0] & RT_MASK_ONLINE)

    def paper_status(self):
        """
        Queries the paper status of the printer.
        Returns 2 if there is plenty of paper, 1 if the paper has arrived to
        the near-end sensor and 0 if there is no paper.
        :returns: 2: Paper is adequate. 1: Paper ending. 0: No paper.
        :rtype: int
        """
        status = self.query_status(RT_STATUS_PAPER)
        if len(status) == 0:
            return 2
        if status[0] & RT_MASK_NOPAPER == RT_MASK_NOPAPER:
            return 0
        if status[0] & RT_MASK_LOWPAPER == RT_MASK_LOWPAPER:
            return 1
        if status[0] & RT_MASK_PAPER == RT_MASK_PAPER:
            return 2

    def __exit__(self, type, value, traceback):
        if self.autoclose:
            self.close()