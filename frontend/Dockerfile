FROM node:20 AS build

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY --from=build /app/build ./build

CMD ["npx", "serve", "-s", "build", "-l", "3000"]