# Immagine di sviluppo (dev server Vite con hot reload). Per una build di
# produzione, questo Dockerfile non è pensato per il deploy — vedi README
# per lo scope di questa fase (solo uso locale via docker-compose).
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
