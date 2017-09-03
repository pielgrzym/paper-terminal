from __future__ import print_function, unicode_literals
import os, sys, tty, termios
import fcntl, pty
import time
import spidev as SPI
import EPD_driver
import datetime
import pyte
import subprocess


bus = 0
device = 0
xDot = 128
yDot = 296
DELAYTIME = 1.5

disp = EPD_driver.EPD_driver(spi=SPI.SpiDev(bus, device))

disp.Dis_Clear_full()

#disp.Dis_String(0, 10, "WELCOME EPD",16)
disp.Dis_Clear_part()

def getchr():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
	tty.setraw(sys.stdin.fileno())
	ch = sys.stdin.read(1)
    finally:
	termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def prep_input(input_string, tail=7):
    """
    Naive terminal emulation
    """
    output_list = []
    for line in input_string.split("\n"):
        if len(line) > 42:
            output_list.append(line[:42])
            output_list.append(line[42:])
        else:
            output_list.append(line)
    if output_list[-1] == '':
        output_list.pop(-1)
    return output_list[-tail:]


def display_input(input_string):
    """
    Naive terminal emulation wrapper
    """
    y_pos = 10
    for l in prep_input(input_string):
        disp.Dis_String(20, y_pos, l[:42], 12)
        y_pos += 16


def print_line(input_list):
    """
    Print list line-by-line
    """
    y_pos = 10
    for l in input_list:
        disp.Dis_String(20, y_pos, l[:42], 12)
        y_pos += 16

if __name__ == "__main__":

    def _make_non_blocking(fdescr):
        fdfl = fcntl.fcntl(fdescr, fcntl.F_GETFL)
        try:
            fcntl.fcntl(fdescr, fcntl.F_SETFL, fdfl | os.O_NDELAY)
        except AttributeError:
            fcntl.fcntl(fdescr, fcntl.F_SETFL, fdfl | os.FNDELAY)

    def prepare():
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

    master, slave = pty.openpty()
    master = os.fdopen(master, 'rb+wb', 0) # open file in an unbuffered mode
    _make_non_blocking(master)

    prog = subprocess.Popen(shell=False, args=['/bin/bash', '-i'], stdin=slave,
            stdout=slave, stderr=subprocess.STDOUT, preexec_fn=prepare,
            env=dict(TERM="linux", COLUMNS="42", LINES="7"))

    master.write("\n")
    master.write("tail -f /var/log/syslog\n")
    #master.write("ls\n")
    #master.write("top\n")


    screen = pyte.Screen(42, 7)
    stream = pyte.Stream(screen)

    time.sleep(1)
    while True:
        try:
            output = master.read()
            stream.feed(output)
            print_line(screen.display)
        except Exception, e:
            print(str(e))
        time.sleep(1.5)
