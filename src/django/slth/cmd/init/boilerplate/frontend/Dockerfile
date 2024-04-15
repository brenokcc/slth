FROM node:20-alpine
RUN apk add curl nginx
WORKDIR /project
ADD package.json .
RUN npm install
ADD public public
ADD index.html .
ADD vite.config.js .
ADD run.sh .
ADD build.sh .
ADD src src
