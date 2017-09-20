from __future__ import print_function, unicode_literals
import threading, Queue
# import spidev as SPI
# import EPD_driver
import epd2in9
import Image, ImageDraw, ImageFont
import pyte
import time

class DisplayThread(threading.Thread):
    def __init__(self, size_x, size_y, display_q):
        super(DisplayThread, self).__init__()
        self.display_q = display_q
        self.bus = 0
        self.device = 0
        self.xDot = 128
        self.yDot = 296
        self.DELAYTIME = 1.5
        self.size_x = size_x
        self.size_y = size_y

        self.stoprequest = threading.Event()

        self.epd = epd2in9.EPD()
        self.image = Image.new('1', (epd2in9.EPD_HEIGHT, epd2in9.EPD_WIDTH), 255)
        self.font = ImageFont.truetype('djavu.ttf', 10)
        self.draw = ImageDraw(self.image)
        self.epd.clear_frame_memory(0xFF)
        self.epd.display_frame()
        # self.disp.Dis_Clear_full()
        # self.disp.Dis_Clear_part()

        self.screen = pyte.Screen(self.size_x, self.size_y)
        self.stream = pyte.Stream(self.screen)

        # self.screen_loop()

    def redraw_image(self):
        self.epd.set_frame_memory(image.rotate(90, expand=1), 0, 0)
        self.epd.display_frame()

    def print_lines(self, input_list):
        """
        Print list line-by-line
        """
        y_pos = 10
        self.image = Image.new('1', (epd2in9.EPD_HEIGHT, epd2in9.EPD_WIDTH), 255)
        self.draw = ImageDraw(self.image)
        self.draw.multiline_text((0, 0), "\n".join(input_list))
        self.redraw_image()
        # for l in input_list:
        #     self.draw.text((0, y_pos), l[:42], font=font, fill=0)
            # self.disp.Dis_String(20, y_pos, l[:42], 12)
            # y_pos += 16

    def refresh_screen(self):
        """
        Read from queue and display content to screen
        """
        try:
            while True:
                output = self.display_q.get(False)
                self.stream.feed(output)
        except Queue.Empty:
            self.print_lines(self.screen.display)

    def run(self):
        while not self.stoprequest.isSet():
            try:
                self.refresh_screen()
            except Exception, e:
                #print(str(e))
                pass
            time.sleep(0.8) # omg, some callback or shit?
        self.disp.Dis_Clear_full()

    def echo(self, output):
        self.stream.feed(output)
        self.print_lines(self.screen.display)

    def join(self, timeout=None):
        self.stoprequest.set()
        super(DisplayThread, self).join(timeout)
