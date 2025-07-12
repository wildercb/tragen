# Frontend Dockerfile for NQ Trading Agent
FROM node:18-alpine

# Add curl for health checks
RUN apk add --no-cache curl

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# For development, use the dev server
CMD ["npm", "start"]