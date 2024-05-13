FROM node:20 AS build

RUN apt-get update && apt-get install -y curl

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}

RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY --from=build /app/build ./build

CMD ["npx", "serve", "-s", "build", "-l", "3000"]