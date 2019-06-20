"""
This module contains the zebra label printer driver
"""

import logging
import socket
from struct import unpack
import binascii

import requests
from unidecode import unidecode

__author__ = 'Stephen Brown (Little Fish Solutions LTD)'

log = logging.getLogger(__name__)

FONTS = 'ABCDEFGH0PQRSTUV'

MODE_SOCKET = 'SOCKET'
MODE_HTTP = 'HTTP'
MODE_HTTPS = 'HTTPS'

ALL_MODES = [MODE_SOCKET, MODE_HTTP, MODE_HTTPS]

JUSTIFICATION_LEFT = 'L'
JUSTIFICATION_CENTRE = 'C'
JUSTIFICATION_RIGHT = 'R'
JUSTIFICATION_JUSTIFIED = 'J'


class Zebra(object):
    def __init__(self, host, port=9100, mode=MODE_SOCKET, http_endpoint=None,
                 timeout=None):
        """
        :param host: The zebra printer host
        :param port: The zebra printer port
        :param mode: The mode: either 'SOCKET', 'HTTP' or 'HTTPS'
        :param http_endpoint: The URL for http / https requests.  Ignored if mode is socket
        :param timeout: The timeout, in seconds, after which to give up waiting for a request
                        to the printer to succeed
        :return:
        """
        if (mode == MODE_HTTP or mode == MODE_HTTPS) and not http_endpoint:
            raise ValueError('You must supply an endpoint when using mode {}'.format(mode))

        self.host = host
        self.port = port
        self.socket = None
        self._mode = None
        self.mode = mode
        self.http_endpoint = http_endpoint
        self.timeout = timeout

        # The current label we are building up code for
        self.current_message = []
        # The offset for drawing functions
        self.pos = (0, 0)
        # Character size for text
        self.char_size = (50, 40)
        # Font for text printing
        self._font = '0'

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if value not in ALL_MODES:
            raise Exception('Invalid mode: %s.  Valid options are %s' % (value, ALL_MODES))
        self._mode = value
    
    def get_url(self, host_override=None, port_override=None):
        host = host_override if host_override else self.host
        port = port_override if port_override else self.port

        if self.mode == MODE_HTTP or self.mode == MODE_HTTPS:
            protocol = 'http' if self.mode == MODE_HTTP else 'https'
            return '%s://%s:%s%s' % (protocol, host, port, self.http_endpoint)
        else:
            assert self.mode == MODE_SOCKET
            return '{}:{}'.format(host, port)

    def connect(self):
        if self.mode == MODE_SOCKET:
            log.info('Connecting to Zebra printer %s:%s' % (self.host, self.port))
            if self.socket:
                try:
                    self.socket.close()
                except socket.error:
                    pass

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.timeout:
                self.socket.settimeout(self.timeout)

            try:
                self.socket.connect((self.host, self.port))
            except socket.error:
                log.exception('Couldn\'t connect to Zebra printer')
                self.socket = None
                raise Exception('Couldn\'t connect to Zebra printer')

    def disconnect(self):
        if self.mode == MODE_SOCKET:
            try:
                self.socket.close()
            except socket.error as e:
                log.warn('Error closing socket: %s' % e)

    def _send(self, message, host_override=None, port_override=None):
        if self.mode == MODE_SOCKET:
            if host_override or port_override:
                raise Exception('Host and port override not implemented for socket connections')

            if not self.socket:
                raise Exception('Zebra printer not connected (%s:%s)' % (self.host, self.port))
            # Send some junk first to detect closed connections
            # self.socket.send('^XA^XZ')

            total_sent = 0
            length = len(message)
            while total_sent < length:
                sent = self.socket.send(message[total_sent:])
                if sent == 0:
                    raise Exception('Socket connection broken')
                total_sent += sent
        elif self.mode == MODE_HTTP or self.mode == MODE_HTTPS:
            url = self.get_url(host_override, port_override)
            payload = {'zpl': message}
            response = requests.post(url, data=payload, verify=False, timeout=self.timeout)
            response_json = response.json()
            if response_json['error']:
                raise Exception('Error sending http request to printer: %s' % response_json['error'])
        else:
            raise Exception('Unhandled mode: %s' % self.mode)

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        if value not in FONTS:
            raise Exception('Invalid font: %s.  Possible value are %s' % (value, FONTS))
        self._font = value

    def message_line(self, line):
        self.current_message.append(line.encode('utf-8'))

    def field_origin(self, pos=None):
        if pos is None:
            pos = self.pos
        self.message_line('^FO%s,%s' % pos)

    def field_separator(self):
        self.message_line('^FS')

    def write_text(self, text, pos=None, char_size=None, font=None):
        if char_size is None:
            char_size = self.char_size

        if font is None:
            font = self.font

        if isinstance(text, str):
            ascii_text = unidecode(text)
        else:
            ascii_text = text

        self.field_origin(pos)
        self.message_line('^A%sN,%s,%s' % (font, char_size[0], char_size[1]))
        self.message_line('^FD%s' % ascii_text)
        self.field_separator()

    def write_text_block(self, text, width, max_lines=1, justification=JUSTIFICATION_LEFT,
                         add_line_space=0, pos=None, char_size=None, font=None,
                         hanging_indent=0):
        if char_size is None:
            char_size = self.char_size

        if font is None:
            font = self.font

        if isinstance(text, str):
            ascii_text = unidecode(text)
        else:
            ascii_text = text

        self.field_origin(pos)
        self.message_line('^A%sN,%s,%s' % (font, char_size[0], char_size[1]))
        self.message_line('^FB%s,%s,%s,%s,%s' % (width, max_lines, add_line_space, justification,
                                                 hanging_indent))
        self.message_line('^FD%s' % ascii_text)
        self.field_separator()

    def draw_box(self, width, height, thickness=1, colour='B', rounding=0, pos=None):
        self.field_origin(pos)
        self.message_line('^GB%s,%s,%s,%s,%s' % (width, height, thickness, colour, rounding))
        self.field_separator()

    def draw_horizontal_line(self, length, thickness=1, colour='B', pos=None):
        self.draw_box(length, 0, thickness, colour, 0, pos)

    def draw_vertical_line(self, length, thickness=1, colour='B', pos=None):
        self.draw_box(0, length, thickness, colour, 0, pos)

    def upload_bitmap(self, zebra_bitmap):
        self.message_line(zebra_bitmap.upload_cmd)

    def render_bitmap(self, zebra_bitmap, scale=(1, 1), pos=None):
        self.field_origin(pos)
        self.message_line('^XGd:%s.GRF,%s,%s' % (zebra_bitmap.zebra_handle, scale[0], scale[1]))
        self.field_separator()

    def set_print_width(self, print_width):
        self.message_line('^PW%s' % print_width)

    def set_label_length(self, label_length):
        self.message_line('^LL%s' % label_length)

    def set_inverted(self, inverted):
        self.message_line('^PO%s' % ('I' if inverted else 'N'))

    def set_mirrored(self, mirrored):
        self.message_line('^PM%s' % ('Y' if mirrored else 'N'))

    def set_label_home(self, x, y):
        self.message_line('^LH%s,%s' % (x, y))

    @property
    def zpl(self):
        return b'^XA\n\n' + b'\n'.join(self.current_message) + b'\n\n^XZ'

    def send_message(self, clear_message=True, host_override=None, port_override=None):
        zpl = self.zpl
        log.debug('Sending message: %s' % zpl)

        # self.connect()
        self._send(zpl)
        # self.disconnect()

        if clear_message:
            self.current_message = []

    def get_message(self, clear_message=True):
        """
        This will return the current label in zpl format and (by default) clear the buffer
        """
        zpl = self.zpl

        if clear_message:
            self.current_message = []

        return zpl


