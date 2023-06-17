import os
import shutil
import cv2
import numpy as np

# Hyperparameters

image_segment_split = 4

scratch_pad = "./data/scratch"


# a method that is a recursive directory reader
def recursive_directory_reader(path, file_list):
    

    # get the list of files in the directory
    files = os.listdir(path)

    # iterate over the files
    for file in files:
        # check if the file is a directory
        if os.path.isdir(path + "/" + file):
            # if the file is a directory, call this method again with the new path
            file_list = recursive_directory_reader(path + "/" + file, file_list)
        else:
            # if the file is not a directory, append it to the list
            file_list.append(path  + file)

    # return the file list
    return file_list


def calculate_non_transparent_percentage(image):
    
    # If the image has 4 channels, assume it's in BGRA format
    if image.shape[2] == 4:
        # Alpha channel is the 4th channel
        alpha_channel = image[:, :, 3]

        # Count non-zero (i.e., non-transparent) pixels in the alpha channel
        non_transparent_pixels = np.count_nonzero(alpha_channel)

        # Total pixels in the image
        total_pixels = alpha_channel.size

        # Calculate percentage
        non_transparent_percentage = (non_transparent_pixels / total_pixels) * 100
    else:
        # If image doesn't have an alpha channel, it's fully opaque
        non_transparent_percentage = 100

    return non_transparent_percentage

# opens the file with opencv
def image_parser(file):
    global image_segments
    # open the file with opencv
    img = cv2.imread(file, cv2.IMREAD_UNCHANGED)

    filename_nopath = os.path.basename(file)
    
    

    # get the height and width of the image
    height, width, channels = img.shape

    horizontal_segments = image_segment_split
    vertical_segments = image_segment_split

    # calculate the size of each segment
    segment_width = width // horizontal_segments
    segment_height = height // vertical_segments

    # initialize an array to hold the image segments
    image_segments = []

    # split the image into segments
    for i in range(vertical_segments):
        for j in range(horizontal_segments):
            # calculate the boundaries of the segment
            x_start = j * segment_width
            y_start = i * segment_height
            x_end = (j+1) * segment_width
            y_end = (i+1) * segment_height

            # slice the image to create the segment
            segment = img[y_start:y_end, x_start:x_end]
            
            # append the segment to the list
            image_segments.append(segment)

    percents = []

    # save the segments
    for i in range(len(image_segments)):
        # get the segment
        segment = image_segments[i]
        file_name = os.path.join(scratch_pad, filename_nopath + "_" + str(i) + ".png")
        #ensure the path for file_name exists
        cv2.imwrite(file_name, segment)
        percent = calculate_non_transparent_percentage(segment)
        percents.append(percent)
    
    print(percents)
    

def _clear_scratch():
    
    # remove all files and folders in scratch_pad
    shutil.rmtree(scratch_pad)
    
    
    

#main 
if __name__ == "__main__":
    # get the current working directory
    cwd = "/data/bom_radar/IDR664/2023/06/17/"
    _clear_scratch()
    # ensure scratch_pad path exists
    if not os.path.exists(scratch_pad):
        os.makedirs(scratch_pad)

    # create an empty list
    files = []

    # call the recursive directory reader method
    files = recursive_directory_reader(cwd, files)

    files = sorted(files)

    for file in files:
        image_parser(file)

    # print the list of files
    

