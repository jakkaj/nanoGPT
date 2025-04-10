"""

# Read in the data
data = pd.read_csv('data.csv')

# Rename columns
data = data.rename(columns={'Unnamed: 0': 'id'})

# Drop rows with missing values
data = data.dropna()

# Create new column with the log of the price
data['log_price'] = np.log(data['price'])

# Create new column with the log of the minimum number of nights
data['log_min_nights'] = np.log(data['minimum_nights'])

# Create new column with the log of the number of reviews
data['log_reviews'] = np.log(data['number_of_reviews'])

# Create new column with the log
Sample from a trained model
"""
import os
import pickle
from contextlib import nullcontext
import random
import torch
import tiktoken
from model import GPTConfig, GPT

# -----------------------------------------------------------------------------
# either 'resume' (from an out_dir) or a gpt2 variant (e.g. 'gpt2-xl')
init_from = 'resume'
out_dir = 'out-trainbom-3'  # ignored if init_from is not 'resume'
start = """5 5 0 5 5 5 0 5 20 
5 5 0 5 5 5 0 5 20 
5 5 0 5 5 5 0 5 20 
5 5 0 5 5 10 0 5 15 
5 5 0 5 5 10 0 5 15 
"""  # or "<|endoftext|>" or etc. Can also specify a file, use as: "FILE:prompt.txt"
save_to = ""
num_samples = 1  # number of samples to draw
max_new_tokens = 2048  # number of tokens generated in each sample
# 1.0 = no change, < 1.0 = less random, > 1.0 = more random, in predictions

#1 AND 400 IS PRETTY GOOD (JORDO)

temperature = .8
top_k = 300  # retain only the top_k most likely tokens, clamp others to have 0 probability
seed = random.randint(0, 10000)
#seed = 1337
device = 'cuda'  # examples: 'cpu', 'cuda', 'cuda:0', 'cuda:1', etc.
dtype = 'bfloat16' if torch.cuda.is_bf16_supported(
) else 'float16'  # 'float32' or 'bfloat16' or 'float16'
compile = False  # use PyTorch 2.0 to compile the model to be faster
# overrides from command line or config file
exec(open('configurator.py').read())
# -----------------------------------------------------------------------------

torch.manual_seed(seed)
torch.cuda.manual_seed(seed)
torch.backends.cuda.matmul.allow_tf32 = True  # allow tf32 on matmul
torch.backends.cudnn.allow_tf32 = True  # allow tf32 on cudnn
# for later use in torch.autocast
device_type = 'cuda' if 'cuda' in device else 'cpu'
ptdtype = {'float32': torch.float32,
           'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
ctx = nullcontext() if device_type == 'cpu' else torch.amp.autocast(
    device_type=device_type, dtype=ptdtype)

# model
if init_from == 'resume':
    # init from a model saved in a specific directory
    ckpt_path = os.path.join(out_dir, 'ckpt.pt')
    checkpoint = torch.load(ckpt_path, map_location=device)
    gptconf = GPTConfig(**checkpoint['model_args'])
    model = GPT(gptconf)
    state_dict = checkpoint['model']
    unwanted_prefix = '_orig_mod.'
    for k, v in list(state_dict.items()):
        if k.startswith(unwanted_prefix):
            state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
    model.load_state_dict(state_dict)
elif init_from.startswith('gpt2'):
    # init from a given GPT-2 model
    model = GPT.from_pretrained(init_from, dict(dropout=0.0))

model.eval()
model.to(device)
if compile:
    model = torch.compile(model)  # requires PyTorch 2.0 (optional)

# look for the meta pickle in case it is available in the dataset folder
load_meta = False
# older checkpoints might not have these...
if init_from == 'resume' and 'config' in checkpoint and 'dataset' in checkpoint['config']:
    meta_path = os.path.join(
        'data', checkpoint['config']['dataset'], 'meta.pkl')
    load_meta = os.path.exists(meta_path)
if load_meta:
    print(f"Loading meta from {meta_path}...")
    with open(meta_path, 'rb') as f:
        meta = pickle.load(f)
    # TODO want to make this more general to arbitrary encoder/decoder schemes
    stoi, itos = meta['stoi'], meta['itos']
    def encode(s_inptut):
        result_ids = []
        splits =s_inptut.split(' ')
        for s in splits:
            
            if '\n' in s:
                s = s.replace('\n', '')
                result_ids.append(stoi['\n'])
            
            if s == '':
                continue
            result_ids.append(stoi[s])                     
        return result_ids
        
    def decode(l): return ' '.join([itos[i] for i in l])
else:
    # ok let's assume gpt-2 encodings by default
    print("No meta.pkl found, assuming GPT-2 encodings...")
    enc = tiktoken.get_encoding("gpt2")
    def encode(s): return enc.encode(s, allowed_special={"<|endoftext|>"})
    def decode(l): return enc.decode(l)

# encode the beginning of the prompt
if start.startswith('FILE:'):
    with open(start[5:], 'r', encoding='utf-8') as f:
        start = f.read()
start_ids = encode(start)
x = (torch.tensor(start_ids, dtype=torch.long, device=device)[None, ...])

# run generation
with torch.no_grad():
    with ctx:
        for k in range(num_samples):
            y = model.generate(x, max_new_tokens,
                               temperature=temperature, top_k=top_k)
            print(y[0].tolist())
            decoded = decode(y[0].tolist())
            if save_to is not None and save_to != '':
                with open(save_to, 'w', encoding='utf-8') as f:
                    f.write(decoded)
            print(decoded)
            print('---------------')
