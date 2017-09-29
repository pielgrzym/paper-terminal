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

    def authenticate(self):
        if pam.authenticate(self.username, self.password):
            logging.debug("Auth success for user: %s" % self.username)
            self.password = None # such security! :D
            self.authenticated = True
        else:
            logging.debug("Auth FAIL for user: %s" % self.username)
            self.authenticated = False
            self.display_q.put("Wrong user/pass\n\r")

    def get_username(self):
         self.username = ""
         ignore_counter = 0
         while True:
             c = self.getchr()
             logging.debug("[Login screen] Typed char: %s (ord: %d)" % (c, ord(c)))
             if ignore_counter > 0:
                 ignore_counter -= 1
                 continue
             if c == "\r":
                 self.display_q.put("\n\r")
                 break
             elif ord(c) == 127: # backspace, delete one char
                 self.username = self.username[:-1]
                 # yes, to erase a char in terminal, one needs to do a
                 # backspace a space and a backspace...
                 c = "\b \b"
             elif ord(c) == 27: # arrows produce 3 chars, so we need to skip 3 inputs total
                 ignore_counter = 2
                 continue
             else:
                 self.username += c
             self.display_q.put(c)

    def get_password(self):
        self.password = getpass("Password: ")

    def run(self):
        while True:
            self.display_q.put("Login: ")
            print("Login: ")
            self.get_username()
            self.display_q.put("Password:\n\r")
            self.get_password()
            self.authenticate()
            if self.authenticated:
                break
