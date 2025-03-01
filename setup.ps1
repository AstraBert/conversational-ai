docker compose up qdrant postgres adminer -d

conda env create -f environment.yml

conda activate conversational-agent

python3 .\scripts\cache.py

Set-Location .\scripts\

uvicorn main:app --host 0.0.0.0 --port 8000

conda deactivate