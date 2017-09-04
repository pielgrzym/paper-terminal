#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import os, sys, tty, termios
import fcntl, pty
import time
import spidev as SPI
import EPD_driver
import datetime
import pyte
import subprocess
import threading
import signal
import pam
import pwd
from getpass import getpass

def prepare_subprocess(username):
    """
    taken from: https://stackoverflow.com/questions/12146230/
        how-to-run-a-shell-in-a-separate-process-and-get-auto-completions-python
    """
    pw_record = pwd.getpwnam(username)
    os.setgid(pw_record.pw_gid)
    os.setuid(pw_record.pw_uid)
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
    KILLALL = False
    def __init__(self, size_x, size_y):
        self.user = None

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
                stdout=self.slave, stderr=subprocess.STDOUT, preexec_fn=prepare_subprocess(self.user),
                env=dict(TERM="linux", COLUMNS=str(self.size_x), LINES=str(self.size_y)))

    def refresh_screen(self):
        """
        Read from subprocess and display content to screen
        """
        output = self.slave_io.read()
        self.stream.feed(output)
        self.print_lines(self.screen.display)

    def screen_loop(self):
        while True:
            if self.KILLALL == True:
                break
                sys.exit(0)
            try:
                self.refresh_screen()
            except Exception, e:
                #print(str(e))
                pass
            #time.sleep(self.DELAYTIME)

    def start_screen_loop(self):
        self._start_shell()
        self.screen_loop_thread = threading.Thread(target=self.screen_loop)
        self.screen_loop_thread.start()

    def stop_screen_loop(self):
        self.KILLALL = True

    def write(self, input_string):
        self.slave_io.write(input_string)

def signal_handler(signal, frame):
    PaperTerminal.KILLALL = True
    sys.exit(0)

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    paper_term = PaperTerminal(42, 7)
    while True:
        paper_term.stream.feed("Username:")
        paper_term.print_lines(paper_term.screen.display)
        username = raw_input()
        paper_term.stream.feed("Password:")
        paper_term.print_lines(paper_term.screen.display)
        password = getpass()
        if pam.authenticate(username, password):
            paper_term.user = username
            break
        else:
            paper_term.stream.feed("Wrong user/pass")
            paper_term.print_lines(paper_term.screen.display)

    if paper_term.user is None:
        sys.exit(1)

    paper_term.start_screen_loop()
    while True:
        r = paper_term.getchr()
        if paper_term.KILLALL == True:
            break
        paper_term.write(r)

    paper_term.stop_screen_loop()
