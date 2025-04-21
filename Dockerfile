FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir gunicorn

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src .


EXPOSE 5000

CMD ["python3", "mcp_server.py"]
