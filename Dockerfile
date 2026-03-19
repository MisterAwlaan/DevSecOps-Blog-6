FROM python:3.12-slim 

WORKDIR /app 

COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt 

COPY . . 

# Exposition du port 5000
EXPOSE 5000 

# Lancement direct de l'application via python
# Cela permet de respecter ton bloc "if __name__ == '__main__':"
CMD ["python", "app.py"]