FROM node:20-alpine
WORKDIR /project
ADD package.json .
RUN sed 15d package.json && npm install http://host.docker.internal:9999/slth-0.0.3.tgz?v=2
RUN npm install
RUN apk add curl
ADD public public
ADD index.html .
ADD vite.config.js .
ADD run.sh .
ADD build.sh .
ADD src src
