.PHONY: msft test prepare-data

msft:
	python stock_data.py MSFT --output data/msft_data.csv

test:
	@echo "Running data preparation tests..."
	# Run pytest from the project root directory
	cd .. && pytest tests/data_preparation

prepare-data:
	@echo "Running data preparation pipeline..."
	# Run pipeline script as module from project root
	cd .. && python -m quant.data_preparation.data_pipeline \
		--data-dir quant/data/historical \
		--output-dir quant/data/processed