FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Set API URL at build time for Next.js rewrites
ENV INTERNAL_API_URL=http://api:8000
ENV NEXT_PUBLIC_API_URL=http://api:8000

RUN npm run build

EXPOSE 3000

ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "start"]
