# Бот Автопостер в ваш Telegram канал и VK Группу на Python

Содержит в себе **Main.py** с исходным кодом

Для функционирования требуются следующие библиотеки: **Aiogram**, **Requests**

Настройка:  
1. Установите все необходимые библиотеки  
2. Создайте config.py файл, в котором создайте следующие поля:  
  * TELEGRAM_TOKEN(str) - получается от BotFather при создании бота (так же его требуется добавить администратором в ваш ТГ канал)  
  * TELEGRAM_CHANNEL_ID(int) - Число, **НЕ СТРОКА** с минусом на начале, можно узнать переслав любой пост специализированным ботам
  * VK_TOKEN(str) - Для получения его требуется создать Standalone приложение в ВК, запустить его и получить его ID, после чего вставить в эту ссылку заместо жирного **ID_HERE**  
  https[]()://oauth.vk.com/authorize?client_id=**ID_HERE**&redirect_url=https://oauth.vk.com/blank.html&scope=offline,wall,photos,audio&response_type=token  
  Вставить эту ссылку в ваш бразуер где вы вошли в ваш аккаунт ВК (Спросит разрешения и вернет вместо этой ссылки URI с токеном)
  После чего скопировать токен после **access_token=** и до **&expires_in=** (не включая их)
  * VK_PUBLIC_ID(str) - ID паблика в вк, без минуса
  * VK_USER_ID(str) - ID страницы в вк
  * VK_ALBUM_ID(str) - ID альбома вашей группы в которую нужно отправлять посты
  * TELEGRAM_ADMIN_ID - ID Аккаунта, с которого будет происходить постинг(будет происходить проверка для безопасности)  
3. Запустите main.py  

Возможности:  
1. Пост Одного фото **/one_photo**
2. Пост Группы фото до 10 **/some_photos**
3. Пост Группы фото с одним музыкальным треком **/audio**

Все почти все действия логируются в консоль для отладки, aiogram выкидывает свои исключения при ошибках
