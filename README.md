# Paper terminal

This small python util allows to spawn a terminal emulator displayed on RaspberryPi with Waveshare E-paper 2.9 inch display.

![Paper term photo](/paper_terminal.png?raw=true "Paper term in action")

## Installation

* requires EPD driver from Waveshare's examples to work
* needs to run as root and have packages from `requirements.txt` installed via pip

## Replacing tty

To run this terminal instead of `tty` you will need a following file in Raspbian:

`/etc/systemd/system/getty@tty1.service.d/override.conf`

```
[Service]
ExecStart=
ExecStart=-/path/to/terminal_poc.py
StandardInput=tty
StandardOutput=tty
User=root
```

Note the `-` before the path.
