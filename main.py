import requests
import json
import time
import asyncio
from typing import List, Union
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, executor, types

#Импорты из config.py, необходимые для работы программы
from config import TELEGRAM_TOKEN, TELEGRAM_CHANNEL_ID, VK_TOKEN, VK_PUBLIC_ID, VK_ALBUM_ID, VK_USER_ID, TELEGRAM_ADMIN_ID


# https://oauth.vk.com/authorize?client_id=51724180&redirect_url=https://oauth.vk.com/blank.html&scope=offline,wall,photos,audio&response_type=token

#Инициализация Бота
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=MemoryStorage())



# Middleware для приема несколько фото со StuckOverflow
class AlbumMiddleware(BaseMiddleware):
    """This middleware is for capturing media groups."""

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        """
        You can provide custom latency to make sure
        albums are handled properly in highload.
        """
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if not message.media_group_id:
            return
        try:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler()  # Tell aiogram to cancel handler for this group element
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: types.Message, result: dict, data: dict):
        """Clean up after handling our album."""
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]

# Функция отправки поста в ВК
def PostOnVKWall(
        token,
        owner_id,
        album_id,
        version_vk,
        image_file_names: list,
        audio_file_names: list = None,
        is_audio_here: bool = False,
        message = ""
):
    list_of_id_uploaded_photos = []
    count_of_image = len(image_file_names)
    count_of_uploaded_image = 0
    while (count_of_image != count_of_uploaded_image):
        url = "https://api.vk.com/method/photos.getUploadServer"
        response_from_getUploadServer = requests.post(
            url=url,
            params={
                'access_token': token,
                'group_id': owner_id,
                'v': version_vk,
                'album_id': album_id
            }
        )
        print(response_from_getUploadServer.json())
        url = response_from_getUploadServer.json()["response"]["upload_url"]
        files = {}
        if len(image_file_names) <= 8:
            for i in range(1, len(image_file_names)+1):
                files['file'+str(i)] = (image_file_names[i - 1], open(image_file_names[i - 1], 'rb'), 'multipart/form-data')
            count_of_uploaded_image += len(image_file_names)
            del image_file_names
        else:
            for i in range(1, 9):
                files['file'+str(i)] = (image_file_names[i - 1], open(image_file_names[i - 1], 'rb'), 'multipart/form-data')
            del image_file_names[:8]
            count_of_uploaded_image += 8
        print(files)
        response_from_UploadServer = requests.post(
            url=url,
            files=files
        )
        print(response_from_UploadServer)
        json_response_from_UploadServer = response_from_UploadServer.json()
        print(json_response_from_UploadServer)
        url = "https://api.vk.com/method/photos.save"
        response_from_photos_save = requests.post(
            url=url,
            params={
                'access_token': token,
                'v': version_vk,
                'album_id': album_id,
                'group_id': owner_id,
                'server': json_response_from_UploadServer['server'],
                'photos_list': json_response_from_UploadServer['photos_list'],
                'hash': json_response_from_UploadServer['hash']
            }
        )
        for i in range(len(response_from_photos_save.json()["response"])):
            list_of_id_uploaded_photos.append(response_from_photos_save.json()["response"][i]["id"])


    response_from_audio_save = None
    if is_audio_here:
        url = "https://api.vk.com/method/audio.getUploadServer"
        response_from_getUploadServer = requests.post(
            url=url,
            params={
                'access_token': token,
                'v': version_vk,
            }
        )
        print(response_from_getUploadServer.json())
        url = response_from_getUploadServer.json()["response"]["upload_url"]
        files = {}
        files['file'] = (audio_file_names, open(audio_file_names, 'rb'), 'multipart/form-data')
        json_response_from_UploadServer = requests.post(
            url=url,
            files=files
        ).json()
        print(json_response_from_UploadServer)
        url = "https://api.vk.com/method/audio.save"
        response_from_audio_save = requests.post(
            url=url,
            params={
                'access_token': token,
                'v': version_vk,
                'server': json_response_from_UploadServer['server'],
                'audio': json_response_from_UploadServer['audio'],
                'hash': json_response_from_UploadServer['hash']
            }
        )

    url = "https://api.vk.com/method/wall.post"
    print(response_from_photos_save)
    attachments = ''
    if is_audio_here:
        attachments = attachments+f'audio{VK_USER_ID}_{response_from_audio_save.json()["response"]["id"]}'+','
    for i in range(count_of_image):
        attachments = attachments+f'photo-{owner_id}_{list_of_id_uploaded_photos[i]}'+','
    print(attachments)
    response_from_wall_post = requests.post(
        url=url,
        params= {
            'access_token': token,
            'from_group': 1,
            'owner_id': "-"+owner_id,
            'attachments': attachments,
            'v': version_vk,
            'message': message
        }
    )
    print(attachments)
    print(response_from_wall_post.json())

# Начало работы
@dp.message_handler(commands=['start', 'info'])
async def StartCommand(message: types.Message):
    await message.reply("Возможности:\n/audio - отправка нескольких фото с музыкой\n/some_photo - отправка нескольких фото \n/one_photo - отправка одного фото\n/cancel - отменить отправку уже после введения команды")

# Прием Поста с Музыкой
class AudioForm(StatesGroup):
    audio = State()
    photo_list = State()

@dp.message_handler(commands=['audio'])
async def AudioCommand(message: types.Message):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        await AudioForm.audio.set()
        await message.reply("Отправь аудио")

