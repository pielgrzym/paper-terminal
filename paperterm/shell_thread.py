from __future__ import print_function, unicode_literals
import threading, Queue
import time
import pwd
import os, sys, tty, termios
import fcntl, pty
import subprocess
import ptyprocess

def prepare_subprocess(gid, uid):
    """
    taken from: https://stackoverflow.com/questions/12146230/
        how-to-run-a-shell-in-a-separate-process-and-get-auto-completions-python
    """
    os.setgid(gid)
    os.setuid(uid)
    try:
        os.setsid() # start a new detached session
    except:
        print("Warning setsid() failed")
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


class ShellThread(threading.Thread):
    def __init__(self, size_x, size_y, user, display_q):
        super(ShellThread, self).__init__()
        self.display_q = display_q
        self.user = user
        self.size_x = size_x
        self.size_y = size_y

    def _make_non_blocking(self, fdescr):
        fdfl = fcntl.fcntl(fdescr, fcntl.F_GETFL)
        try:
            fcntl.fcntl(fdescr, fcntl.F_SETFL, fdfl | os.O_NDELAY)
        except AttributeError:
            fcntl.fcntl(fdescr, fcntl.F_SETFL, fdfl | os.FNDELAY)

    def start_shell(self):
        """
        Use excellent ptyprocess package to run a pty with a shell
        and denot the process to a chosen user.
        """
        self.slave_io, self.slave = pty.openpty()
        self.slave_io = os.fdopen(self.slave_io, 'rb+wb', 0) # open file in an unbuffered mode
        self._make_non_blocking(self.slave_io)
        pw_record = pwd.getpwnam(self.user)
        uid = pw_record.pw_uid
        gid = pw_record.pw_gid

        self.slave_process = ptyprocess.PtyProcessUnicode.spawn(['/bin/bash','-i'],
                preexec_fn=prepare_subprocess(uid, gid),
                dimensions=(self.size_y, self.size_x),
                env=dict(TERM="linux",
                    HOME=pw_record.pw_dir,
                    LOGNAME=pw_record.pw_name,
                    PWD=pw_record.pw_dir,
                    USER=pw_record.pw_name
                    ))

    def start_shell_subprocess(self):
        """
        Start subprocess with a shell and nonblocking io for communication
        taken from:
        https://stackoverflow.com/questions/12146230/
        how-to-run-a-shell-in-a-separate-process-and-get-auto-completions-python
        """
        self.slave_io, self.slave = pty.openpty()
        self.slave_io = os.fdopen(self.slave_io, 'rb+wb', 0) # open file in an unbuffered mode
        self._make_non_blocking(self.slave_io)
        pw_record = pwd.getpwnam(self.user)
        uid = pw_record.pw_uid
        gid = pw_record.pw_gid

        self.slave_process = subprocess.Popen(shell=False, args=['/bin/bash', '-i'], stdin=self.slave,
                stdout=self.slave, stderr=subprocess.STDOUT, preexec_fn=prepare_subprocess(uid, gid),
                env=dict(TERM="linux",
                    COLUMNS=str(self.size_x),
                    LINES=str(self.size_y),
                    HOME=pw_record.pw_dir,
                    LOGNAME=pw_record.pw_name,
                    PWD=pw_record.pw_dir,
                    USER=pw_record.pw_name
                    ))

    def run(self):
        self.start_shell()
        while self.slave_process.isalive():
        # while self.slave_process.poll() is None:
            try:
                output = self.slave_process.read()
                # output = self.slave_io.read()
                self.display_q.put(output)
            except Exception, e:
                # print(str(e))
                pass # haha, I'll pass ]:->
            # time.sleep(0.8)

    def write(self, input_string):
        try:
            self.slave_process.write(input_string)
        except:
            # some bad shit waiting to blow up here. NAH, it's gonna be fine ]:->
            pass
