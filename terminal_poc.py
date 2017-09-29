#!/usr/bin/env python
from __future__ import print_function, unicode_literals
# import signal
import pam
from getpass import getpass
from paperterm import *
import logging

logging.basicConfig(
    filename="debug.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(module)sf:%(funcName)s: %(message)s"
    )

logging.info("--------[ INIT ]--------")

# def signal_handler(signal, frame):
#     PaperTerminal.KILLALL = True
#     sys.exit(0)
TERM_WIDTH=49
TERM_HEIGHT=8

def getchr():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

if __name__ == "__main__":

    # signal.signal(signal.SIGINT, signal_handler)

    display_q = Queue.Queue()
    display_thread = DisplayThread(TERM_WIDTH, TERM_HEIGHT, display_q)
    display_thread.start()
    shell_thread = None

    # with open("/etc/issue", 'r') as msg:
    #     display_q.put(msg.read().decode('string_escape'))
    display_q.put("Paper Terminal v0.1 login\n\r")

    while True:
        display_q.put("Login: ")
        print("Login: ")
        username = ""
        while True:
            c = getchr()
            display_q.put(c)
            if c == "\r":
                display_q.put("\n\r")
                break
            else:
                username += c
        display_q.put("Password:\n\r")
        # print("Password: ")
        # password = raw_input() # TODO: rnd how to prevent getpass delay
        password = getpass("Password: ")
        if pam.authenticate(username, password):
            shell_thread = ShellThread(TERM_WIDTH, TERM_HEIGHT, username, display_q)
            shell_thread.start()
            break
        else:
            display_q.put("Wrong user/pass\n\r")

    while shell_thread.is_alive():
        r = getchr()
        shell_thread.write(r)

    display_thread.join()
