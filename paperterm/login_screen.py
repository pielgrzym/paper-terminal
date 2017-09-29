from getpass import getpass
import os, sys, tty, termios
import fcntl, pty
import logging
import pam

class LoginScreen(object):
    def __init__(self, display_q):
        self.display_q = display_q
        self.display_q.put("Paper Terminal v0.1 login\n\r")
        logging.debug("Started login screen")

    def getchr(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def run(self):
        while True:
            self.display_q.put("Login: ")
            print("Login: ")
            self.username = ""
            while True:
                c = self.getchr()
                logging.debug("[Login screen] Typed char: %s (ord: %d)", % c, ord(c))
                if c == "\r":
                    self.display_q.put("\n\r")
                    break
                elif ord(c) == 8: # backspace, delete one char
                    self.username = self.username[:-1]
                elif ord(c) in [13, 37, 38, 39, 40]: # delete or arrows
                    continue
                else:
                    self.username += c
                self.display_q.put(c)
            self.display_q.put("Password:\n\r")
            self.password = getpass("Password: ")
            if pam.authenticate(self.username, self.password):
                logging.debug("Auth success for user: %s" % self.username)
                self.password = None # such security! :D
                self.authenticated = True
                break
            else:
                logging.debug("Auth FAIL for user: %s" % self.username)
                self.authenticated = False
                self.display_q.put("Wrong user/pass\n\r")
