# Paper terminal

This small python util allows to spawn a terminal emulator displayed on RaspberryPi with Waveshare E-paper 2.9 inch display.

![Paper term photo](/screenshot1.png?raw=true "Paper term in action")

![Paper term photo](/screenshot2.png?raw=true "Now with cursor support!")

## Installation

* requires EPD driver from Waveshare's examples to work
* needs to run as root and have packages from `requirements.txt` installed via pip

## Usage

```
usage: paperterm.py [-h] [--no-loadkeys] [--loadkeys-config LOADKEYS_CONFIG]
                    [--term-width TERM_WIDTH] [--term-height TERM_HEIGHT]
                    [--log-file LOG_FILE] [--use-syslog]

optional arguments:
  -h, --help            show this help message and exit
  --no-loadkeys         Disable loadkeys being ran prior to shell
  --loadkeys-config LOADKEYS_CONFIG
                        Config file for key remapping
  --term-width TERM_WIDTH
                        Width of the terminal
  --term-height TERM_HEIGHT
                        Height of the terminal
  --log-file LOG_FILE   Location of logfile
  --use-syslog          Use syslog for logging
```

## Replacing tty

To run this terminal instead of `tty` you will need a following file in Raspbian:

`/etc/systemd/system/getty@tty1.service.d/override.conf`

```
[Service]
ExecStart=
ExecStart=-/path/to/paperterm.py --use-syslog
StandardInput=tty
StandardOutput=tty
User=root
```

Note the `-` before the path.
