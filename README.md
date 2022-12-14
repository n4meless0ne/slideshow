# slideshow
Slide show tool for artists

This tool helps artists to practice gesture drawings using images on their local hard drive.

1. Requirements

- Python 3.x: See https://www.python.org/getit/
- tkinter: See https://tkdocs.com/tutorial/install.html
- Pillow: See https://pillow.readthedocs.io/en/stable/installation.html or just type "pip install Pillow" in command line
- pip install screeninfo
- pip install pywin32

2. Usage and arguments

```
usage: slideshow.py [-h] [-path path [path ...]] [-zip-path zip_path]
                    [-zip-file zip_file [zip_file ...]] [-timeout TIMEOUT]
                    [-width WIDTH] [-height HEIGHT]

Rotate images from directory in given timeout.

optional arguments:
  -h, --help            show this help message and exit
  -path path [path ...]
                        paths to the images directory (current directory by
                        default). You can specify many directories
  -zip-path zip_path    path to the directory with zip files contains images
  -zip-file zip_file [zip_file ...]
                        zip files with images. You can specify many files.
  -timeout TIMEOUT      timeout in seconds (60 by default)
  -width WIDTH          window width in pixels (600 by default)
  -height HEIGHT        window height in pixels (800 by default)
  ```

Example: 
```
python slideshow.py -path C:\Images -timeout 120
```
