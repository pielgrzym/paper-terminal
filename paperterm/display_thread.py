from __future__ import print_function, unicode_literals
import threading, Queue
# import spidev as SPI
# import EPD_driver
import epd2in9
import Image, ImageDraw, ImageFont
import pyte
import time
import logging

class DisplayThread(threading.Thread):
    def __init__(self, size_x, size_y, display_q):
        super(DisplayThread, self).__init__()
        self.display_q = display_q
        self.bus = 0
        self.device = 0
        self.x_max = 128
        self.y_max = 296
        self.size_x = size_x
        self.size_y = size_y

        self.stoprequest = threading.Event()

        self.epd = epd2in9.EPD()
        self.epd.init(self.epd.lut_full_update)
        self.image = Image.new('1', (epd2in9.EPD_HEIGHT, epd2in9.EPD_WIDTH), 255)
        self.font = ImageFont.load('terminus_12.pil')
        self.line_height = 16
        #self.font = ImageFont.truetype('terminus.ttf', 12)
        self.draw = ImageDraw.Draw(self.image)
        self.clear_display()
        self.epd.init(self.epd.lut_partial_update)

        self.screen = pyte.Screen(self.size_x, self.size_y)
        self.stream = pyte.Stream(self.screen)
        self.buffer = []

    def clear_display(self):
        self.epd.clear_frame_memory(0xFF)
        self.epd.display_frame()

    def redraw_image_part(self, old_r, new_r):

        logging.debug("Redrawing image part ...")

        old = old_r.copy()
        old = old.rotate(90, expand=1)
        new = new_r.copy()
        new = new.rotate(90, expand=1)

        i_old = old.load()
        i_new = new.load()

        (width, height) = new.size

        min_x = width
        min_y = height
        max_x = 0
        max_y = 0

        logging.debug("Size: %d:%d", width, height)

        for y in range(0, height):
            for x in range(0, width):
                if i_old[x,y] != i_new[x,y]:
                    if x < min_x: min_x = x
                    if x > max_x: max_x = x
                    if y < min_y: min_y = y
                    if y > max_y: max_y = y

        logging.debug("Size: MIN_X=%d MAX_X=%d MIN_Y=%d MAX_Y=%d",
                      min_x, max_x, min_y, max_y)

        part = new.crop((min_x, min_y, max_x, max_y))

        return (part, min_x, min_y)

    def redraw_image(self):
        self.epd.set_frame_memory(self.image.rotate(90, expand=1), 0, 0)
        self.epd.display_frame()
        self.epd.set_frame_memory(self.image.rotate(90, expand=1), 0, 0)
        self.epd.display_frame()

    def check_single_line_modified(self, input_list):
        new_lines = set(input_list) - set(self.buffer)
        if len(new_lines) == 1:
            return input_list.index(new_lines.pop())
        else:
            return False

    def check_prompt(self, line):
        if 'pi@raspberrypi:' in line:
            return True
        else:
            return False

    def print_lines(self, input_list):
        """
        Print list line-by-line
        """
        image_old = self.image.copy()
        self.image = Image.new('1', (epd2in9.EPD_HEIGHT, epd2in9.EPD_WIDTH), 255)
        self.draw = ImageDraw.Draw(self.image)
        self.draw.multiline_text((0, 0), "\n".join(input_list), font=self.font)
        logging.debug("To be redrawed ...")
        try:
            (image_part, x, y) = self.redraw_image_part(image_old, self.image)
            self.epd.set_frame_memory(image_part, x, y)
            self.epd.display_frame()
            self.epd.set_frame_memory(image_part, x, y)
            self.epd.display_frame()
        except Exception:
            logging.exception("Exception in partial redraw")

        self.buffer = input_list

    def refresh_screen(self):
        """
        Read from queue and display content to screen
        """
        new_data = False
        try:
            while True:
                output = self.display_q.get(False)
                new_data = True
                self.stream.feed(output)
        except Queue.Empty:
            if new_data:
                self.print_lines(self.screen.display)

    def run(self):
        while not self.stoprequest.isSet():
            try:
                self.refresh_screen()
            except Exception, e:
                #print(str(e))
                pass
            time.sleep(0.05) # omg, some callback or shit?
        self.clear_display()

    def echo(self, output):
        self.stream.feed(output)
        self.print_lines(self.screen.display)

    def join(self, timeout=None):
        self.stoprequest.set()
        super(DisplayThread, self).join(timeout)
