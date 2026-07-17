FROM composer:2 AS dependencies
WORKDIR /app
COPY apps/api/composer.json apps/api/composer.lock ./
RUN composer install --no-dev --no-interaction --no-scripts --prefer-dist --optimize-autoloader

FROM php:8.4-cli-alpine
WORKDIR /app
RUN apk add --no-cache postgresql-dev $PHPIZE_DEPS \
    && docker-php-ext-install pdo_pgsql \
    && apk del $PHPIZE_DEPS
COPY apps/api ./
COPY --from=dependencies /app/vendor ./vendor
RUN mkdir -p storage/framework/cache storage/framework/sessions storage/framework/views storage/logs \
    && chown -R www-data:www-data storage bootstrap/cache
USER www-data
EXPOSE 8080
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8080"]
