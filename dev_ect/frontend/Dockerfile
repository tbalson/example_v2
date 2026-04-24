FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 1. Upgrade core build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 2. Pre-install a safe version of numpy BEFORE the requirements file
RUN pip install --no-cache-dir "numpy<2.0.0"

# 3. Now install everything else
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]