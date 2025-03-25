 #!/bin/bash

# Проверяем существование виртуального окружения
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run build.sh first to set up the environment."
    exit 1
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем бота
echo "Starting K-89 Coffee Bot..."
python bot.py