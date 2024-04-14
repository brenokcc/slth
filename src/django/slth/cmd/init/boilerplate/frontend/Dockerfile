FROM node:20-alpine
WORKDIR /project
ADD package.json .
RUN npm install
RUN apk add curl
ADD public public
ADD index.html .
ADD vite.config.js .
ADD run.sh .
ADD build.sh .
ADD src src