class ZebraBitmap(object):
    """
    The image width in pixels MUST be a multiple of 32!
    """
    def __init__(self, filename, zebra_handle='IMAGE'):
        log.info('Loading Zebra Bitmap: %s' % filename)

        self.filename = filename
        self.zebra_handle = zebra_handle

        with open(filename, 'rb') as f:

            def read_int():
                return unpack('I', f.read(4))[0]

            def read_short():
                return unpack('H', f.read(2))[0]

            header = f.read(2)
            log.debug('Header: %s' % header)
            if header != b'BM':
                raise Exception('Unrecognized header: %s' % header)
            size = read_int()
            log.debug('Size: %s Bytes' % size)

            skip = read_short()
            log.debug('Skipping: %s' % skip)
            skip = read_short()
            log.debug('Skipping: %s' % skip)

            pixel_offset = read_int()
            log.debug('Pixel Data starts at %s' % pixel_offset)

            dib_header_size = read_int()
            log.debug('DIB Header Size: %s' % dib_header_size)
            if dib_header_size < 40:
                raise Exception('Only bitmaps with at least 40 byte headers are supported!')
            width = read_int()
            if width % 32 != 0:
                raise Exception('Width must be a multiple of 32')
            height = read_int()
            log.debug('Size: (%s x %s)' % (width, height))
            colour_planes = read_short()
            if colour_planes != 1:
                raise Exception('I don\'t know how to handle colour_planes=%s' % colour_planes)
            bpp = read_short()
            log.debug('%s BPP' % bpp)
            if bpp != 1:
                raise Exception('Only monochrome supported')

            compression_type = read_int()
            log.debug('Compression Type: %s' % compression_type)
            if compression_type != 0:
                raise Exception('Unsupported compression type: %s' % compression_type)

            image_size = read_int()
            log.debug('Image Size (inc padding): %s' % image_size)
            h_res = read_int()
            log.debug('Horizontal Resolution: %s' % h_res)
            v_res = read_int()
            log.debug('Vertical Resolution: %s' % v_res)
            num_colours = read_int()
            log.debug('Num Colours: %s' % num_colours)
            num_important_colours = read_int()
            log.debug('Num Important Colours: %s' % num_important_colours)

            # Skip to pixel data
            f.seek(pixel_offset)

            pixel_data = f.read((width * height) // 8)
            log.info('%s Bytes of pixel data read' % len(pixel_data))

        # ascii_data = binascii.hexlify(pixel_data).upper()
        # We need to flip the image and convert to ascii
        ascii_data = ''

        for row in range(height - 1, -1, -1):
            start = row * width // 8
            end = start + width // 8
            ascii_data = ascii_data + binascii.hexlify(pixel_data[start:end]).upper().decode('ascii')

            # row_data = pixel_data[start:end]
            # debug_out = ''
            # for i in row_data:
            #     o = ord(i)
            #
            #     debug_out += '#' if o & 128 else ' '
            #     debug_out += '#' if o & 64 else ' '
            #     debug_out += '#' if o & 32 else ' '
            #     debug_out += '#' if o & 16 else ' '
            #     debug_out += '#' if o & 8 else ' '
            #     debug_out += '#' if o & 4 else ' '
            #     debug_out += '#' if o & 2 else ' '
            #     debug_out += '#' if o & 1 else ' '
            # print debug_out

        # Upload a bitmap image
        self.upload_cmd = '~DGR:%s.GRF,%s,%s,%s' % (zebra_handle, width * height // 8, width // 8, ascii_data)

    def get_render_cmd(self):
        return ''

    def __repr__(self):
        return self.upload_cmd

