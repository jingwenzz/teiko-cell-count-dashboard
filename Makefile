.PHONY: setup pipeline dashboard

setup:
	pip install -r requirements.txt
	npm --prefix frontend install

pipeline:
	python run_pipeline.py

dashboard:
	test -f cell_counts.db || python load_data.py
	npm --prefix frontend run build
	python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
