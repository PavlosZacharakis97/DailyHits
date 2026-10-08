# syntax=docker/dockerfile:1

# ---- dev: Vite dev server; source is bind-mounted by docker-compose.yml ----
FROM node:24-alpine AS dev
WORKDIR /app
RUN chown node:node /app
USER node
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci
COPY --chown=node:node . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
