# 🚀 Развёртывание на VPS (5.35.92.70) с доменом tenhens.ru

## 📋 Предварительные требования

1. **VPS сервер** с IP `5.35.92.70`
2. **Домен** `tenhens.ru` с настроенными DNS:
   - A-запись: `tenhens.ru` → `5.35.92.70`
   - A-запись: `www.tenhens.ru` → `5.35.92.70`
3. **Docker и Docker Compose** установлены на сервере
4. **Открытые порты**: 80 (HTTP), 443 (HTTPS), 22 (SSH)

---

## 🔧 Шаг 1: Подготовка сервера

### Подключитесь к серверу по SSH:
```bash
ssh root@5.35.92.70
```

### Обновите систему и установите Docker:
```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose curl git
systemctl enable docker
systemctl start docker
```

### Проверьте установку:
```bash
docker --version
docker-compose --version
```

---

## 🔧 Шаг 2: Настройка проекта на сервере

### Создайте директорию для приложения:
```bash
mkdir -p /opt/tenhens
cd /opt/tenhens
```

### Создайте файл `.env` с секретным ключом:
```bash
cat > .env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF
```

### Скопируйте файлы проекта на сервер:

**Вариант A: Через git clone (если проект в репозитории):**
```bash
git clone <ваш-репозиторий> .
```

**Вариант B: Через scp с локальной машины:**
```bash
# С локальной машины выполните:
scp -r /workspace/* root@5.35.92.70:/opt/tenhens/
```

---

## 🔧 Шаг 3: Настройка Nginx и SSL

### Обновите конфигурацию Nginx для работы с fullstack-приложением:

Создайте файл `/opt/tenhens/nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl;
    server_name tenhens.ru www.tenhens.ru;

    ssl_certificate /etc/letsencrypt/live/tenhens.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tenhens.ru/privkey.pem;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;

    location / {
        proxy_pass http://fullstack:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Для WebSocket (если понадобится)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

server {
    listen 80;
    server_name tenhens.ru www.tenhens.ru;
    
    # Перенаправление на HTTPS
    return 301 https://$host$request_uri;
}
```

### Создайте docker-compose.prod.yml для продакшена:

```bash
cat > docker-compose.prod.yml << 'EOF'
version: "3.8"

services:
  fullstack:
    build: ./fullstack
    env_file: .env
    volumes:
      - egg_data:/app/data
    restart: unless-stopped
    networks:
      - app-network

  nginx:
    build: ./nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - letsencrypt:/etc/letsencrypt
    depends_on:
      - fullstack
    restart: unless-stopped
    networks:
      - app-network

volumes:
  egg_data:
  letsencrypt:

networks:
  app-network:
    driver: bridge
EOF
```

---

## 🔧 Шаг 4: Получение SSL сертификата (Let's Encrypt)

### Установите Certbot:
```bash
apt install -y certbot
```

### Остановите контейнеры (если запущены):
```bash
docker-compose -f docker-compose.prod.yml down
```

### Получите сертификат (standalone mode):
```bash
certbot certonly --standalone \
  -d tenhens.ru \
  -d www.tenhens.ru \
  --email admin@tenhens.ru \
  --agree-tos \
  --non-interactive
```

### Или используйте webroot (если на порту 80 уже что-то работает):
```bash
mkdir -p /var/www/certbot
certbot certonly --webroot \
  -w /var/www/certbot \
  -d tenhens.ru \
  -d www.tenhens.ru \
  --email admin@tenhens.ru \
  --agree-tos \
  --non-interactive
```

### Проверьте, что сертификаты созданы:
```bash
ls -la /etc/letsencrypt/live/tenhens.ru/
```

---

## 🔧 Шаг 5: Запуск приложения

### Соберите и запустите контейнеры:
```bash
cd /opt/tenhens
docker-compose -f docker-compose.prod.yml up -d --build
```

### Проверьте статус:
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Посмотрите логи:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🔧 Шаг 6: Автоматическое обновление SSL сертификатов

