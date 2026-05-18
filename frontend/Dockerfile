# Stage 1: Build
FROM node:20-alpine as build-stage

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:stable-alpine as production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html

# Use a shell script to dynamically set the port in nginx config
CMD ["sh", "-c", "sed -i 's/listen  80;/listen '\"${PORT:-80}\"';/g' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
