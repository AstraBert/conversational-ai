FROM condaforge/miniforge3

WORKDIR /app/
COPY ./shell /app/shell/
COPY environment.yml /app/
COPY docker/*.py /app/

RUN bash /app/shell/conda_env.sh 

CMD ["bash", "/app/shell/run.sh"]
