eval "$(conda shell.bash hook)"

conda activate conversational-agent
cd /app/
python3 cache.py
uvicorn main:app --host 0.0.0.0 --port 8000
conda deactivate
