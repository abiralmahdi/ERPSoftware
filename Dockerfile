FROM python:3.11-slim

WORKDIR /app

# Install git (and optionally gcc and build-essential for other dependencies)
RUN apt-get update && apt-get install -y git

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:9876"]
