FROM node:20 AS build

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

ARG REACT_APP_BACKEND_IP
ARG REACT_APP_BACKEND_PORT
ENV REACT_APP_BACKEND_IP=${REACT_APP_BACKEND_IP}
ENV REACT_APP_BACKEND_PORT=${REACT_APP_BACKEND_PORT}

RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY --from=build /app/build ./build

CMD ["npx", "serve", "-s", "build", "-l", "3000"]