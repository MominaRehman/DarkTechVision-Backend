FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y tor && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p models uploads/text uploads/images uploads/onion_images tor/data

EXPOSE 8000

CMD ["python", "run.py"]