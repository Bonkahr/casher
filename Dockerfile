# 
FROM python:3.10

# 
WORKDIR /casher

# 
COPY ./requirements.txt /casher/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /casher/requirements.txt

# 
COPY ./app /casher/app

# 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
