import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# ⚙️ НАСТРОЙКИ КОНФИГУРАЦИИ (Заполняет клиент)
# ==========================================
API_TOKEN = 'ВАШ_ТОКЕН_БОТА'
ADMIN_ID = 123456789          # Для Бота-Визитки (куда слать заявки)
CHANNEL_ID = -1001234567890   # Для Бота-Подписок / VIP-клуба (ID канала)
CHANNEL_URL = 'https://t.me' # Ссылка на канал

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# ==========================================
# 🏢 МОДУЛЬ 1: БОТ-ВИЗИТКА И СБОР ЗАЯВОК
# ==========================================
@dp.message(Command("start"))
async def cmd_start_vizitka(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="💰 Прайс-лист", callback_data="price"))
    builder.add(types.InlineKeyboardButton(text="📞 Оставить заявку", callback_data="order"))
    builder.adjust(1)
    
    await message.answer(
        f"👋 Здравствуйте, {message.from_user.first_name}!\n"
        "Рады приветствовать вас. Выберите интересующий раздел ниже:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "price")
async def show_price(callback: types.CallbackQuery):
    await callback.message.answer("📝 Наш базовый прайс:\n• Услуга А — от 3 000 руб.\n• Услуга Б — от 5 000 руб.")
    await callback.answer()

@dp.callback_query(F.data == "order")
async def process_order(callback: types.CallbackQuery):
    await callback.message.answer("✍️ Напишите вашу задачу в ответном сообщении, и менеджер сразу свяжется с вами!")
    await callback.answer()


# ==========================================
# 🎁 МОДУЛЬ 2: ВЫДАЧА ПОДАРКА ЗА ПОДПИСКУ
# ==========================================
# Чтобы активировать этот режим, клиенту достаточно переключить команду запуска
@dp.message(Command("gift"))
async def cmd_gift(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_URL))
    builder.add(types.InlineKeyboardButton(text="✅ Я подписался!", callback_data="check_sub"))
    builder.adjust(1)

    await message.answer(
        "🎁 Чтобы получить ваш бесплатный инфопродукт, подпишитесь на наш канал и нажмите кнопку проверки:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: types.CallbackQuery):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=callback.from_user.id)
        if member.status in ['member', 'administrator', 'creator']:
            await callback.answer("🎉 Успешно!")
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer("🚀 Спасибо за подписку! Ваш подарок: https://your-site.com")
        else:
            await callback.answer("❌ Вы еще не подписались на канал!", show_alert=True)
    except Exception as e:
        await callback.answer("⚠️ Ошибка проверки подписки. Убедитесь, что бот добавлен в админы канала.", show_alert=True)


# ==========================================
# 💳 МОДУЛЬ 3: VIP-КЛУБ (ПЛАТЕЖИ TELEGRAM STARS)
# ==========================================
@dp.message(Command("vip"))
async def cmd_vip(message: types.Message):
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Доступ в закрытый VIP-чат",
        description="Оплата доступа на 1 месяц.",
        payload="vip_sub",
        provider_token="", # Для Telegram Stars всегда пусто
        currency="XTR",    # Валюта Telegram Stars
        prices=[types.LabeledPrice(label="VIP Доступ", amount=150)] # Цена в звездах
    )

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    await message.answer("🎉 Оплата прошла! Генерирую вашу уникальную ссылку...")
    invite_link = await bot.create_chat_invite_link(chat_id=CHANNEL_ID, member_limit=1)
    await message.answer(f"👉 Ваша одноразовая ссылка для входа: {invite_link.invite_link}")


# ==========================================
# ✉️ ЭХО-ПЕРЕСЫЛКА (МЕНЕДЖЕРУ ДЛЯ ВИЗИТКИ)
# ==========================================
@dp.message()
async def forward_to_admin(message: types.Message):
    if message.text and not message.text.startswith('/'):
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 **Новая заявка!**\nОт: @{message.from_user.username}\nТекст: {message.text}"
            )
            await message.answer("✅ Сообщение отправлено менеджеру. Ожидайте ответа!")
        except Exception:
            await message.answer("ℹ️ Бот работает. Введите /start, /gift или /vip для теста модулей.")


async def main():
    print("Универсальный коммерческий бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())