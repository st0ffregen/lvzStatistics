FROM python:3.9.9
ARG APP_ENVIRONMENT
COPY . /usr/src/api
RUN python -m pip install --upgrade pip
RUN pip install -r /usr/src/api/requirements.txt
WORKDIR /usr/src/api/
CMD if [ ${APP_ENVIRONMENT} = "development" ] ; \
then \
    python run.py ; \
    else python -c 'print("running in production")' ; \
    gunicorn -w 4 -b api:5000 run:app ; \
fi