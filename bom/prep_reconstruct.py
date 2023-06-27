from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
import numpy as np
from tqdm import tqdm
import concurrent.futures

import pickle

import cv2
from bom_tools.preparation_tools import get_scratch, percentages_to_image, image_parser, get_percents_string, get_percents, encode_lines, encode, get_vocabs, local_encode, recursive_directory_reader, calculate_non_transparent_percentage, scratch_pad, base_path, image_segment_split, _clear_scratch, image_parser_wrapper
from bom_tools.render_tools import join_gifs, render_gif, render_bigstring


def process_file(file):
    scratch = get_scratch()
    
    file_percent = image_parser(file)
    if file_percent is  None:
        return None
    
    parsed_image = percentages_to_image(file_percent)
    
    # get only filename component from file
    
    
    # file_save= os.path.join(scratch,"lowgen", f'{os.path.basename(file)}.jpg')
    # os.makedirs(os.path.dirname(file_save), exist_ok=True)
    # #ensure file_save directory exists
    
    
    
    # # save with cv2
    # cv2.imwrite(file_save, parsed_image)
    
    high_res_percent = image_parser(file, 32)
    high_parsed_image = percentages_to_image(high_res_percent, 32)
    return (parsed_image, high_parsed_image)


# main
if __name__ == "__main__":
    scratch = _clear_scratch()
    render_path = '/data/BomWeather/BomWeather'

    

    files = recursive_directory_reader(render_path)

    files = sorted(files)
    
    # get first 1000 files
    files = files[:200]

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        img_pairs = list(tqdm(executor.map(process_file, files), total=len(files)))

        
    img_pairs = [img for img in img_pairs if img is not None]
    # save img_pairs using pickle

    #convert teh image pairs to np.arrays
    img_pairs_np = [(np.array(img[0]), np.array(img[1])) for img in img_pairs]

    #now run torchvision.transforms.ToTensor() on each of the images
    
    
    
    with open(os.path.join(scratch, 'img_pairs.pkl'), 'wb') as f:
        pickle.dump(img_pairs_np, f)
