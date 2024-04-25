FROM node:20-alpine
RUN apk add curl nginx vim
WORKDIR /opt/deploy
ADD package.json .
RUN npm install
ADD public public
ADD index.html .
ADD vite.config.js .
ADD run.sh .
ADD src src
ARG VERSION
ARG VITE_API_URL
RUN echo $VITE_API_URL
RUN rm -f dist/*
RUN npm install slth
RUN npm run build