FROM python:2

ENV APP_ENV prodution

WORKDIR /app

RUN python -m pip install flask

# numpy required for the installation of vamp
RUN python -m pip install numpy
RUN python -m pip install librosa soundfile resampy vamp midiutil jams scipy

COPY . .

# install melodia vamp library
RUN mkdir /usr/local/lib/vamp
RUN mv /app/melodia-vamp/* /usr/local/lib/vamp

RUN mkdir /app/upload

EXPOSE 5000
ENTRYPOINT FLASK_APP=/app/interface_flask/interface.py flask run --host=0.0.0.0 --port=5000