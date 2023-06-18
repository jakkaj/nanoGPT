gpt2: 
	python sample.py \
		--init_from=gpt2-xl \
		--start="Generate some sample json data" \
		--num_samples=1 --max_new_tokens=100
	
bom_downloader_docker:
	cd bom && docker build -t bom_downloader ./
	docker run -it --rm -v /data/bom_radar:/app/data/bom_radar bom_downloader

bom_train:
	python train.py config/train_bom_3.py

bom_generate:
	python sample_bom.py --out_dir=out-trainbom-3

shakespear_train:
	python train.py config/train_shakespeare_char.py

