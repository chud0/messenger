# messenger
This is the homework on the platform: geekbrains.ru

Server
======
Файл sever.py, необязательные ключи -p и -a задают порт и адрес для прослушивания, по умолчанию 7777 и "".
Пример запуска:

    python3 server.py -p 8888

Недоработки:
* Куча всего

Client
======
Файл client.py, обязательный ключ -l, необязательные -p и -a; логин, порт и хост соответственно.
Порт и хост по умолчанию 7777 и "localhost".
Пример запуска:

    python3 client.py -l chud0
После запуска можно отправлять команды: добавление/удаление контактов, получение списка контактов.
Для отправки сообщения нужно выбрать кому посылать набрав "<<" и через пробел логин, пример:

    << usr1
приглашение для ввода изменится на "      usr1<<" (если не очень то изменилось понажимайте Enter).
Для смены юзера нужно набрать ">>". Косяки с отображением есть, можно "промотать" Enter -ом.

Клиент сделан на потоках, которые работают в while True, общение потоков через очереди.

Client GUI
==========
Файл gui_app_client.py
![](client_gui.jpg)

* 1 - Выбор контакта из контакт листа, поле присланных/полученных сообщений соответственно меняется.
* 2 - Поле для ввода сообщения и логина юзера при добавлении контакта.
* 3 - Кнопка для отправки сообщения, так же отправляет Enter в поле 2.
* 4 - При получении входящего сообщения иконка в контакт листе изменяется (пока не будет прочтен).
* 5 - Добавление контакта в контакт лист, предварительно набрать логин в поле 2.
* 6 - Удаление контакта, предварительно выбрать в контакт листе.

Методы из консольного клиента + прикручен поток, который читает очередь вывода и через сигнал передает на печать.

Недоработки:
* Проверок нет, падает при каждом неосторожном действии (добавление/удаление несуществующих юзверей, ...).
* Логин юзера в коде


Код запускал на Ubuntu и MacOS, в Windows не пробовал.

Конструктивная критика приветствуется)

Ник в Telegram: chud0
