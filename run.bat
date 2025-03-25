 @echo off

REM Проверяем существование виртуального окружения
if not exist venv (
    echo Error: Virtual environment not found!
    echo Please run build.bat first to set up the environment.
    exit /b 1
)

REM Активируем виртуальное окружение
call venv\Scripts\activate

REM Запускаем бота
echo Starting K-89 Coffee Bot...
python bot.py