from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
from bom_tools.preparation_tools import get_percents_string, get_percents, encode_lines, encode, get_vocabs, local_encode, recursive_directory_reader, calculate_non_transparent_percentage, scratch_pad, base_path, image_segment_split, _clear_scratch, image_parser_wrapper
from bom_tools.render_tools import join_gifs, render_gif, render_bigstring

def run_process(command):
    """
    Runs a shell command and returns the output as a string.
    """
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error:
        raise Exception(f"Command '{command}' failed with error: {error.decode('utf-8')}")
    return output.decode('utf-8')

#main
if __name__ == "__main__":   
    
    prompt_number = 32    
    render_path = "/data/BomWeather/BomWeather/2020/07/07"
    starter = "336.png"
    
    # prompt_number = 16    
    # render_path = "/data/BomWeather/BomWeather/2020/01/23"
    # starter = "1000.png"
    
    
    # this one is good (big storm from west)
    # prompt_number = 12
    # render_path = "/data/BomWeather/BomWeather/2020/06/20"
    # starter = "1524.png"
    
    #render_path = "/data/bom_radar/IDR713/2023/06/18"
    
    
    scratch = _clear_scratch()    
    
    files = recursive_directory_reader(render_path)

    files = sorted(files)
    
    # find the index of the file that contains the starter string
    index = next((i for i, f in enumerate(files) if starter in f), None)

    # return all files after and including the starter file
    files = files[index:] if index is not None else []

    gif1 = os.path.join(scratch, "orig_animation.gif")
    gif2 = os.path.join(scratch, "percents_orig_animation.gif")
    gif3 = os.path.join(scratch, "combined.gif")  
    gif4 = os.path.join(scratch, "bigstring_starter.gif") 
    gif5 = os.path.join(scratch, "predictions.gif")
    gif6 = os.path.join(scratch, "actuals.gif")
    gif7 = os.path.join(scratch, "predictions_actuals.gif")
    all_percents = get_percents(files)
    
    bigstring = get_percents_string(all_percents)    
    
    
    
    # get prompt_number lines from start of bigstring
    lines = bigstring.splitlines()[:prompt_number]    
    
    #render them to a string with \n between them
    prompt_lines = "\n".join(lines) + "\n"
    
    prompt_file = os.path.join(scratch, "prompt.txt")
    result_file = os.path.join(scratch, "prompt_result.txt")
    
    with open(prompt_file, "w") as f:
        f.write(prompt_lines)
    
    # run a python program python sample_bom.py --out_dir=out-trainbom-3 --start={prompt_file}
    command = f"python sample_bom.py --out_dir=out-trainbom-3 --start=FILE:{prompt_file} --save_to={result_file}"
    run_process(command)
    
    
    score_lines = ""
    # read result_file
    with open(result_file, "r") as f:
        score_lines = f.read()
    
    #read each line in score_lines, split it by spaces and validate that it has 9 elements
    
    valid_score_lines = []
    for line in score_lines.splitlines():
        score = line.split()
        if len(score) != image_segment_split * image_segment_split:
            continue
        valid_score_lines.append(line)
    
    print('\n'.join(valid_score_lines))
    
    # get len(valid_score_lines) lines from teh start of bigstring
    original_lines = bigstring.splitlines()[:len(valid_score_lines)]
    render_bigstring("\n".join(valid_score_lines), gif5, scratch, True, 1, prompt_number)
    render_bigstring("\n".join(original_lines), gif6, scratch, True, 1)
    join_gifs([gif6, gif5], gif7)
    
    
    
    
    
    # render originals and things
    render_gif(files, gif1)
    
    render_bigstring(bigstring, gif2, scratch)
    render_bigstring(prompt_lines, gif4, scratch)
    
    #join_gifs([gif1, gif2], gif3)