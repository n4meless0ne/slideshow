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
                    [-zip-path-random zip_path_random]
                    [-zip-file zip_file [zip_file ...]] [-timeout TIMEOUT]
                    [-width WIDTH] [-height HEIGHT]

Rotate images from directory in given timeout.

options:
  -h, --help            show this help message and exit
  -path path [path ...]
                        Paths to the images directory (current directory by
                        default). You can specify many directories
  -zip-path zip_path    Path to the directory with zip files contains images.
                        The one random zip file selected, then all it images
                        will be shown in random order
  -zip-path-random zip_path_random
                        Path to the directory with zip files contains images.
                        All zip files selected, then all images from all these
                        files will be shown in random order
  -zip-file zip_file [zip_file ...]
                        Zip files with images. You can specify many files.
  -timeout TIMEOUT      Timeout in seconds (60 by default)
  -width WIDTH          Window width in pixels (600 by default)
  -height HEIGHT        Window height in pixels (800 by default)

```

Example: 
```
python slideshow.py -path C:\Images -timeout 120
```
