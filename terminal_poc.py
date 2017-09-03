from __future__ import print_function, unicode_literals
import os, sys, tty, termios
import fcntl, pty
import time
import spidev as SPI
import EPD_driver
import datetime
import pyte
import subprocess

def prepare_subprocess():
    """
    taken from: https://stackoverflow.com/questions/12146230/
        how-to-run-a-shell-in-a-separate-process-and-get-auto-completions-python
    """
    os.setsid() # start a new detached session
    tty.setcbreak(sys.stdin) # set standard input to cbreak mode
    old = termios.tcgetattr(sys.stdin)
    old[0] |= termios.BRKINT # transforms break to SIGINT
    old[3] &= termios.ICANON # non-canonical mode
    old[3] |= termios.ECHO | termios.ISIG # set echo and signal characters handling
    cc = old[6]
    # make input unbuffered
    cc[termios.VMIN] = 1
    cc[termios.VTIME] = 0
    termios.tcsetattr(sys.stdin, termios.TCSANOW, old)


class PaperTerminal(object):
    def __init__(self, size_x, size_y):
        self.bus = 0
        self.device = 0
        self.xDot = 128
        self.yDot = 296
        self.DELAYTIME = 1.5
        self.size_x = size_x
        self.size_y = size_y

        self.disp = EPD_driver.EPD_driver(spi=SPI.SpiDev(self.bus, self.device))
        self.disp.Dis_Clear_full()
        self.disp.Dis_Clear_part()

        self.screen = pyte.Screen(self.size_x, self.size_y)
        self.stream = pyte.Stream(self.screen)

        self._start_shell()

    def getchr(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def print_lines(self, input_list):
        """
        Print list line-by-line
        """
        y_pos = 10
        for l in input_list:
            self.disp.Dis_String(20, y_pos, l[:42], 12)
            y_pos += 16

    def _make_non_blocking(self, fdescr):
        fdfl = fcntl.fcntl(fdescr, fcntl.F_GETFL)
        try:
            fcntl.fcntl(fdescr, fcntl.F_SETFL, fdfl | os.O_NDELAY)
        except AttributeError:
            fcntl.fcntl(fdescr, fcntl.F_SETFL, fdfl | os.FNDELAY)

    def _start_shell(self):
        """
        Start subprocess with a shell and nonblocking io for communication
        taken from:
        https://stackoverflow.com/questions/12146230/
        how-to-run-a-shell-in-a-separate-process-and-get-auto-completions-python
        """
        self.slave_io, self.slave = pty.openpty()
        self.slave_io = os.fdopen(self.slave_io, 'rb+wb', 0) # open file in an unbuffered mode
        self._make_non_blocking(self.slave_io)

        self.slave_process = subprocess.Popen(shell=False, args=['/bin/bash', '-i'], stdin=self.slave,
                stdout=self.slave, stderr=subprocess.STDOUT, preexec_fn=prepare_subprocess,
                env=dict(TERM="linux", COLUMNS=str(self.size_x), LINES=str(self.size_y)))

    def refresh_screen(self):
        """
        Read from subprocess and display content to screen
        """
        output = self.slave_io.read()
        self.stream.feed(output)
        self.print_lines(self.screen.display)

    def write(self, input_string):
        self.slave_io.write(input_string)


if __name__ == "__main__":

    paper_term = PaperTerminal(42, 7)
    paper_term.write("tail -f /var/log/syslog\n")
    #master.write("ls\n")
    #slave_io.write("top\n")

    time.sleep(1)
    while True:
        try:
            paper_term.refresh_screen()
        except Exception, e:
            print(str(e))
        time.sleep(1.5)
