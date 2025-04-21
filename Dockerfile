FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir gunicorn
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY mcp_server.py /app/
COPY mcp_tools.py /app/
COPY brave_api.py /app/
COPY page_loader.py /app/
COPY llm.py /app/


EXPOSE 5000

CMD ["python3", "mcp_server.py"]
