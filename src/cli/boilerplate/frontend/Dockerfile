FROM node:20-alpine
WORKDIR /project
ADD package.json .
ADD package-lock.json .
RUN npm install
ADD public public
ADD index.html .
ADD vite.config.js .
ADD run.sh .
ADD build.sh .
ADD src src
