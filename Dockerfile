# 
FROM python:3.9

# 
WORKDIR /app

# 
COPY ./requirements.txt /app/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 
COPY . /app

#
RUN mkdir -p service_accounts

#
EXPOSE 8080

# 
CMD ["fastapi", "run", "--port", "8080"]
