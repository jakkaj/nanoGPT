import math
import os
from pathlib import Path
import pickle
import shutil
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
# Hyperparameters

from bom_tools.preparation_tools import encode_lines, encode, get_vocabs, local_encode, recursive_directory_reader, calculate_non_transparent_percentage, scratch_pad, base_path, image_segment_split, _clear_scratch, image_parser_wrapper

image_segment_split = 3

scratch_pad = "./data/scratch"
base_path = "./data/train_bom_3"


# main
if __name__ == "__main__":
    # get the current working directory
    #cwd = "/data/BomWeather/BomWeather"
    cwd = "/data/BomWeather/BomWeather/2020/07"
    scratch_path = _clear_scratch()
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

    # print (all_percents)

    bigstring = ""

    for img_percent in all_percents:
        for percent in img_percent:
            bigstring += f"{percent} "
        bigstring += "\n"
    
    # save bigstring to file`
    with open(os.path.join(scratch_path, 'bigstring.txt'), 'w') as f:
        f.write(bigstring)

    lines = bigstring.splitlines()

    

    vocabs = get_vocabs()

    stoi = vocabs[0]
    itos = vocabs[1]
    
    # bigstring_ids = encode_lines(lines, stoi)

    # # save all ids to file
    # with open(os.path.join(scratch_path, 'bigstring_encoded.txt'), 'w') as f:
    #     f.write(bigstring_ids)

    total_lines = len(lines)

    split_index = int(total_lines * 0.9)  # Calculate the index where to split

    train_data = lines[:split_index]
    val_data = lines[split_index:]

    # n = len(all_ids)
    # train_data = all_ids[:int(n*0.9)]
    # val_data = all_ids[int(n*0.9):]

    # Ensure teh percentages are encoded as a unit, not per char, e.g. 99 not 9 and 9 separately
    train_ids = encode_lines(train_data, stoi)
    val_ids = encode_lines(val_data, stoi)
    

    # num_copies = 1000
    # train_data_repeated = [x for x in train_ids for _ in range(num_copies)]
    # val_data_repeated = [x for x in val_ids for _ in range(num_copies)]

    train_ids = np.array(train_ids).astype(np.uint16)
    val_ids = np.array(val_ids).astype(np.uint16)

    print(f"train has {len(train_ids):,} tokens")
    print(f"val has {len(val_ids):,} tokens")

    # ensure path exists
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    train_ids.tofile(os.path.join(base_path, 'train.bin'))
    val_ids.tofile(os.path.join(base_path, 'val.bin'))

    # save the meta information as well, to help us encode/decode later
    meta = {
        'vocab_size': vocabs[2],
        'itos': itos,
        'stoi': stoi,
    }
    with open(os.path.join(base_path, 'meta.pkl'), 'wb') as f:
        pickle.dump(meta, f)
