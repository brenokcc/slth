FROM slth-frontend
WORKDIR /project
ADD package.json .
ADD package-lock.json .
RUN npm install
RUN mkdir -p node_modules
RUN cp -r /slth node_modules/slth
ADD public public
ADD index.html .
ADD vite.config.js .
ADD run.sh .
ADD build.sh .
ADD src src
