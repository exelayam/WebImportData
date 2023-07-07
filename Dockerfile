FROM python:latest
WORKDIR /WebImportData
COPY . /WebImportData
RUN pip install sqlite3
RUN pip install -r requirements.txt
EXPOSE 80
CMD ["python", "main.py"]