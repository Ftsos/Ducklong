# Base image with Node.js and necessary tools
FROM node:18-alpine as base
RUN apk add --no-cache g++ make py3-pip libc6-compat wget bash
RUN npm install -g pnpm
RUN apk add --no-cache libc6-compat
RUN apk update

ENV PATH="/root/.local/share/pnpm:/root/.local/share/pnpm/global/5/node_modules/.bin:$PATH"
ENV PNPM_HOME=/app/.pnpm
ENV PATH=$PNPM_HOME:$PATH

WORKDIR /app

COPY package*.json ./
EXPOSE 3000
EXPOSE 5328

# Install Python dependencies
COPY requirements.txt ./api/
RUN pip install --no-cache-dir -r api/requirements.txt --break-system-packages
RUN pip install gunicorn --break-system-packages

# Build stage for Node.js app
FROM base as builder
WORKDIR /app
COPY . .
RUN npm run build

# Production stage for Node.js and Flask apps
FROM base as production
WORKDIR /app
ENV NODE_ENV=production
RUN npm ci
RUN pnpm install --frozen-lockfile --prod

RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
COPY --from=builder /app/api ./api

# Start both Node.js and Flask apps in production
CMD ["sh", "-c", "npm start & gunicorn --preload --reload -b 0.0.0.0:5328 --log-level info --access-logfile - --error-logfile - --chdir /app/api index:app"]

# Development stage for Node.js and Flask apps
FROM base as dev
WORKDIR /app
ENV NODE_ENV=development
RUN npm install
COPY . .

# Start both Node.js and Flask apps in development
CMD ["sh", "-c", "npm run next-dev & gunicorn --preload  --reload -b 0.0.0.0:5328 --log-level info --access-logfile - --error-logfile - --chdir /app/api index:app"]