### Создайте скрипт для обновления:
```bash
cat > /usr/local/bin/renew-cert.sh << 'EOF'
#!/bin/bash
certbot renew --quiet
docker-compose -f /opt/tenhens/docker-compose.prod.yml restart nginx
EOF

chmod +x /usr/local/bin/renew-cert.sh
```

### Добавьте задачу в crontab:
```bash
crontab -e
```

Добавьте строку (обновление каждый день в 3:00):
```
0 3 * * * /usr/local/bin/renew-cert.sh
```

---

## 🔧 Шаг 7: Проверка работы

### Проверьте доступность сайта:
```bash
curl -I https://tenhens.ru
curl -I https://www.tenhens.ru
```

### Проверьте редирект HTTP → HTTPS:
```bash
curl -I http://tenhens.ru
```

### Откройте в браузере:
- https://tenhens.ru
- https://www.tenhens.ru

---

## 🛠 Управление приложением

### Просмотр логов:
```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Только backend
docker-compose -f docker-compose.prod.yml logs -f fullstack

# Только nginx
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Перезапуск:
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Остановка:
```bash
docker-compose -f docker-compose.prod.yml down
```

### Обновление приложения:
```bash
cd /opt/tenhens
git pull  # если используете git
docker-compose -f docker-compose.prod.yml up -d --build
```

### Резервное копирование базы данных:
```bash
# Найдите volume с базой данных
docker volume ls | grep egg_data

# Скопируйте базу данных
docker run --rm \
  -v tenhens_egg_data:/source \
  -v $(pwd):/backup \
  alpine tar czf /backup/egg_database_backup.tar.gz -C /source .
```

### Восстановление из резервной копии:
```bash
docker run --rm \
  -v tenhens_egg_data:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/egg_database_backup.tar.gz -C /target
```

---

## 🔒 Безопасность

### Настройте фаервол (UFW):
```bash
apt install -y ufw
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
ufw status
```

### Создайте обычного пользователя (не root):
```bash
adduser deploy
usermod -aG docker deploy
```

### Настройте SSH ключи (отключите парольный вход):
```bash
# На локальной машине:
ssh-copy-id root@5.35.92.70

# На сервере отредактируйте /etc/ssh/sshd_config:
PasswordAuthentication no
PermitRootLogin prohibit-password

# Перезапустите SSH:
systemctl restart sshd
```

---

## 📊 Мониторинг

### Установите htop и netstat:
```bash
apt install -y htop net-tools
```

### Проверьте использование ресурсов:
```bash
docker stats
htop
```

### Проверьте открытые порты:
```bash
netstat -tulpn
```

---

## ❗ Решение проблем

### Контейнер не запускается:
```bash
docker-compose -f docker-compose.prod.yml logs fullstack
```

### Ошибка SSL:
```bash
# Проверьте права доступа к сертификатам
ls -la /etc/letsencrypt/live/tenhens.ru/

# Пересоздайте сертификат
certbot delete --cert-name tenhens.ru
certbot certonly --standalone -d tenhens.ru -d www.tenhens.ru
```

### Приложение недоступно:
```bash
# Проверьте, что контейнеры работают
docker-compose -f docker-compose.prod.yml ps

# Проверьте сеть
docker network inspect tenhens_app-network

# Проверьте логи nginx
docker-compose -f docker-compose.prod.yml logs nginx
```

### Сброс пароля пользователя:
```bash
# Подключитесь к базе данных
docker exec -it tenhens-fullstack-1 sqlite3 /app/data/egg_database.db

# Обновите пароль (хэш от "newpassword123")
UPDATE users SET password='ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f' WHERE username='your_username';

# Выйдите из SQLite
.exit
```

---

## 📞 Контакты

Если возникли проблемы:
1. Проверьте логи: `docker-compose -f docker-compose.prod.yml logs -f`
2. Проверьте сертификаты: `certbot certificates`
3. Проверьте DNS: `dig tenhens.ru`

---

## 🎉 Готово!

Ваш сервис доступен по адресу:
- **https://tenhens.ru**
- **https://www.tenhens.ru**

Теперь вы можете регистрировать новых пользователей без зависимости от Telegram!
