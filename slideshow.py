import argparse
import random
import sys
import tempfile
import tkinter as tk
import PIL.Image
import PIL.ImageTk
import PIL.ImageOps
import screeninfo
import win32clipboard

from os import walk
from os.path import join, exists
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path

image_extensions = ['.jpg', '.png', '.bmp']
zip_extensions = ['.zip']

# some statistics
total_image_shown = 0
total_time_spent = 0

cur_window_width = 0
cur_window_height = 0

count_buttons = 6


def is_file_valid(file_name, extensions):
    return any(x in str.lower(file_name) for x in extensions)


def findAllSupportedFiles(path_list, extensions):
    files_list = []

    for path in path_list:
        if not path or not exists(path):
            continue

        for dirpath, dirs, files in walk(path):
            for name in files:
                if is_file_valid(name, extensions):
                    files_list.append(join(dirpath, name))

    return files_list


def findAllSupportedZipFiles(zip_file_list):
    temp_path_names = []
    for zip_file in zip_file_list:
        if not zip_file or not exists(zip_file):
            print('File {} not found'.format(zip_file))

        with ZipFile(zip_file, 'r') as zipObj:
            # create temp directory
            temp_path = tempfile.TemporaryDirectory()

            # extract files into temp directory
            zipObj.extractall(temp_path.name)

            # save temp path object in global list
            zip_extract_temp_paths.append(temp_path)

            # save path to temp directory in list
            temp_path_names.append(temp_path.name)

    return findAllSupportedFiles(temp_path_names, image_extensions)


def send_to_clipboard(clip_type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()


def saveToClipboard(file_path):
    image = PIL.Image.open(file_path)

    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    send_to_clipboard(win32clipboard.CF_DIB, data)


def updateTimeLabel():
    global timer_paused
    global cur_timer
    global timeImgLabel

    if not timer_paused:
        cur_timer -= 1
        if cur_timer < 0:
            nextImage(1)

    textTime = '{:02d}:{:02d}'.format(int(cur_timer / 60), int(cur_timer % 60))
    window.title('Slide show ({})'.format(textTime))

    timeImgLabel.config(text=textTime)

    # when run out of time - make timer red
    if cur_timer <= 5:
        timeImgLabel.config(foreground='red')

    window.after(1000, updateTimeLabel)


def pauseImage():
    global timer_paused

    if timer_paused:
        timer_paused = False
        pauseButton.config(text='Pause')
        print('Unpaused ... ')
    else:
        timer_paused = True
        pauseButton.config(text='Unpause')
        print('Paused ... ')


def getIndexOfNextImageInSameFolder():
    global cur_img_index
    cur_dir = Path(img_list[cur_img_index])

    # search from current index till the end of list
    for i in range(cur_img_index + 1, len(img_list)):
        if Path(img_list[i]).parent == cur_dir.parent:
            return i

    # search from begin of list till current index
    for i in range(0, cur_img_index - 1):
        if Path(img_list[i]).parent == cur_dir.parent:
            return i

    return cur_img_index + 1


def nextImage(direction):
    global cur_img_index, cur_timer, cur_photo, timer_paused, cur_window_width, cur_image
    global total_image_shown, total_time_spent

    total_time_spent += (max_timer_value - cur_timer)

    print('Took {} seconds. '.format(max_timer_value - cur_timer))

    cur_timer = max_timer_value

    # unpause if was paused
    if timer_paused:
        pauseImage()

    # set label default color
    timeImgLabel.config(foreground='blue')

    # next image index
    if direction == 2:
        # next image in same folder as current image
        cur_img_index = getIndexOfNextImageInSameFolder()
    else:
        cur_img_index += direction

    if cur_img_index == len(img_list):
        cur_img_index = 0
    elif cur_img_index < 0:
        cur_img_index = len(img_list) - 1

    cur_image = loadImage(img_list[cur_img_index])

    # use PIL (Pillow) to convert to a PhotoImage
    cur_photo = PIL.ImageTk.PhotoImage(cur_image)

    timeImgLabel.config(image=cur_photo)

    imgFileNameLabel.config(text=img_list[cur_img_index], wraplength=cur_window_width)


def copyImage():
    print('Copy to clipboard: {0}'.format(img_list[cur_img_index]))
    saveToClipboard(img_list[cur_img_index])


def mirrorImage():
    global cur_photo, cur_image
    print('Mirror image: {0}'.format(img_list[cur_img_index]))

    cur_image = PIL.ImageOps.mirror(cur_image)

    # use PIL (Pillow) to convert to a PhotoImage
    cur_photo = PIL.ImageTk.PhotoImage(cur_image)

    timeImgLabel.config(image=cur_photo)


def getTotalMonitorsWidth():
    monitors = screeninfo.get_monitors()

    total_width = 0
    for m in reversed(monitors):
        total_width += m.width

    return total_width


def loadImage(img_file_path):
    global total_image_shown, screen_width, cur_window_width

    # window default size
    target_img_width = default_image_width
    target_img_height = default_image_height

    # load an image
    pil_img = PIL.Image.open(img_file_path)

    pil_img = PIL.ImageOps.exif_transpose(pil_img)

    # get the image dimensions
    width, height = pil_img.size

    # make window well scaled and not greater when original dimensions
    cur_img_ratio = width / height
    target_def_ratio = target_img_width / target_img_height

    # calculate appropriate width or height for the new image
    if cur_img_ratio > target_def_ratio:
        target_img_height = int(target_img_width / cur_img_ratio)
    else:
        target_img_width = int(target_img_height * cur_img_ratio)

    # get screen width and height
    # ws = window.winfo_screenwidth()  # width of the screen
    hs = window.winfo_screenheight()  # height of the screen

    # calculate x and y coordinates for the Tk root window
    button_height = int(26 * 2.66)

    # position window
    x = screen_width - target_img_width - screen_width / 64
    y = hs / 32 + button_height

    if y > (hs - target_img_height):
        y = 0

    # just magic variable
    border_x = 6

    cur_window_width = target_img_width + border_x

    # image file name height
    fileName_height = 20

    # set the dimensions of the screen and where it is placed
    # if we don't see right side - slightly move window to the left
    if window.winfo_x() > x:
        window.geometry('%dx%d+%d+%d' % (cur_window_width, target_img_height + button_height + fileName_height, x, y))
    else:
        window.geometry('%dx%d' % (cur_window_width, target_img_height + button_height + fileName_height))

    pil_img = pil_img.resize((target_img_width, target_img_height), resample=PIL.Image.Resampling.LANCZOS)

    print('{}, w={}, h={}'.format(img_file_path, target_img_width, target_img_height))

    total_image_shown += 1

    return pil_img


# command line arguments
parser = argparse.ArgumentParser(description='Rotate images from directory in given timeout.')

parser.add_argument('-path', metavar='path', default='', nargs='+',
                    help='paths to the images directory (current directory by default). You can specify many '
                         'directories')

parser.add_argument('-zip-path', metavar='zip_path', default='',
                    help='path to the directory with zip files contains images')

parser.add_argument('-zip-file', metavar='zip_file', default='', nargs='+',
                    help='zip files with images. You can specify many files.')

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

img_list = []
cur_img_index = 0
cur_photo = 0
cur_image = 0

zip_extract_temp_paths = []

if args.zip_file:

    # extract the zip files to temp directories and return list of images inside them
    img_list = findAllSupportedZipFiles(args.zip_file)

elif args.zip_path:

    if not args.zip_path or not exists(args.zip_path):
        print('Directory {} not found'.format(args.zip_path))
        sys.exit(-1)

    # if zip-path defined - use it to find archives
    zip_files_list = findAllSupportedFiles([args.zip_path], zip_extensions)

    if len(zip_files_list) == 0:
        print('No supported archives found in directory {}'.format(args.zip_path))
        sys.exit(-1)

    # now peek one random archive file and extract it to the temp directory
    img_list = findAllSupportedZipFiles([random.choice(zip_files_list)])

else:
    # use specified path or current directory to find all supported images
    img_list = findAllSupportedFiles(args.path if args.path else '.', image_extensions)

if len(img_list) == 0:
    print('No supported images found')
    sys.exit(-1)

# shuffle images
random.shuffle(img_list)

print('{} images found'.format(len(img_list)))

# get screen width in multi-monitor configuration
screen_width = getTotalMonitorsWidth()

print('Total monitor(s) width in pixels: {0}'.format(screen_width))

# create a window
window = tk.Tk()
window.title('Slide show')

# prev button
tk.Button(window, text='Prev', width=5,
          command=lambda: nextImage(-1)).grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)

