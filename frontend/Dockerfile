FROM node:20

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}

# Install dev dependencies for hot reloading
RUN npm install -g npm@latest

# Add curl for healthcheck
RUN apt-get update && apt-get install -y curl

EXPOSE 3000

CMD ["npm", "start"]