@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def CanselAudio(message: types.Message, state: FSMContext):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        current_state = await state.get_state()
        if current_state is None:
            return

        await state.finish()
        await message.reply('ОК')

@dp.message_handler(state=AudioForm.audio, content_types=types.ContentType.AUDIO)
async def GetAudio(message: types.Message, state: FSMContext):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        await message.audio.download('audio.mp3')
        time.sleep(3)
        async with state.proxy() as data:
            data['audio'] = 'audio.mp3'
            data['audio_id'] = message.audio.file_id

        await AudioForm.next()
        await message.reply("Теперь отправь фото")

@dp.message_handler(content_types=types.ContentType.ANY, state=AudioForm.photo_list)
async def process_age(message: types.Message,album: List[types.Message], state: FSMContext):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        """This handler will receive a complete album of any type."""
        media_group = types.MediaGroup()
        counter = 0
        list_of_downloaded_photo = []
        caption = ""
        for obj in album:
            print(obj.content_type)
            if obj.photo:
                counter += 1
                file_id = obj.photo[-1].file_id
                caption = album[0].caption
                await obj.photo[-1].download(str(counter)+'.png')
                list_of_downloaded_photo.append(str(counter)+'.png')
            else:
                file_id = obj[obj.content_type].file_id
            try:
                # We can also add a caption to each file by specifying `"caption": "text"`
                if counter == 1:
                    media_group.attach({"media": file_id, "type": obj.content_type, "caption": caption})
                    print(caption)
                else:
                    media_group.attach({"media": file_id, "type": obj.content_type})
            except ValueError:
                return await message.answer("This type of album is not supported by aiogram.")
        await bot.send_media_group(chat_id=TELEGRAM_CHANNEL_ID, media=media_group,)
        audio_file_names = None
        audio_id = None
        async with state.proxy() as data:
            audio_file_names = data['audio']
            audio_id = data['audio_id']
        await bot.send_audio(chat_id=TELEGRAM_CHANNEL_ID, audio=audio_id)
        time.sleep(5)
        PostOnVKWall(VK_TOKEN, VK_PUBLIC_ID, VK_ALBUM_ID, "5.131", list_of_downloaded_photo, message=caption, audio_file_names=audio_file_names, is_audio_here=True)
        await state.finish()


# Прием Поста без музыки
class MediaGroupForm(StatesGroup):
    photo_list = State()
@dp.message_handler(commands=['some_photos'])
async def MediaGroupCommand(message: types.Message):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        await MediaGroupForm.photo_list.set()
        await message.reply("Отправь несколько фото")

@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def CanselSomePhoto(message: types.Message, state: FSMContext):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        current_state = await state.get_state()
        if current_state is None:
            return

        await state.finish()
        await message.reply('ОК')

@dp.message_handler(state=MediaGroupForm.photo_list, content_types=types.ContentType.ANY)
async def handle_albums(message: types.Message, album: List[types.Message], state: FSMContext):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        """This handler will receive a complete album of any type."""
        media_group = types.MediaGroup()
        counter = 0
        list_of_downloaded_photo = []
        caption = ""
        for obj in album:
            print(obj.content_type)
            if obj.photo:
                counter += 1
                file_id = obj.photo[-1].file_id
                caption = album[0].caption
                await obj.photo[-1].download(str(counter)+'.png')
                list_of_downloaded_photo.append(str(counter)+'.png')
            else:
                file_id = obj[obj.content_type].file_id
            try:
                # We can also add a caption to each file by specifying `"caption": "text"`
                if counter == 1:
                    media_group.attach({"media": file_id, "type": obj.content_type, "caption": caption})
                    print(caption)
                else:
                    media_group.attach({"media": file_id, "type": obj.content_type})
            except ValueError:
                return await message.answer("This type of album is not supported by aiogram.")
        await bot.send_media_group(chat_id=TELEGRAM_CHANNEL_ID, media=media_group,)
        time.sleep(5)
        PostOnVKWall(VK_TOKEN, VK_PUBLIC_ID, VK_ALBUM_ID, "5.131", list_of_downloaded_photo, message=caption)
        await state.finish()

#Прием поста с одним фото
class OnePhotoForm(StatesGroup):
    one_photo = State()

@dp.message_handler(commands=['one_photo'])
async def OnePhotoCommand(message: types.Message):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        await OnePhotoForm.one_photo.set()
        await message.reply("Отправь фото")

@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def CanselOnePhoto(message: types.Message, state: FSMContext):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        current_state = await state.get_state()
        if current_state is None:
            return

        await state.finish()
        await message.reply('ОК')

@dp.message_handler(state=OnePhotoForm.one_photo, content_types=types.ContentType.PHOTO)
async def OnePhoto(message: types.Message, state:FSMContext):
    if message.from_user.id == TELEGRAM_ADMIN_ID:
        await bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID, photo=message.photo[-1].file_id, caption=message.caption)
        print(message.caption)
        await message.photo[-1].download('1.png')
        time.sleep(1.5)
        list = ['1.png']
        PostOnVKWall(VK_TOKEN, VK_PUBLIC_ID, VK_ALBUM_ID, "5.131", list, message=message.caption)
        await state.finish()



#main
if __name__ == '__main__':
    dp.middleware.setup(AlbumMiddleware())
    executor.start_polling(dp, skip_updates=True)
