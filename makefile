gpt2: 
	python sample.py \
		--init_from=gpt2-xl \
		--start="Generate some sample json data" \
		--num_samples=1 --max_new_tokens=100

bom_downloader_docker:
	cd bom && docker build -t bom_downloader ./
	docker run -it --rm -v $(HOST_PROJECT_PATH)/data/bom_radar:/app/data/bom_radar bom_downloader