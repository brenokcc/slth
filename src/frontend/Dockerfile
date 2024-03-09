FROM node:18-alpine
WORKDIR /opt/app
ADD package.json .
RUN npm install
ADD public public
ADD index.html .
ADD vite.config.js .
ADD run.sh .
ADD build.sh .
ADD src src
