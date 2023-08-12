import os
import uuid

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiogram.utils.markdown as fmt
from aiogram.types import InputFile, ParseMode

import db, keyboard
from aiogram.dispatcher import FSMContext
from fsm import Users, Application, Update
import re


API_TOKEN = '5998330752:AAGS3LqbrL0rMO4Pgw3V-T-tpE_0fzq5N2c'

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
tmp = {}


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message, state: FSMContext):
    exist_user = db.check_existing(message.chat.id)
    if not exist_user:
        await message.answer(
            fmt.hbold('☀Доброго времени суток') + ', бот создан, чтобы обрабатывать заявки и обращения пользователей. '
                     'Чтобы воспользоваться этим, пришлите для начала Ваше ' + fmt.hbold('Имя') + ' и ' + fmt.hbold('Фамилию'))
        user_id = message.from_user.id
        await Users.Name.set()
    else:
       await message.answer(fmt.hbold('✈Добро пожаловать ') + fmt.hitalic('в главное меню чат-бота Управляющей компании "УЭР-ЮГ"') +
                            '. Здесь Вы можете оставить заявку для управляющей компании или направить свое предложение по управлению домом. Просто воспользуйтесь кнопками '
                            + '<b><i>меню </i></b>' + 'чтобы взаимодействовать с функциями бота:', reply_markup=keyboard.start_m)


@dp.message_handler(state=Users.Name)
async def phnum(message: types.Message, state: FSMContext):
    name_input = message.text
    name_surname = name_input.split()

    if len(name_surname) == 2:
        name, surname = name_surname
        if re.match(r'^[А-ЯЁа-яё]+\s[А-ЯЁа-яё]+$', name_input):
            name = name.capitalize()
            surname = surname.capitalize()
            name_surname = name + ' ' + surname
            await state.update_data(name=name_surname)
            await message.answer('📞Теперь отправьте Ваш' + fmt.hbold(' номер телефона') + ' через ' + fmt.hbold(
                '+7') + ' следующим сообщением:')
            await Users.Phnum.set()
        else:
            await message.answer(
                '⚠️ Неправильный формат имени и фамилии. Введите в верхнем регистре, используя кириллицу и разделение одним пробелом.')
    else:
        await message.answer('⚠️ Введите имя и фамилию в одной строке, разделенные одним пробелом.')


@dp.message_handler(state=Users.Phnum)
async def addphnum(message: types.Message, state: FSMContext):
    phnum = message.text
    if re.match(r'^\+7\d{10}$', phnum):
        await state.update_data(phnum=phnum)
        data = await state.get_data()
        db.update_user(message.chat.id, name=data['name'], phnum=data['phnum'])

        await state.finish()

        await message.answer('✅ Ваши данные сохранены и обновлены в базе данных.')
    else:
        await message.answer('⚠️ Неправильный формат номера телефона. Введите номер в формате +7XXXXXXXXXX.')


@dp.message_handler(text='📛Оставить заявку')
async def define_timezone_handler(message: types.Message):
    await message.answer('📛👇📛<i>Выберите категорию, по которой Вы хотите оставить заявку в УК:</i>', reply_markup=keyboard.application_m)


@dp.callback_query_handler(lambda c: c.data == 'leave_app')
async def leave_application_handler(callback: types.CallbackQuery):
    await callback.message.answer('<b><i>Шаг 1/3 📝 </i></b>' + 'Напишите адрес или ориентир проблемы (улицу, номер дома, подъезд, этаж и квартиру) или пропустите этот пункт:', reply_markup=keyboard.skip_m)
    await Application.Location.set()


@dp.message_handler(state=Application.Location)
async def process_location_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['location'] = message.text
    await Application.Photo.set()
    await message.answer('Шаг 2/3 📷 Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:', reply_markup=keyboard.skip_m)


@dp.message_handler(content_types=['photo', 'video'], state=Application.Photo)
async def process_media_step(message: types.Message, state: FSMContext):
    if message.content_type not in ['photo', 'video']:
        await message.answer('⛔📛В данном пункте нужно обязательно отправить <b>фотографию</b> или <b>видео</b> в виде медиа-сообщения. Попробуйте ещё раз:')
        return

    file_id = message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    downloaded_file = await bot.download_file(file_path)
    file_extension = os.path.splitext(file_path)[-1]
    unique_filename = f'{uuid.uuid4()}{file_extension}'
    save_path = os.path.join(f'Media', unique_filename)

    with open(save_path, 'wb') as f:
        f.write(downloaded_file.read())

    async with state.proxy() as data:
        data['photo'] = save_path

    await Application.Reason.set()

    await message.answer('Шаг 3/3 📝 Напишите причину обращения:', reply_markup=keyboard.skip_m)


