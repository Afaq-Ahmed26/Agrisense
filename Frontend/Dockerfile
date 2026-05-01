# Stage 1: Build the Vue.js application
FROM node:20-alpine as builder

WORKDIR /app

ARG VITE_API_BASE_URL
ARG VITE_API_BASE_URLS
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_API_BASE_URLS=$VITE_API_BASE_URLS

COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve the static files with Nginx
FROM nginx:stable-alpine

# Copy the built static files from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the Nginx configuration for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for Nginx
EXPOSE 80

# Command to run Nginx
CMD ["nginx", "-g", "daemon off;"]