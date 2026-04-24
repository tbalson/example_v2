FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the heavy SpaCy model directly via pip to avoid URL resolution errors
RUN pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1.tar.gz

COPY . .

EXPOSE 5000

# Boot the Gunicorn server
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:5000", "app:connexion_app"]