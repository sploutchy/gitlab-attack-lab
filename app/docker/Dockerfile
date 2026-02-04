FROM php:8.3-cli

RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Copy files
COPY . .

# Ensure entrypoint is executable
RUN chmod +x /app/docker/entrypoint.sh

# Install PHP dependencies (skip scripts to avoid artisan during build)
RUN composer install --no-dev --optimize-autoloader --no-scripts

# Install Node dependencies and build assets
RUN npm install && npm run build

# Create necessary directories
RUN mkdir -p storage/logs bootstrap/cache

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["php", "-S", "0.0.0.0:8000", "-t", "public"]
