from concurrent.futures import ThreadPoolExecutor
from bom_tools.preparation_tools import get_percents_string, get_percents, encode_lines, encode, get_vocabs, local_encode, recursive_directory_reader, calculate_non_transparent_percentage, scratch_pad, base_path, image_segment_split, _clear_scratch, image_parser_wrapper
from bom_tools.render_tools import join_gifs, render_gif, render_bigstring


#main
if __name__ == "__main__":   
    
    render_path = "/data/BomWeather/BomWeather/2020/05/21"
    
    starter = "0806.png"
    
    
    
    
    scratch = _clear_scratch()
    
    
    files = recursive_directory_reader(render_path)

    files = sorted(files)
    
    # find the index of the file that contains the starter string
    index = next((i for i, f in enumerate(files) if starter in f), None)

    # return all files after and including the starter file
    files = files[index:] if index is not None else []

    gif1 = "./data/scratch/orig_animation.gif"
    gif2 = "./data/scratch/percents_orig_animation.gif"
    gif3 = "./data/scratch/combined.gif"
    render_gif(files, gif1)

    all_percents = get_percents(files)
    
    bigstring = get_percents_string(all_percents)

    render_bigstring(bigstring, gif2, scratch)
    
    join_gifs([gif1, gif2], gif3)
    
    