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
from os.path import join, exists, basename, splitext
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path

# supported file extensions
image_extensions = ['.jpg', '.png', '.bmp']
zip_extensions = ['.zip']

# some statistics
total_image_shown = 0
total_time_spent = 0

# helper variables for resize the window to fit new image
cur_window_width = 0
cur_window_height = 0

# total button count
count_buttons = 0

# color theme for timer  setup here
timer_foreground_color = 'cyan'
timer_foreground_color_low = 'red'


class ImagePath:
    """Path to image"""
    def __init__(self, img_path):
        self.img_path = img_path

    def get_path(self):
        return self.img_path

    def get_folder(self):
        return Path(self.img_path).parent

    def same_folder(self, other):
        return self.get_folder() == other.get_folder()

    def exclude_folder(self):
        global img_list

        print('Exclude folder/archive: {0}'.format(self.get_folder()))
        img_list = [item for item in img_list if not self.same_folder(item)]
        print('{0} images left, current {1}'.format(len(img_list), cur_img_index))

        nextImage(1)


class ImagePathInZip(ImagePath):
    """Path to the zip with image in it + image file stored in this zip file
    If img_path empty - read image list from zip"""
    def __init__(self, zip_path, img_path, temp_path) :
        # path to archive
        self.zip_path = zip_path

        # image file name in archive
        self.img_path = img_path

        # one temporary directory for all zip archive
        self.temp_path = temp_path

        # if image was opened from archive - keep path to it here
        self.real_path_to_img = ''

    def get_folder(self):
        return self.zip_path

    def get_path(self):
        global cur_img_index

        if len(self.real_path_to_img) != 0:
            return self.real_path_to_img

        with ZipFile(self.zip_path, 'r') as zipObj:

            # if img_path empty - read all images from zip
            if not self.img_path or self.img_path == '':
                # create temp directory
                temp_path = tempfile.TemporaryDirectory(prefix=splitext(basename(self.zip_path))[0] + '_')

                # save temp path object in global list
                zip_extract_temp_paths.append(temp_path)

                for img_file in zipObj.namelist():
                    if is_file_valid(img_file, image_extensions):
                        if not self.img_path or self.img_path == '':
                            # set image in current element
                            self.img_path = img_file
                            self.temp_path = temp_path.name
                        else:
                            # add other images in list
                            img_list.append(ImagePathInZip(self.zip_path, img_file, temp_path.name))

                # shuffle images which go next in list to keep Next/Prev button working (more or less)
                if (cur_img_index + 1) < len(img_list):
                    # make copy
                    img_list_copy = img_list[(cur_img_index + 1):]

                    # shuffle it
                    random.shuffle(img_list_copy)

                    # return temporary list to the back of the list
                    img_list[(cur_img_index + 1):] = img_list_copy

            if not self.img_path or self.img_path == '':
                # zip without images - don't know what to do
                return ''

            # extract files into temp directory
            zipObj.extract(self.img_path, self.temp_path)

            # save path to temp directory in list
            self.real_path_to_img = join(self.temp_path, self.img_path)

            return self.real_path_to_img


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


def toImgList(path_list):
    temp_img_list = []

    for path in path_list:
        temp_img_list.append(ImagePath(path))

    return temp_img_list


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

    return toImgList(findAllSupportedFiles(temp_path_names, image_extensions))


def findAllSupportedZipFilesRandom(zip_file_list):
    temp_list = []

    for zip_file in zip_file_list:
        if not zip_file or not exists(zip_file):
            print('File {} not found'.format(zip_file))

        print('File {} found'.format(zip_file))

        temp_list.append(ImagePathInZip(zip_file, '', ''))

    return temp_list


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
        timeImgLabel.config(foreground=timer_foreground_color_low)

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


def getIndexOfPrevImageInSameFolder():
    global cur_img_index

    # search from current index till the beginning of list
    for i in reversed(range(0, cur_img_index - 1)):
        if img_list[cur_img_index].same_folder(img_list[i]):
            return i

    # search from the end of the list till current index
    for i in reversed(range(cur_img_index + 1, len(img_list))):
        if img_list[cur_img_index].same_folder(img_list[i]):
            return i

    return cur_img_index + 1


def getIndexOfNextImageInSameFolder():
    global cur_img_index

    # search from current index till the end of list
    for i in range(cur_img_index + 1, len(img_list)):
        if img_list[cur_img_index].same_folder(img_list[i]):
            return i

    # search from begin of list till current index
    for i in range(0, cur_img_index - 1):
        if img_list[cur_img_index].same_folder(img_list[i]):
            return i

    return cur_img_index + 1


def nextImage(direction):
    global cur_img_index, cur_timer, cur_photo, timer_paused, cur_window_width, cur_image
    global total_image_shown, total_time_spent

    total_time_spent += (max_timer_value - cur_timer)

    print('Image {0} took {1} second(s).'.format(cur_img_index, max_timer_value - cur_timer))

    cur_timer = max_timer_value

    # unpause if was paused
    if timer_paused:
        pauseImage()

    # set label default color
    timeImgLabel.config(foreground=timer_foreground_color)

    # next image index
    if direction == 2:
        # next image in same folder as current image
        cur_img_index = getIndexOfNextImageInSameFolder()
    elif direction == -2:
        # prev image in same folder as current image
        cur_img_index = getIndexOfPrevImageInSameFolder()
    else:
        cur_img_index += direction

    if cur_img_index == len(img_list):
        cur_img_index = 0
    elif cur_img_index < 0:
        cur_img_index = len(img_list) - 1

    cur_image = loadImage(img_list[cur_img_index].get_path())

    # use PIL (Pillow) to convert to a PhotoImage
    cur_photo = PIL.ImageTk.PhotoImage(cur_image)

    timeImgLabel.config(image=cur_photo)

    imgFileNameLabel.config(text=img_list[cur_img_index].get_path(), wraplength=cur_window_width)


