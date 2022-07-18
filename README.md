# Проект "Yatube"

## Описание:
Cоциальная сеть для публикации личных дневников.
Сервис позволяет:
-   регистрироваться, восстанавливать пароль по почте;
-   создавать личную страницу, для публикации записей;
-   создавать и редактировать свои записи;
-   просматривать страницы других авторов;
-   комментировать записи других авторов;
-   подписываться на авторов;
-   записи можно отправлять в определённую группу;
-   модерация записей, работа с пользователями, создание групп осуществляется через панель администратора;

## Развертывание:
### Запуск веб-сервера::
- Склонируйте проект на Ваш компьютер 
```sh 
git clone https://github.com/DenisShahbazyan/hw05_final.git
``` 
- Перейдите в папку с проектом 
```sh 
cd hw05_final
``` 
- Создайте и активируйте виртуальное окружение 
```sh 
python -m venv venv 
source venv/Scripts/activate 
``` 
- Обновите менеджер пакетов (pip) 
```sh 
pip install --upgrade pip 
``` 
- Установите необходимые зависимости 
```sh 
pip install -r requirements.txt
``` 
- Создайте миграции
```sh
python ./yatube/manage.py makemigrations
python ./yatube/manage.py migrate
```
- Создайте суперпользователя 
```sh
python ./yatube/manage.py createsuperuser
```
- Запуск сервера
```sh
python ./yatube/manage.py runserver
```
- Сайт запуститься по адресу http://127.0.0.1:8000

## Системные требования:
- [Python](https://www.python.org/) 3.10.4

## Планы по доработке:
>Проект сделан в учебных целях, доработка не планируется.

## Используемые технологии:
- [Django](https://www.djangoproject.com/) 3.2.3
- [Pillow](https://pillow.readthedocs.io/en/stable/) 9.2.0
- [sorl-thumbnail](https://pypi.org/project/sorl-thumbnail/) 12.7.0
- [django-debug-toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/) 3.2.4

## Авторы:
- [Denis Shahbazyan](https://github.com/DenisShahbazyan)

## Лицензия:
- MIT