# ── Stage 1: build with Vite ─────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

# Copy lockfile + package.json together so cache invalidates correctly
COPY package.json package-lock.json ./
RUN npm ci --silent

COPY . .
RUN npm run build

# ── Stage 2: serve with nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
