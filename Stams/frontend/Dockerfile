# Use Node.js for building
FROM node:18-slim

# Set working directory
WORKDIR /app

# Copy package files and install
COPY package.json ./
RUN npm install

# Copy the rest of the code
COPY . .

# Expose Vite dev port
EXPOSE 5173

# Run Vite dev server
CMD ["npm", "run", "dev", "--", "--host"]
