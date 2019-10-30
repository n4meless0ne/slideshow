import sys
import argparse
import random
import tempfile
import shutil

import tkinter as tk
import PIL.Image, PIL.ImageTk

from os import walk, mkdir
from os.path import join, exists

from zipfile import ZipFile

def isImageSupported(file_name):
    # supported extensions
    img_ext = ['.jpg', '.png', '.bmp']

    if any(x in str.lower(file_name) for x in img_ext):
        return True

    return False


def findAllSupportedFiles(path):
    files_list = []

    for dirpath, dirs, files in walk(path):
        for name in files:
            if isImageSupported(name):
                files_list.append(join(dirpath, name))

    return files_list

# some statistics
total_image_shown = 0
total_time_spent = 0

# command line arguments
parser = argparse.ArgumentParser(description='Rotate images from directory in given timeout')

parser.add_argument('-path', metavar='path', default='',
                    help='path to the images directory (current directory by default)')

parser.add_argument('-zip-path', metavar='zip_path', default='',
                    help='path to the directory with zip files contains images')

parser.add_argument('-timeout', dest='timeout', type=int, default=60,
                    help='timeout in seconds (60 by default)')

parser.add_argument('-width', dest='width', type=int, default=600,
                    help='window width in pixels (600 by default)')

parser.add_argument('-height', dest='height', type=int, default=800,
                    help='window height in pixels (800 by default)')

args = parser.parse_args()
print(args)

# timeout in seconds
max_timer_value = args.timeout
cur_timer = max_timer_value
timer_paused = False

default_image_width = args.width
default_image_height = args.height

w_width = 0
w_height = 0

img_list = []
cur_img_index = 0
cur_photo = 0

zip_extract_temp_path = ''

if args.zip_path:

    zip_files_list = []

    # if zip-path defined - use it to find archives
    for dirpath, dirs, files in walk(args.zip_path):
        for name in files:
            if any(x in str.lower(name) for x in ['.zip']):
                zip_files_list.append(join(dirpath, name))

    # now peek one random archive file
    zip_file = random.choice(zip_files_list)

    # extract the zip file to temp directory
    if zip_file:
        with ZipFile(zip_file, 'r') as zipObj:
            zip_extract_temp_path = join(tempfile.gettempdir(), '_slideshow_ref')

            if exists(zip_extract_temp_path):
                shutil.rmtree(zip_extract_temp_path)

            zipObj.extractall(zip_extract_temp_path)
            img_list = findAllSupportedFiles(zip_extract_temp_path)

else:
    # if use path ot . to find all supported images
    img_list = findAllSupportedFiles(args.path if args.path else '.')

if len(img_list) == 0:
    print('No supported images found')
    sys.exit(-1)

# shuffle images
random.shuffle(img_list)


def updateTimeLabel():
    global timer_paused
    global cur_timer

    if not timer_paused:
        cur_timer -= 1
        if cur_timer < 0:
            nextImage(1);

    textTime = '{:02d}:{:02d}'.format(int(cur_timer / 60), int(cur_timer % 60))
    window.title('Slide show ({})'.format(textTime))

    window.after(1000, updateTimeLabel)


def nextImage(direction):
    global cur_img_index, task_id, canvas, canvas_img, cur_timer, cur_photo
    global total_image_shown, total_time_spent

    total_time_spent += (max_timer_value - cur_timer)

    print('Took {} seconds. '.format(max_timer_value - cur_timer))

    cur_timer = max_timer_value
    cur_img_index += direction

    if cur_img_index == len(img_list):
        cur_img_index = 0
    elif cur_img_index < 0:
        cur_img_index = len(img_list) - 1

    cur_photo = loadImage(img_list[cur_img_index])

    canvas.width = w_width
    canvas.height = w_height

    canvas.itemconfig(canvas_img, image = cur_photo)


def pauseImage():
    global timer_paused

    if timer_paused:
        timer_paused = False
        print('Unpaused ... ')
    else:
        timer_paused = True
        print('Paused ... ')


def loadImage(img_file_path):

    global w_width, w_height, total_image_shown

    # Window default size
    w_width = default_image_width
    w_height = default_image_height

    # Load an image
    pil_img = PIL.Image.open(img_file_path)

    # Get the image dimensions
    width, height = pil_img.size

    # make window well scaled and not greater when original dimensions
    img_ratio = width / height
    wnd_def_ratio = w_width / w_height

    if img_ratio > wnd_def_ratio:
        w_height = int(w_width / img_ratio)
    else:
        w_width = int(w_height * img_ratio)

    # get screen width and height
    ws = window.winfo_screenwidth() # width of the screen
    hs = window.winfo_screenheight() # height of the screen

    # calculate x and y coordinates for the Tk root window
    button_height = 26

    x = ws - w_width - ws/64
    y = hs/32 + button_height

    if y > (hs-w_height):
        y = 0

    # set the dimensions of the screen
    # and where it is placed
    # if we don't see right side - slighly move window to the left
    if window.winfo_x() > x:
        window.geometry('%dx%d+%d+%d' % (w_width, w_height + button_height, x, y))
    else:
        window.geometry('%dx%d' % (w_width, w_height + button_height))

    pil_img = pil_img.resize((w_width, w_height), resample=PIL.Image.LANCZOS)

    print('{}, w={}, h={}'.format(img_file_path, w_width, w_height))

    total_image_shown += 1

    # Use PIL (Pillow) to convert to a PhotoImage
    return PIL.ImageTk.PhotoImage(pil_img)

# Create a window
window = tk.Tk()
window.title('Slide show')

# Prev button
tk.Button(window, text='Prev image', width=5, command=lambda: nextImage(-1)).grid(row = 0, column=0, sticky=tk.N+tk.E+tk.S+tk.W)

# Pause button
tk.Button(window, text='Pause', width=5, command=lambda: pauseImage()).grid(row = 0, column=1, sticky=tk.N+tk.E+tk.S+tk.W)

# Next button
tk.Button(window, text='Next image', width=5, command=lambda: nextImage(1)).grid(row = 0, column=2, sticky=tk.N+tk.E+tk.S+tk.W)

# Load image
cur_photo = loadImage(img_list[cur_img_index])

# Create a canvas that can fit the above image
canvas = tk.Canvas(window, width = default_image_width, height = default_image_height)
canvas.grid(row = 1, columnspan=3)

# Add a PhotoImage to the Canvas
canvas_img = canvas.create_image(0, 0, image=cur_photo, anchor=tk.NW)

# Callback to update timer and change image
window.after(1000, updateTimeLabel)

# Run the window loop
window.mainloop()

if zip_extract_temp_path and exists(zip_extract_temp_path):
    shutil.rmtree(zip_extract_temp_path)

# Some statistics
total_time_spent += (max_timer_value - cur_timer)
print('{} images were drawn in {} seconds (average {:.2f} seconds per image)'.format(
    total_image_shown, total_time_spent, total_time_spent / total_image_shown))
