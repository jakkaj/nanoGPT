import math
import os
from pathlib import Path
import pickle
import shutil
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
# Hyperparameters

image_segment_split = 3

scratch_pad = "./data/scratch"
base_path = "./data/train_bom_3"


from bom_tools.preparation_tools import encode_lines, encode, recursive_directory_reader, calculate_non_transparent_percentage, scratch_pad, base_path, image_segment_split, _clear_scratch, image_parser_wrapper
#main 
if __name__ == "__main__":
    # get the current working directory
    #cwd = "/data/BomWeather/BomWeather"
    cwd = "/data/bom_radar/IDR713"
    
    with open(os.path.join(base_path, 'meta.pkl'), 'rb') as f:
        loaded_meta = pickle.load(f)
    
    stoi = loaded_meta.get('stoi')
    itos = loaded_meta.get('itos')    
    
    

    # create an empty list
    files = []

    # call the recursive directory reader method
    files = recursive_directory_reader(cwd)

    files = sorted(files)

    all_percents = []

    # for file in files:
    #     percents = image_parser(file)
    #     if percents is None:
    #         continue
    #     all_percents.append(percents)

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = executor.map(image_parser_wrapper, files)

    all_percents = [result for result in results if result != 'No Result']

    # print (all_percents)

    bigstring = ""

    for img_percent in all_percents:
        for percent in img_percent:
            bigstring += f"{percent} "
        bigstring += "\n"
    # print (bigstring)

    lines = bigstring.splitlines()
    
    
    ids = encode_lines(lines, stoi)
    
    print(ids)
    
    #save bigstring to file
    with open(os.path.join(base_path, 'bigstring.txt'), 'w') as f:
        f.write(bigstring)
        
    print (bigstring)