FROM node:20

WORKDIR /app


COPY ./package.json ./
COPY ./.env ./
COPY ./electron.js ./
COPY ./yarn.lock ./
COPY ./public ./public
COPY ./src ./src

RUN yarn install

EXPOSE 3000

CMD ["yarn", "start"]