def copyImage():
    print('Copy to clipboard: {0}'.format(img_list[cur_img_index].get_path()))
    saveToClipboard(img_list[cur_img_index].get_path())


def mirrorImage():
    global cur_photo, cur_image
    print('Mirror image: {0}'.format(img_list[cur_img_index].get_path()))

    cur_image = PIL.ImageOps.mirror(cur_image)

    # use PIL (Pillow) to convert to a PhotoImage
    cur_photo = PIL.ImageTk.PhotoImage(cur_image)

    timeImgLabel.config(image=cur_photo)

def excludeFolder():
    img_list[cur_img_index].exclude_folder()


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

    # apply exif information to rotate image properly (vertical or horizontal orientation)
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
                    help='Paths to the images directory (current directory by default). You can specify many '
                         'directories')

parser.add_argument('-zip-path', metavar='zip_path', default='',
                    help='Path to the directory with zip files contains images. The one random zip file selected,'
                         ' then all it images will be shown in random order')

parser.add_argument('-zip-path-random', metavar='zip_path_random', default='',
                    help='Path to the directory with zip files contains images. All zip files selected,'
                         ' then all images from all these files will be shown in random order')

parser.add_argument('-zip-file', metavar='zip_file', default='', nargs='+',
                    help='Zip files with images. You can specify many files.')

parser.add_argument('-timeout', dest='timeout', type=int, default=60,
                    help='Timeout in seconds (60 by default)')

parser.add_argument('-width', dest='width', type=int, default=600,
                    help='Window width in pixels (600 by default)')

parser.add_argument('-height', dest='height', type=int, default=800,
                    help='Window height in pixels (800 by default)')

args = parser.parse_args()
print(args)

# timeout in seconds
max_timer_value = args.timeout
cur_timer = max_timer_value
timer_paused = False

default_image_width = args.width
default_image_height = args.height

# list of ImagePath
img_list = []

cur_img_index = 0
cur_photo = 0
cur_image = 0

# keep created TemporaryDirectory objects here to prevent it from deletion (will be deleted after program exit)
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

elif args.zip_path_random:

    if not args.zip_path_random or not exists(args.zip_path_random):
        print('Directory {} not found'.format(args.zip_path_random))
        sys.exit(-1)

    # if zip-path defined - use it to find archives
    zip_files_list = findAllSupportedFiles([args.zip_path_random], zip_extensions)

    if len(zip_files_list) == 0:
        print('No supported archives found in directory {}'.format(args.zip_path))
        sys.exit(-1)

    img_list = findAllSupportedZipFilesRandom(zip_files_list)

else:
    # use specified path or current directory to find all supported images
    img_list = toImgList(findAllSupportedFiles(args.path if args.path else '.', image_extensions))

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

# setup color palette for window
window.tk_setPalette(background='#26242f', foreground='gray90',
                     activeBackground='gray10', activeForeground='gray80')

# prev button
tk.Button(window, text='Prev', width=5,
          command=lambda: nextImage(-1)).grid(row=0, column=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)
count_buttons += 1

# prev (in folder) button
tk.Button(window, text='Prev in fld', width=5,
          command=lambda: nextImage(-2)).grid(row=0, column=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)
count_buttons += 1

# pause button
pauseButton = tk.Button(window, text='Pause', width=5, command=lambda: pauseImage())
pauseButton.grid(row=0, column=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)
count_buttons += 1

# copy button
tk.Button(window, text='Copy', width=5,
          command=lambda: copyImage()).grid(row=0, column=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)
count_buttons += 1

# mirror button
tk.Button(window, text='Mirror', width=5,
          command=lambda: mirrorImage()).grid(row=0, column=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)
count_buttons += 1

# exclude button
tk.Button(window, text='Exclude fld', width=5,
          command=lambda: excludeFolder()).grid(row=0, column=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)
count_buttons += 1

# next (in folder) button
tk.Button(window, text='Next in fld', width=5,
          command=lambda: nextImage(2)).grid(row=0, column=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)
count_buttons += 1

# next button
tk.Button(window, text='Next', width=5,
          command=lambda: nextImage(1)).grid(row=0, column=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)
count_buttons += 1

# load image
cur_image = loadImage(img_list[cur_img_index].get_path())

# use PIL (Pillow) to convert to a PhotoImage
cur_photo = PIL.ImageTk.PhotoImage(cur_image)

# label for image and timer
timeImgLabel = tk.Label(image=cur_photo, text="00:00", font=("Arial", 24),
                        foreground=timer_foreground_color, compound='bottom')
timeImgLabel.grid(row=1, column=0, columnspan=count_buttons, sticky=tk.N + tk.E + tk.S + tk.W)

imgFileNameLabel = tk.Label(text=img_list[cur_img_index].get_path(),
                            compound='bottom', justify='left', wraplength=cur_window_width)
imgFileNameLabel.grid(row=2, column=0, columnspan=count_buttons, sticky=tk.N + tk.S + tk.W)

# callback to update timer and change image
window.after(1000, updateTimeLabel)

# run the window loop
window.mainloop()

# some statistics
total_time_spent += (max_timer_value - cur_timer)

print('{} images were drawn in {} seconds (average {:.2f} seconds per image)'.format(
    total_image_shown, total_time_spent, total_time_spent / total_image_shown))
