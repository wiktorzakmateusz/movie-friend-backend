FROM python:3.11-slim

# installs git and git-lfs
RUN apt-get update && apt-get install -y git git-lfs curl
RUN git lfs install

WORKDIR /app

# github token for private repository LFS usage
ARG GITHUB_TOKEN

# clones the repository
RUN git clone https://oauth2:${GITHUB_TOKEN}@github.com/wiktorzakmateusz/movie-friend-backend.git .

# pulls LFS files
RUN git lfs pull

# compiles cython
RUN cd ml/models_code && python setup.py build_ext --inplace

# installs dependecies
RUN pip install -r requirements.txt

# starts fast api server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]