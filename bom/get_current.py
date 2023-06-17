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


from bom_tools.preparation_tools import encode, recursive_directory_reader, calculate_non_transparent_percentage, scratch_pad, base_path, image_segment_split, _clear_scratch, image_parser_wrapper
#main 
if __name__ == "__main__":
    # get the current working directory
    #cwd = "/data/BomWeather/BomWeather"
    cwd = "./data/bom_radar/IDR713"
    _clear_scratch()
    # ensure scratch_pad path exists
    if not os.path.exists(scratch_pad):
        os.makedirs(scratch_pad)

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

    #print (all_percents)

    bigstring = ""
    
    for img_percent in all_percents:
        for percent in img_percent:
            bigstring += f"{percent:03d}"
        bigstring += "\n"       
    #print (bigstring)
    
    lines = bigstring.splitlines()
    
    all_ids = encode(lines)
    
    
    
    chars = sorted(list(set(all_ids)))
    vocab_size = len(chars)
    
    
    print(vocab_size)
    
    with open(os.path.join(base_path, 'meta.pkl'), 'rb') as f:
        loaded_meta = pickle.load(f)
    
    stoi = loaded_meta.get('stoi')
    itos = loaded_meta.get('itos')    
    
    def local_encode(s):
        return [stoi.get(c, 999) for c in s] # encoder: take a string, output a list of integers
    def local_decode(l):
        return ''.join([itos[i] for i in l]) # decoder: take a list of integers, output a string
    
    
    
    train_ids = local_encode(all_ids)
    
    
   
   
    
    
     
    # num_copies = 1000
    # train_data_repeated = [x for x in train_ids for _ in range(num_copies)]
    # val_data_repeated = [x for x in val_ids for _ in range(num_copies)]


   # train_ids = np.array(train_ids).astype(np.uint16)
    print (train_ids)
    print(all_ids)
    
    print(f"train has {len(train_ids):,} tokens")
   
    