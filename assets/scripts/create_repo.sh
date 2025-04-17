#!/bin/bash

# Параметры
REPO_NAME="neurorat"
DESCRIPTION="Продвинутый RAT с интеграцией LLM для автономной работы"
PRIVATE=false

# Запрос токена
echo "Для создания репозитория на GitHub необходим персональный токен доступа."
echo "Вы можете создать его здесь: https://github.com/settings/tokens"
echo "Токен должен иметь разрешение 'repo' для создания репозитория."
echo -n "Введите ваш токен доступа: "
read -s TOKEN
echo ""

# Создаем JSON для запроса
JSON="{\"name\":\"$REPO_NAME\",\"description\":\"$DESCRIPTION\",\"private\":$PRIVATE}"

# Отправляем запрос
echo "Создание репозитория $REPO_NAME..."
RESPONSE=$(curl -s -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: token $TOKEN" \
  -d "$JSON" \
  https://api.github.com/user/repos)

# Проверяем результат
if echo "$RESPONSE" | grep -q "html_url"; then
  REPO_URL=$(echo "$RESPONSE" | grep -o '"html_url": *"[^"]*"' | grep -o 'https://[^"]*')
  echo "Репозиторий успешно создан: $REPO_URL"
  
  # Настраиваем локальный репозиторий
  echo "Настройка локального репозитория..."
  git remote add origin "${REPO_URL}.git"
  git branch -M main
  
  echo "Теперь вы можете загрузить код командой: git push -u origin main"
else
  echo "Ошибка при создании репозитория:"
  echo "$RESPONSE"
fi 