@dp.message_handler(state=Application.Reason)
async def process_reason_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['reason'] = message.text
        chat_id = message.chat.id
        location = data.get('location', 'Unknown Location')
        photo = data.get('photo')
        reason = data.get('reason', 'No reason provided')
        user_info = db.get_user_info(chat_id)
        name = user_info['name']
        num = user_info['phnum']
        user = await bot.get_chat_member(chat_id, message.from_user.id)
        user_username = user.user.username
        db.add_application(chat_id, location, photo, reason)

        group_chat_id = -1001973593367
        application_info = f"⛔Поступила новая жалобa:\n@{user_username}\n<b>Имя и фамилия: </b>{name}\n<b>Номер телефона:</b> {num}\n<b>Адрес:</b> {location}\n<b>Причина:</b> {reason}"

        if photo:
            input_photo = InputFile(photo)
            await bot.send_photo(group_chat_id, input_photo, caption=application_info, parse_mode='HTML')
        else:
            await bot.send_message(group_chat_id, application_info, parse_mode='HTML')

        await state.finish()
        await message.answer('<b>✅Жалоба отправлена администрации.</b>' + '<i> Спасибо за Ваше обращение!</i>')


@dp.callback_query_handler(lambda c: c.data == 'skip', state=Application.Location)
async def skip_location_handler(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['location'] = None
    await Application.Photo.set()
    await callback.message.answer('Шаг 2/3 📷 Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:', reply_markup=keyboard.skip_m)


@dp.callback_query_handler(lambda c: c.data == 'skip', state=Application.Photo)
async def skip_photo_handler(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = None
    await Application.Reason.set()
    await callback.message.answer('Шаг 3/3 📝 Напишите причину обращения в подробностях:', reply_markup=keyboard.skip_m)


@dp.callback_query_handler(lambda c: c.data == 'back', state='*')
async def go_back(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Вы вернулись назад.')
    async with state.proxy() as data:
        if 'photo' in data:
            del data['photo']
        current_state = await state.get_state()
        if current_state == Application.Reason.state:
            await Application.Photo.set()
            await callback.message.answer('Шаг 2/3 📷 Прикрепите фотографию или видео к своей заявке или пропустите этот пункт:', reply_markup=keyboard.skip_m)
        elif current_state == Application.Photo.state:
            await Application.Location.set()
            await callback.message.answer('<b><i>Шаг 1/3 📝 </i></b>' + 'Напишите адрес или ориентир проблемы (улицу, номер дома, подъезд, этаж и квартиру) или пропустите этот пункт:', reply_markup=keyboard.skip_m)
        elif current_state == Application.Suggestion.state:
            await callback.message.answer('📛👇📛<i>Выберите категорию, по которой Вы хотите оставить заявку в УК:</i>', reply_markup=keyboard.application_m)
            await state.finish()
        else:
            await callback.message.answer(
            fmt.hbold('✈Добро пожаловать ') + fmt.hitalic('в главное меню чат-бота Управляющей компании "УЭР-ЮГ"') +
            '. Здесь Вы можете оставить заявку для управляющей компании или направить свое предложение по управлению домом. Просто воспользуйтесь кнопками '
            + '<b><i>меню </i></b>' + 'чтобы взаимодействовать с функциями бота:', reply_markup=keyboard.start_m)


@dp.callback_query_handler(lambda c: c.data == 'share', state='*')
async def share_suggestion(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('<b>Распишите Ваше предложение вподробностях: (Добавьте фотографию, если есть)</b>',reply_markup=keyboard.back_markup)
    await state.update_data(suggestion=True)
    await Application.Suggestion.set()


@dp.message_handler(state=Application.Suggestion, content_types=['text', 'photo'])
async def process_suggestion_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        suggestion = data.get('suggestion', False)
        if suggestion:
            if message.photo:
                suggestion_text = message.caption  # Используем текст из caption фото
                photo = message.photo[-1].file_id

                chat_id = message.chat.id
                user_info = db.get_user_info(chat_id)
                name = user_info['name']
                num = user_info['phnum']
                user = await bot.get_chat_member(chat_id, message.from_user.id)
                user_username = user.user.username
                group_chat_id = -1001973593367
                suggestion_info = f"🔔Получено новое предложение:\n@{user_username}\n<b>Имя и фамилия: </b>{name}\n<b>Номер телефона:</b> {num}\n<b>Содержание:</b> {suggestion_text}"

                file_info = await bot.get_file(photo)
                file_path = file_info.file_path
                downloaded_file = await bot.download_file(file_path)
                file_extension = os.path.splitext(file_path)[-1]
                unique_filename = f'{uuid.uuid4()}{file_extension}'
                save_path = os.path.join(f'Media', unique_filename)

                with open(save_path, 'wb') as f:
                    f.write(downloaded_file.read())

                input_photo = InputFile(save_path)
                await bot.send_photo(group_chat_id, input_photo, caption=suggestion_info, parse_mode='HTML')
            else:
                suggestion_text = message.text

                chat_id = message.chat.id
                user_info = db.get_user_info(chat_id)
                name = user_info['name']
                num = user_info['phnum']
                user = await bot.get_chat_member(chat_id, message.from_user.id)
                user_username = user.user.username
                group_chat_id = -1001973593367
                suggestion_info = f"🔔Получено новое предложение:\n@{user_username}\n<b>Имя и фамилия: </b>{name}\n<b>Номер телефона:</b> {num}\n<b>Содержание:</b> {suggestion_text}"

                await bot.send_message(group_chat_id, suggestion_info, parse_mode='HTML')

            await message.answer('✅💡<b>Идея принята и передана администрации. </b><i>Спасибо за Ваше обращение!</i>')
            await state.finish()
        else:
            await message.answer('⛔📛Предложение должно содержать только текст')
            await state.finish()


@dp.message_handler(text='☎Полезные контакты')
async def send_contacts(message: types.Message):
    contacts_text = """
Управляющая компания:    
<b>Диспетчерская служба 000 «УЭР-ЮГ»</b>
+7 4722 35-50-06

<b>Инженеры ООО «УЭР-ЮГ»</b>
+7 920 566-28-86

<b>Бухгалтерия ООО «УЭР-ЮГ»</b>
+7 4722 35-50-06

Белгород, Свято-Троицкий б-р. д. 15, подъезд No 1

<u>Телефоны для ОТКРЫТИЯ Ворот и шлагбаума:</u>
<b>Шлагбаум «Набережная»</b>
+7 920 554-87-74

<b>Ворота «Харьковские»</b>
+7 920 554-87-40

<b>Ворота «Мост»</b>
+7 920 554-64-06

<b>Калитка 1 «МОСТ»</b>
+7 920 554-42-10

<b>Калитка 2 «Мост»</b>
+7 920 554-89-04

<b>Калитка 3 «Харьковская»</b>
+7 920 554-87-39

<b>Калитка 4 «Харьковская»</b>
+7 920 554-89-02

<b>Охрана</b>
+7 915 57-91-457

<b>Участковый</b>
Куленцова Марина Владимировна:
+7 999 421-53-72"""

    await message.answer(contacts_text, parse_mode='HTML')


@dp.message_handler(text='⚙Настройки')
async def settings(message: types.Message):
    await message.answer('⚙Тут Вы сможете поменять <b>Имя</b> и <b>Фамилию</b> в Базе данных нашего бота или же можете поменять Ваш <b>номер телефона</b>, '
                         'если Вы изначально вводили что-то неверно. Выберите, что хотите поменять или вернитесь назад в <b>главное меню</b>:', reply_markup=keyboard.settings)


@dp.callback_query_handler(lambda c: c.data == 'сh_name')
async def change_name(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer('🛠<i>Отправьте свое Имя и Фамилию, чтобы поменять настройки :</i>')
    await Update.Name.set()


@dp.callback_query_handler(lambda c: c.data == 'сh_num')
async def change_number(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer('🛠<i>Отправьте свой номер телефона, чтобы поменять настройки :</i>')
    await Update.Phnum.set()


@dp.message_handler(state=Update.Name)
async def set_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        chat_id = message.chat.id
        new_name = message.text
        old_data = await state.get_data()
        db.update_user(chat_id, name=old_data.get('name'), phnum=old_data.get('phnum'))
        db.update_user(chat_id, name=new_name, phnum=old_data.get('phnum'))
        await state.finish()
        await message.answer('🛠✅🛠Настройки <b>имени</b> успешно применены!')


@dp.message_handler(state=Update.Phnum)
async def set_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        chat_id = message.chat.id
        new_number = message.text
        old_data = await state.get_data()
        db.update_user(chat_id, name=old_data.get('name'), phnum=old_data.get('phnum'))
        db.update_user(chat_id, name=old_data.get('name'), phnum=new_number)
        await state.finish()
        await message.answer('🛠✅🛠Настройки <b>номера</b> успешно применены!')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)