# pause button
pauseButton = tk.Button(window, text='Pause', width=5, command=lambda: pauseImage())
pauseButton.grid(row=0, column=1, sticky=tk.N + tk.E + tk.S + tk.W)

# copy button
tk.Button(window, text='Copy', width=5,
          command=lambda: copyImage()).grid(row=0, column=2, sticky=tk.N + tk.E + tk.S + tk.W)

# copy button
tk.Button(window, text='Mirror', width=5,
          command=lambda: mirrorImage()).grid(row=0, column=3, sticky=tk.N + tk.E + tk.S + tk.W)

# next (in folder) button
tk.Button(window, text='Next in fld', width=5,
          command=lambda: nextImage(2)).grid(row=0, column=4, sticky=tk.N + tk.E + tk.S + tk.W)

# next button
tk.Button(window, text='Next', width=5,
          command=lambda: nextImage(1)).grid(row=0, column=5, sticky=tk.N + tk.E + tk.S + tk.W)

# load image
cur_image = loadImage(img_list[cur_img_index])

# use PIL (Pillow) to convert to a PhotoImage
cur_photo = PIL.ImageTk.PhotoImage(cur_image)

# label for image and timer
timeImgLabel = tk.Label(image=cur_photo, text="00:00", font=("Arial", 24), foreground='blue', compound='bottom')
timeImgLabel.grid(row=1, column=0, columnspan=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)

imgFileNameLabel = tk.Label(text=img_list[cur_img_index], compound='bottom', justify='left',
                            wraplength=cur_window_width)
imgFileNameLabel.grid(row=2, column=0, columnspan=count_buttons, sticky=tk.N + tk.S + tk.W)

# callback to update timer and change image
window.after(1000, updateTimeLabel)

# run the window loop
window.mainloop()

# some statistics
total_time_spent += (max_timer_value - cur_timer)

print('{} images were drawn in {} seconds (average {:.2f} seconds per image)'.format(
    total_image_shown, total_time_spent, total_time_spent / total_image_shown))
