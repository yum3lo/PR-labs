# minimal python environment
FROM python:3.12-slim 

WORKDIR /app

COPY requirements.txt .

# --no-cache-dir - not cache the downloaded packages
# reduces the image size as cached files are not stored in the container
RUN pip install --no-cache-dir -r requirements.txt

# copy the current directory contents into the container at /app
COPY . .

CMD ["python", "webserver.py"]