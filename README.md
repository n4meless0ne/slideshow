# slideshow
Slide show tool for artists

This tool helps artists to practice gesture drawings using images on their local hard drive.

1. Requirements

- Python 3.x: See https://www.python.org/getit/
- tkinter: See https://tkdocs.com/tutorial/install.html
- Pillow: just type "pip install Pillow" in command line

2. Usage and arguments

```
python slideshow.py [-h] [-path path] [-timeout TIMEOUT] [-width WIDTH]
                    [-height HEIGHT]

Rotate images from directory in given timeout

optional arguments:
  -h, --help        show this help message and exit
  -path path        path to the images directory (current directory by
                    default)
  -timeout TIMEOUT  timeout in seconds (60 by default)
  -width WIDTH      window width in pixels (600 by default)
  -height HEIGHT    window height in pixels (800 by default)
  ```

Example: 
```
python slideshow.py -path C:\Images -timeout 120
```
