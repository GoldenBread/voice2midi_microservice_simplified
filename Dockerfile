FROM python:2

ENV APP_ENV prodution

WORKDIR /app

# numpy required for the installation of vamp
RUN python -m pip install numpy
RUN python -m pip install librosa soundfile resampy vamp midiutil jams scipy

RUN apt update && apt install ruby libfftw3-dev libsndfile1-dev libao-dev libsamplerate0-dev libncurses5-dev -y

COPY Gemfile .
COPY Gemfile.lock .
RUN gem install bundler
RUN bundle install

COPY . .

# install melodia vamp library
RUN mkdir /usr/local/lib/vamp
RUN mv /app/melodia-vamp/* /usr/local/lib/vamp

EXPOSE 5000
CMD ["ruby", "main.rb"]