FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=8080 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 10001 cymbal && \
    adduser --system --uid 10001 cymbal

COPY --from=builder /app/public ./public
COPY --from=builder --chown=cymbal:cymbal /app/.next/standalone ./
COPY --from=builder --chown=cymbal:cymbal /app/.next/static ./.next/static

USER cymbal
EXPOSE 8080

CMD ["node", "server.js"]
