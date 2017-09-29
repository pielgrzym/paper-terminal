#!/usr/bin/env python
from __future__ import print_function, unicode_literals
# import signal
import pam
from getpass import getpass
from paperterm import *
from logging.handlers import SysLogHandler, FileHandler
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--no-loadkeys", help="Disable loadkeys being ran prior to shell", action="store_true")
parser.add_argument("--loadkeys-config", help="Config file for key remapping", default='/home/pi/keys')
parser.add_argument("--term-width", help="Width of the terminal", default=49, type=int)
parser.add_argument("--term-height", help="Height of the terminal", default=8, type=int)
parser.add_argument("--log-file", help="Location of logfile", default="debug.log")
parser.add_argument("--use-syslog", help="Use syslog for logging", action="store_true")

args = parser.parse_args()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(module)sf:%(funcName)s: %(message)s"
    )

logger = logging.getLogger()

if args.use_syslog:
    logger.addHandler(SysLogHandler('/dev/log'))
else:
    logger.addhandler(FileHandler(args.log_file))

logging.info("--------[ INIT ]--------")

# def signal_handler(signal, frame):
#     PaperTerminal.KILLALL = True
#     sys.exit(0)
TERM_WIDTH=args.term_width
TERM_HEIGHT=args.term_height

def getchr():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main_main():
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

if __name__ == "__main__":
    import logging
    if not args.no_loadkeys:
        try:
            import subprocess
            subprocess.call(['loadkeys', args.loadkeys_config])
        except Exception as e:
            logging.exception("loadkeys error")
    try:
        main_main()
    except Exception as e:
        logging.exception("message")

    # signal.signal(signal.SIGINT, signal_handler)

