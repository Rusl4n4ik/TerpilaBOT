from aiogram import types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


start_m = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
start_btn1 = ['📛Оставить заявку', '📞Связаться']
start_btn2= ['⚙Настройки']
start_btn3= ['☎Полезные контакты']
start_m.add(*start_btn1)
start_m.add(*start_btn2)
start_m.add(*start_btn3)

application_m = types.InlineKeyboardMarkup(row_width=2)
app_btn1 = types.InlineKeyboardButton('📛Оставить заявку', callback_data='leave_app')
app_btn2 = types.InlineKeyboardButton('💡Поделиться предложением', callback_data='share')
app_btn3 = types.InlineKeyboardButton('🔙Назад', callback_data='back')
back_markup = types.InlineKeyboardMarkup().add(app_btn3)
application_m.add(app_btn1, app_btn2, app_btn3)

skip_m = types.InlineKeyboardMarkup(row_width=2)
skip = types.InlineKeyboardButton('▶Пропустить', callback_data='skip')
skip_m.add(skip,app_btn3)

settings = types.InlineKeyboardMarkup(row_width=2)
name = types.InlineKeyboardButton('🛠Поменять имя', callback_data='сh_name')
number = types.InlineKeyboardButton('🛠Поменять номер', callback_data='сh_num')
settings.add(name, number, app_btn3)

call_m = types.InlineKeyboardMarkup(row_width=1)
call1 = types.InlineKeyboardButton('📞Перезвоните мне', callback_data='call_back')
call2 = types.InlineKeyboardButton('📞Свяжитесь со мной в чат-боте', callback_data='chat')
call_m.add(call1, call2, app_btn3)

call_b = types.InlineKeyboardMarkup()
yes_button = types.InlineKeyboardButton('✅Дa', callback_data='confirm_number')
leave_num = types.InlineKeyboardButton('🔙Оставить номер телефона', callback_data='leave-num')
call_b.add(yes_button, leave_num)

finish = types.InlineKeyboardMarkup()
end_dialog_btn = types.InlineKeyboardButton('❌📞Завершить диалог', callback_data='end_dialog')
finish.add(end_dialog_btn)