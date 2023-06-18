import os
import cv2
import imageio
import numpy as np
from skimage.transform import resize
from bom_tools.preparation_tools import image_segment_split

def render_gif(files, target):
    # create the animation
    with imageio.get_writer(target, mode='I') as writer:
        for file in files:
            image = imageio.imread(file)
            writer.append_data(image)

def render_bigstring(bigstring, target, scratch, clear_files=False, repeat=1):
    
    scratch_path = os.path.join(scratch, "render_bigstring")
    # ensure scratch_path exists
    if not os.path.exists(scratch_path):
        os.makedirs(scratch_path)
    
    
    lines = bigstring.splitlines()
    
    files = []
    for line_num, line in enumerate(lines):
        line = line.strip()
        percents = [int(p) for p in line.split(' ')]
        np_percent = np.array(percents)
        # multiple them all by 10
        np_percent = np_percent * 10
        np_matrix = np.reshape(np_percent, (image_segment_split, image_segment_split))
        #print (np_matrix)
        image = np.zeros((384, 384), dtype=np.uint8)

        # fill each segment with the corresponding percentage
        for j in range(image_segment_split):
            for i in range(image_segment_split):
                x = i * 128
                y = j * 128
                w = 128
                h = 128
                fill = int(np_matrix[j, i] / 100 * 255)
                cv2.rectangle(image, (x, y), (x + w, y + h), fill, -1)

        
        # save the image
        for i in range(repeat):
            image_save_path = os.path.join(scratch_path, str(line_num) + "_" + str(i) + ".png")
            files.append(image_save_path)
            cv2.imwrite(image_save_path, image)
        
        
    render_gif(files, target)
    if clear_files:
        # remove all files in files
        for file in files:
            os.remove(file)
    

"""
reads the two gifs then uses open cv to render them side by side
saves the output to a new gif
"""


def join_gifs(gif_paths, output_path, duration=0.3):
    # read all GIF files into a list of images sequences (frames)
    gif_images = [imageio.mimread(path) for path in gif_paths]

    # Ensure all gifs have the same number of frames, otherwise this won't work
    min_len = min([len(gif) for gif in gif_images])
    gif_images = [gif[:min_len] for gif in gif_images]

    # Get the maximum height among all frames in all GIFs
    max_height = max(max(img.shape[0] for img in gif) for gif in gif_images)

    # Join gifs frame by frame
    output_images = []
    for frame_index in range(min_len):
        # Get the corresponding frame from each gif
        frames = [gif[frame_index] for gif in gif_images]

        # Resize frames to have the same height
        frames = [resize(frame, (max_height, frame.shape[1]), mode='reflect', preserve_range=True).astype(np.uint8) for frame in frames]

        # Concatenate frames side by side and append to output frames list
        output_images.append(np.concatenate(frames, axis=1))
    
    # Save new gif
    imageio.mimsave(output_path, output_images, 'GIF', duration=duration, loop=0)
