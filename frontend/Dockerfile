FROM node:20 AS build

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json files to the working directory
COPY package*.json ./

# Install the frontend dependencies
RUN npm ci

# Copy the frontend code to the working directory
COPY . .

# Build the React app
RUN npm run build

# Use a lightweight web server to serve the built files
FROM nginx:stable-alpine

# Copy the built files from the previous stage to the Nginx HTML directory
COPY --from=build /app/build /usr/share/nginx/html

# Copy the Nginx configuration file to the appropriate location
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose the port on which the frontend will be served
EXPOSE 80

# Start the Nginx server
CMD ["nginx", "-g", "daemon off;"]