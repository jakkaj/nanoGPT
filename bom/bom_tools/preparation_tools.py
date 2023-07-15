# a method that is a recursive directory reader

import math
import os
from pathlib import Path
import pickle
import shutil
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
# Hyperparameters
image_segment_split = 8
image_round_percent = 5


scratch_pad = "./data/scratch"
base_path = "./data/train_bom_3"

def recursive_directory_reader(path):
    

    return [str(f) for f in Path(path).rglob("*.png")]


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
        
        if non_transparent_percentage < 10:
            non_transparent_percentage = 0
        
        #round non_transparent_percentage to nearest 5%
        
        
        
    else:
        # If image doesn't have an alpha channel, it's fully opaque
        non_transparent_percentage = 100

    

    #round up non_transparent_percentage to nearest int
    non_transparent_percentage =  math.floor(non_transparent_percentage)
    #non_transparent_percentage = non_transparent_percentage / 100
    non_transparent_percentage = math.floor(non_transparent_percentage / image_round_percent) * image_round_percent

    # if(non_transparent_percentage > 20):
    #     print(f"non_transparent_percentage: {non_transparent_percentage}")

    return non_transparent_percentage

def percentages_to_image(percents, seg = image_segment_split):
    percentages = np.array(percents)
    # Reshape to 3x3 and convert to grayscale image
    img_small = np.reshape(percentages, (seg, seg))

    # Convert small image to 8-bit grayscale image (range 0-255)
    img_small = (img_small * 255).astype(np.uint8)
    
    return img_small




def tidy_image(image):
    # Find the size of the image
    height, width = image.shape

    # Determine the size of each segment
    segment_height = height // image_segment_split
    segment_width = width // image_segment_split

    # Create a new image to hold the output
    output_image = np.zeros_like(image)

    # Iterate over the image
    for i in range(image_segment_split):
        for j in range(image_segment_split):
            # Find the bounds of the current segment
            start_i = i * segment_height
            end_i = (i+1) * segment_height
            start_j = j * segment_width
            end_j = (j+1) * segment_width

            # Extract the segment from the image
            segment = image[start_i:end_i, start_j:end_j]

            # Count the number of non-black pixels
            non_black_pixels = np.sum(segment > 0)

            # If less than 5% of the pixels are non-black
            if non_black_pixels < 0.10 * segment_width * segment_height:
                # Set the segment to black
                output_image[start_i:end_i, start_j:end_j] = 0
            else:
                # Otherwise, copy the original segment
                output_image[start_i:end_i, start_j:end_j] = segment

    return output_image


    

# opens the file with opencv
def image_parser(file, seg = image_segment_split):
    #print(file)
    
    # open the file with opencv
    img = cv2.imread(file, cv2.IMREAD_UNCHANGED)
    if(img is None):
        #print(f"Dead: {file}")
        return None
    filename_nopath = os.path.basename(file)
    
    img[:16,:] = 0
    
    threshold = np.all(img[..., :3] < [5, 5, 5], axis=2)

    # For every pixel that is close to black, we set its alpha value to 0
    img[threshold] = (0, 0, 0, 0)

    # get the height and width of the image
    height, width, channels = img.shape

    horizontal_segments = seg
    vertical_segments = seg

    # calculate the size of each segment
    segment_width = width // horizontal_segments
    segment_height = height // vertical_segments

    # if segment_width or segment_height is not a whole number, throw error
    if segment_width * horizontal_segments != width or segment_height * vertical_segments != height:
        raise ValueError('The number of horizontal/vertical segments must divide the image perfectly.')

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
        #cv2.imwrite(file_name, segment)
        percent = calculate_non_transparent_percentage(segment)
        percents.append(percent)
    
    # #print(percents)
    # percentages = np.array(percents)
    # percentages = np.ceil(10 * percentages) / 100.0

    # # Clip values to the valid range for safety
    # percentages = np.clip(percentages, 0, 1)

    # # Reshape to 3x3 and convert to grayscale image
    # img_small = np.reshape(percentages, (seg, seg))

    # # Convert small image to 8-bit grayscale image (range 0-255)
    # img_small = (img_small * 255).astype(np.uint8)

    # # Upscale using nearest neighbor interpolation (to avoid blending values)
    # img_large = cv2.resize(img_small, (seg * 128, seg * 128), interpolation = cv2.INTER_NEAREST)
    # out_file = os.path.join(scratch_pad, filename_nopath + "_large.png")
    # Save the image
    #cv2.imwrite(out_file, img_large)
    
    return percents

def get_scratch():
    return scratch_pad

def _clear_scratch():
    if os.path.exists(scratch_pad):
        # remove all files and folders in scratch_pad
        shutil.rmtree(scratch_pad)
    # ensure scratch_pad path exists
    if not os.path.exists(scratch_pad):
        os.makedirs(scratch_pad)
    return scratch_pad
   
def normalize(x, min_value=0, max_value=999999999):
    normalized_value = (x - min_value) / (max_value - min_value)
    return normalized_value

def denormalize(normalized_x, min_value=0, max_value=999999999):
    original_value = normalized_x * (max_value - min_value) + min_value
    return original_value
   
    
def encode(text_array):
    # split the text in to lines
    lines = text_array
    
    lines_array_int = []


    for line in lines:
        lint_int = int(line)
        lines_array_int.append(lint_int)
        lines_array_int.append(-1)
    
    return lines_array_int

def decode(ints):
    output = ""
    for i in ints:
        if i == 1:
            output += "\n"
        else:
            output += f"{i:09d}"

    return output

def image_parser_wrapper(file):
    percents = image_parser(file)
    return percents if percents is not None else 'No Result'

def get_vocabs():   

    all_chars = [str(i) for i in range(0, 101, image_round_percent)]
    all_chars.append(" ")
    all_chars.append("\n")
    
    chars = sorted(list(set(all_chars)))
    vocab_size = len(chars)    
    
    print(vocab_size)
    
    stoi = { ch:i for i,ch in enumerate(chars) }
    itos = { i:ch for i,ch in enumerate(chars) }
    
    return (stoi, itos, vocab_size)
    
def local_encode(s, stoi):
    return stoi[s] # encoder: take a string, output a list of integers
def local_decode(l, itos):
        return ''.join([itos[i] for i in l]) # decoder: take a list of integers, output a string
    
def encode_lines(lines, stoi):
    result_ids = []
    for i in lines:
        #split local_encode(i) by ' '
        splits =i.split(' ') 
        for s in splits:
            if s == '':
                continue
            
            result_ids.append(local_encode(s, stoi))
        
        result_ids.append(local_encode('\n', stoi))
        
    return result_ids

def get_percents(files):
    all_percents = []

    
    

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(tqdm(executor.map(image_parser_wrapper, files), total=len(files)))


    all_percents = [result for result in results if result != 'No Result']
    
    return all_percents

def get_percents_string(all_percents):
    bigstring = ""
    
    for img_percent in all_percents:
        for percent in img_percent:
            bigstring += f"{percent} "
        bigstring += "\n"
    
    return bigstring