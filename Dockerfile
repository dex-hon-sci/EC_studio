FROM python:3.11-slim

WORKDIR /home/dexter/Euler_Capital_codes/EC_studio/app

COPY requirements.txt .
COPY EC_API .
COPY web_app.py ./
COPY web_riskmonitor.py ./
COPY test_script.py ./
COPY log .

RUN pip install --no-cache-dir -r requirements.txt

# Enable Flask debug mode
ENV FLASK_DEBUG=1
#ENV PYTHONPATH="${PYTHONPATH}:/home/dexter/Euler_Capital_codes/EC_studio"


EXPOSE 7000

#CMD ["python", "web_riskmonitor.py"]
CMD ["python", "test_script.py"]
#CMD ["python", "web_app.py"]

