# Используем официальный образ Node.js
FROM node:16 AS build

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходный код
COPY . .

# Собираем приложение
RUN npm run build

# Используем Nginx для обслуживания статических файлов
FROM nginx:alpine

# Копируем собранное приложение
COPY --from=build /app/build /usr/share/nginx/html

# Копируем конфигурацию Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт
EXPOSE 80

# Команда для запуска
CMD ["nginx", "-g", "daemon off;"]