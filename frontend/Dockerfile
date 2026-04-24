# syntax=docker/dockerfile:1.7

# ---------- Stage 1: build ----------
# D-05: node:20-alpine is small and has full npm toolchain for Vite 8 + React 19.
FROM node:20-alpine AS build

WORKDIR /build

# Copy manifest first so `npm ci` is cached when source changes but deps don't.
COPY package.json package-lock.json* ./
# Use `npm ci` if lockfile exists, fall back to `npm install` otherwise.
# (package-lock.json is expected; the `|| npm install` is a safety net for
# first-time builds before the lockfile is committed.)
RUN npm ci || npm install

# Copy sources and build to dist/.
COPY . .
RUN npm run build

# ---------- Stage 2: serve ----------
# D-05: nginx:alpine serves static dist/ output; tiny image.
FROM nginx:alpine

# D-06: custom nginx config replicates the Vite dev proxy rewrite.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the build output from stage 1 into nginx's default doc root.
COPY --from=build /build/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
