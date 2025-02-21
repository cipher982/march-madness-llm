FROM node:20

WORKDIR /app

# Copy package files first
COPY package*.json ./
COPY package-lock.json* ./

# Use cache mount for npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY . .

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}

# Install dev dependencies for hot reloading
RUN npm install -g npm@latest

# Add curl for healthcheck
RUN apt-get update && apt-get install -y curl

EXPOSE 3000

CMD ["npm", "start"]