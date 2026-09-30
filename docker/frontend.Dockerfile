FROM node:24-alpine AS dependencies
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:24-alpine AS builder
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY frontend/ ./
# NEXT_PUBLIC_* values are compiled into the browser bundle, so this is a build argument
# and not a runtime variable. The default is the same-origin proxy path, because a hosted
# build must not point the browser at the backend directly, and because Render cannot
# pass build arguments to a Docker build. docker-compose.yml overrides it with
# http://localhost:8000 for the local demo.
ARG NEXT_PUBLIC_API_URL=/api/backend
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=dependencies /app/node_modules ./node_modules

EXPOSE 3000

# Bind $PORT when the host assigns one, which Render does, otherwise the Compose port.
CMD ["sh", "-c", "./node_modules/.bin/next start --port ${PORT:-3000}"]
