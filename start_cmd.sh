#!/bin/sh

install() {
    docker build . -t microservice-voice2midi
    start
}

start() {
    docker run -it -p 5000:5000 --hostname localhost microservice-voice2midi
}

case "$1" in
    "install") install;;
    "start") start;;
    *) echo -e "Usage: $0 COMMAND\n\nCommands:\n  install\n  start\n"
esac
