FROM node:20 AS build

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}

RUN npm run build

FROM node:20-alpine

RUN apk add --no-cache curl

WORKDIR /app

COPY --from=build /app/build ./build

CMD ["npx", "serve", "-s", "build", "-l", "3000"]