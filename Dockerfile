FROM python:3.11-slim

# installs git and git-lfs
RUN apt-get update && apt-get install -y git git-lfs curl build-essential python3-dev
RUN git lfs install

WORKDIR /app

# github token for private repository LFS usage
ARG GITHUB_TOKEN

# clones the repository using Railway token
RUN --mount=type=secret,id=GITHUB_TOKEN \
    git clone https://oauth2:$(cat /run/secrets/GITHUB_TOKEN)@github.com/wiktorzakmateusz/movie-friend-backend.git .

# pulls LFS files
RUN git lfs pull

# installs dependecies
RUN pip install -r requirements.txt

# compiles cython
RUN cd ml/models_code && python setup.py build_ext --inplace

# starts fast api server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]