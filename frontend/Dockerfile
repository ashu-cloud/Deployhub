FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

ENV AUTH_SERVICE_URL=http://auth-service:8001
ENV PROJECT_SERVICE_URL=http://project-service:8002
ENV DEPLOYMENT_SERVICE_URL=http://deployment-service:8006

CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]
