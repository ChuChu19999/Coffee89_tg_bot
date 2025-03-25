import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from database import Database

load_dotenv()

db = Database()

# Состояния диалога добавления товара
ADD_ITEM_NAME = 1
ADD_ITEM_DESCRIPTION = 2
ADD_ITEM_PRICE = 3

# Состояния диалога редактирования товара
EDIT_ITEM_SELECT = 1
EDIT_ITEM_FIELD = 2
EDIT_ITEM_VALUE = 3


async def setup_commands(application: Application):
    """Установка команд бота"""
    commands = (
        BotCommand("start", "Запустить бота"),
        BotCommand("menu", "Показать меню"),
        BotCommand("orders", "Мои заказы"),
        BotCommand("about", "О нас"),
    )
    await application.bot.set_my_commands(commands)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    # Создаем пользователя в базе данных
    db.create_user_if_not_exists(user.id, user.username)

    keyboard = [
        (InlineKeyboardButton("🍵 Меню", callback_data="menu"),),
        (
            InlineKeyboardButton("🛒 Корзина", callback_data="view_cart"),
            InlineKeyboardButton("📝 Мои заказы", callback_data="my_orders"),
        ),
        (InlineKeyboardButton("ℹ️ О нас", callback_data="about"),),
    ]

    # Проверка на администратора
    if db.is_admin(user.id):
        keyboard.append(
            (InlineKeyboardButton("👑 Админка", callback_data="admin_panel"),)
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"✨ Добро пожаловать в 𝓚-89 𝓒𝓸𝓯𝓯𝓮𝓮, {user.first_name}! ✨\n\n"
        "Выберите действие 👇",
        reply_markup=reply_markup,
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu и кнопки меню"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.edit_message_text
    else:
        message = update.message.reply_text

    menu_items = db.get_menu_items()
    keyboard = []
    for item in menu_items:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{item['name']} - {item['price']}₽",
                    callback_data=f"order_{item['id']}",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message(
        "☕️ *Наше меню:*\n\n" "Выберите напиток для заказа 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /orders и кнопки мои заказы"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        message = query.edit_message_text
    else:
        user = update.effective_user
        message = update.message.reply_text

    orders = db.get_user_orders(user.id)

    if not orders:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message("У вас пока нет заказов.", reply_markup=reply_markup)
        return

    text = "📋 *Ваши заказы:*\n\n"
    for order in orders:
        text += f"🔸 Заказ #{order['id']}\n"
        text += f"📌 Статус: {order['status']}\n"
        text += "🛍 Состав заказа:\n"
        for item in order["items"]:
            text += f"  • {item['name']} × {item['quantity']} = {item['subtotal']}₽\n"
        text += f"💰 Итого: {order['total']}₽\n\n"

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message(text, reply_markup=reply_markup, parse_mode="Markdown")


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /about и кнопки О нас"""
    try:
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            message = query.edit_message_text
        else:
            message = update.message.reply_text

        about_text = (
            "✨ *𝓚-89 𝓒𝓸𝓯𝓯𝓮𝓮* - ваша любимая кофейня! ✨\n\n"
            "🕐 *Режим работы:*\n"
            "Пн-Вс: 9:00 - 21:00\n\n"
            "📍 *Адрес:*\n"
            "ЯНАО, г. Новый Уренгой\n"
            "м-рн Оптимистов, 3, корп. 1\n\n"
            "📱 *Контакты:*\n"
            "Telegram: @CoffeeNur89\n\n"
            "✨ *Акции и предложения:*\n"
            "При покупке двух упаковок чая – получите скидку 15% на обе!\n\n"
            "Мы варим кофе с любовью и заботой о каждом госте! 💝\n"
            "Ждем вас в 𝓚-89 𝓒𝓸𝓯𝓯𝓮𝓮, чтобы подарить вам незабываемый вкус и уют! ✨\n\n"
            "🛟 По вопросам работы бота обращайтесь: @Lill\\_Polly"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📍 Показать на карте", url="https://yandex.ru/maps/-/CHaBEOmM"
                )
            ],
            [InlineKeyboardButton("✈️ Telegram", url="https://t.me/CoffeeNur89")],
            [InlineKeyboardButton("🛟 Тех. поддержка", url="https://t.me/Lill_Polly")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await message(about_text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка в about_handler: {e}")
        if update.message:
            await update.message.reply_text(
                "Произошла ошибка при загрузке информации. Попробуйте позже."
            )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик панели администратора"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к панели администратора.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Статистика заказов", callback_data="admin_stats")],
        [InlineKeyboardButton("📦 Управление заказами", callback_data="manage_orders")],
        [InlineKeyboardButton("🍽 Управление меню", callback_data="menu_management")],
        [
            InlineKeyboardButton(
                "👥 Управление админами", callback_data="admin_management"
            )
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ]

    await query.edit_message_text(
        "👑 *Админка:*\n\n" "Выберите действие 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик возврата в главное меню"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🍵 Меню", callback_data="menu")],
        [
            InlineKeyboardButton("🛒 Корзина", callback_data="view_cart"),
            InlineKeyboardButton("📝 Мои заказы", callback_data="my_orders"),
        ],
        [InlineKeyboardButton("ℹ️ О нас", callback_data="about")],
    ]

    # Проверка на администратора
    if db.is_admin(query.from_user.id):
        keyboard.append(
            [InlineKeyboardButton("👑 Админка", callback_data="admin_panel")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"✨ Добро пожаловать в 𝓚-89 𝓒𝓸𝓯𝓯𝓮𝓮, {query.from_user.first_name}! ✨\n\n"
        "Выберите действие 👇",
        reply_markup=reply_markup,
    )


async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на товар в меню"""
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split("_")[1])
    item = db.get_menu_item(item_id)

    if not item:
        await query.edit_message_text(
            "Товар не найден",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад в меню", callback_data="menu")]]
            ),
        )
        return

    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data=f"decrease_{item_id}"),
            InlineKeyboardButton("1", callback_data="quantity"),
            InlineKeyboardButton("➕", callback_data=f"increase_{item_id}"),
        ],
        [
            InlineKeyboardButton(
                "🛒 Добавить в корзину", callback_data=f"add_to_cart_{item_id}"
            )
        ],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu")],
    ]

    await query.edit_message_text(
        f"✨ *{item['name']}*\n"
        f"💰 Цена: {item['price']}₽\n\n"
        "Выберите количество 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику заказов"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к этой функции.")
        return

    # Получаем статистику за разные периоды
    all_time_stats = db.get_orders_stats()
    day_stats = db.get_orders_stats("day")
    week_stats = db.get_orders_stats("week")
    month_stats = db.get_orders_stats("month")

    text = "📊 *Статистика заказов:*\n\n"

    text += "🌟 *За все время:*\n"
    text += f"📦 Всего заказов: {all_time_stats['total_orders']}\n"
    text += f"💰 Выручка: {all_time_stats['total_revenue']}₽\n\n"

    text += "*🌟 За последний день:*\n"
    text += f"📦 Заказов: {day_stats['total_orders']}\n"
    text += f"💰 Выручка: {day_stats['total_revenue']}₽\n\n"

    text += "*🌟 За неделю:*\n"
    text += f"📦 Заказов: {week_stats['total_orders']}\n"
    text += f"💰 Выручка: {week_stats['total_revenue']}₽\n\n"

    text += "*🌟 За месяц:*\n"
    text += f"📦 Заказов: {month_stats['total_orders']}\n"
    text += f"💰 Выручка: {month_stats['total_revenue']}₽\n\n"

    text += "*Текущие заказы:*\n"
    text += f"🕒 Ожидают выполнения: {all_time_stats['pending_orders']}\n"
    text += f"🕒 Выполнено: {all_time_stats['completed_orders']}\n\n"

    text += "*Последние заказы:*\n"
    for order in all_time_stats["orders"]:
        text += f"#{order['id']} - {order['status']} - {order['total']}₽\n"

    keyboard = [
        [InlineKeyboardButton("📦 Управление заказами", callback_data="manage_orders")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")],
    ]

    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )


async def manage_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление заказами"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к этой функции.")
        return

    orders = db.get_all_orders(status="Принят")

    if not orders:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Нет активных заказов.", reply_markup=reply_markup
        )
        return

    text = "📦 *Активные заказы:*\n\n"
    keyboard = []

    for order in orders:
        text += (
            f"*Заказ #{order['id']}*\n"
            f"⏰ Время получения: {order.get('desired_time', 'Не указано')}\n"
            f"📱 Контакт: @{order.get('username', 'Нет username')}\n"
            f"💰 Сумма: {order['total']}₽\n"
            "Состав заказа:\n"
        )
        for item in order["items"]:
            text += f"- {item['name']} x{item['quantity']}\n"
        text += "\n"

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✅ Выполнить #{order['id']}",
                    callback_data=f"complete_order_{order['id']}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметить заказ как выполненный и уведомить пользователя"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к этой функции.")
        return

    order_id = int(query.data.split("_")[-1])
    db.update_order_status(order_id, "Готов")

    # Отправляем уведомление пользователю
    await notify_user_order_ready(context, order_id)

    await query.answer("Заказ отмечен как выполненный! Клиент уведомлен.")
    await manage_orders(update, context)


async def process_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик оформления заказа"""
    query = update.callback_query
    await query.answer()

    # Получаем корзину из контекста пользователя
    cart_items = context.user_data.get("cart", [])
    if not cart_items:
        await query.edit_message_text(
            "Ваша корзина пуста. Добавьте товары для оформления заказа.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 В меню", callback_data="menu")]]
            ),
        )
        return

    try:
        # Создаем заказ
        order_id = db.process_order(query.from_user.id, cart_items)

        # Очищаем корзину
        context.user_data["cart"] = []

        # Формируем сообщение о успешном создании заказа
        text = (
            "✅ *Заказ успешно оформлен!*\n\n"
            f"Номер заказа: #{order_id}\n"
            "Статус: Принят\n\n"
            "Мы уведомим вас, когда заказ будет готов!\n"
            "Спасибо, что выбрали нас! 🙏"
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 В главное меню", callback_data="back_to_main"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown",
        )

    except Exception as e:
        await query.edit_message_text(
            "Произошла ошибка при оформлении заказа. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 В главное меню", callback_data="back_to_main"
                        )
                    ]
                ]
            ),
        )
        print(f"Error processing order: {e}")


async def notify_user_order_ready(context: ContextTypes.DEFAULT_TYPE, order_id: int):
    """Отправить уведомление пользователю о готовности заказа"""
    order_info = db.notify_order_status(order_id)
    if not order_info:
        return

    text = (
        "🎉 *Ваш заказ готов!*\n\n"
        f"Номер заказа: #{order_info['order_id']}\n"
        "Состав заказа:\n"
    )

    for item in order_info["items"]:
        text += f"• {item['name']} x{item['quantity']}\n"

    text += f"\nИтого: {order_info['total']}₽\n\n"
    text += "Ждём вас! ☕️"

    try:
        await context.bot.send_message(
            chat_id=order_info["telegram_id"], text=text, parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending notification: {e}")


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить товар в корзину"""
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split("_")[-1])

    # Получаем текущее количество из кнопки
    keyboard = query.message.reply_markup.inline_keyboard
    quantity_button = keyboard[0][1]  # Кнопка с количеством
    quantity = int(quantity_button.text)

    # Инициализируем корзину, если её нет
    if "cart" not in context.user_data:
        context.user_data["cart"] = []

    # Проверяем, есть ли уже такой товар в корзине
    found = False
    for item in context.user_data["cart"]:
        if item["item_id"] == item_id:
            # Если товар найден, увеличиваем его количество
            item["quantity"] += quantity
            found = True
            break

    # Если товар не найден в корзине, добавляем новый
    if not found:
        cart_item = {"item_id": item_id, "quantity": quantity}
        context.user_data["cart"].append(cart_item)

    # Получаем название товара для сообщения
    item = db.get_menu_item(item_id)
    item_name = item["name"] if item else "товар"

    await query.edit_message_text(
        f"✅ {item_name} добавлен в корзину",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🛒 Перейти в корзину", callback_data="view_cart"
                    ),
                    InlineKeyboardButton("🔙 Вернуться в меню", callback_data="menu"),
                ]
            ]
        ),
    )


async def update_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик изменения количества товара"""
    query = update.callback_query
    await query.answer()

    action, item_id = query.data.split("_")
    item_id = int(item_id)
    item = db.get_menu_item(item_id)

    if not item:
        await query.edit_message_text(
            "Товар не найден",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад в меню", callback_data="menu")]]
            ),
        )
        return

    # Получаем текущее количество из текста кнопки
    keyboard = query.message.reply_markup.inline_keyboard
    quantity_button = keyboard[0][1]  # Кнопка с количеством
    current_quantity = int(quantity_button.text)

    # Изменяем количество
    if action == "increase":
        new_quantity = current_quantity + 1
    else:  # decrease
        new_quantity = max(1, current_quantity - 1)

    # Обновляем клавиатуру
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data=f"decrease_{item_id}"),
            InlineKeyboardButton(str(new_quantity), callback_data="quantity"),
            InlineKeyboardButton("➕", callback_data=f"increase_{item_id}"),
        ],
        [
            InlineKeyboardButton(
                "🛒 Добавить в корзину", callback_data=f"add_to_cart_{item_id}"
            )
        ],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="menu")],
    ]

    await query.edit_message_text(
        f"✨ *{item['name']}*\n"
        f"💰 Цена: {item['price']}₽\n\n"
        "Выберите количество 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик просмотра корзины"""
    try:
        if update.callback_query:
            query = update.callback_query
            try:
                await query.answer()
            except Exception:
                # Игнорируем ошибку устаревшего callback_query
                pass
            message = query.edit_message_text
        else:
            message = update.message.reply_text

        cart_items = context.user_data.get("cart", [])
        if not cart_items:
            await message(
                "Ваша корзина пуста!",
                reply_markup=InlineKeyboardMarkup(
                    ((InlineKeyboardButton("🔙 В меню", callback_data="menu"),),)
                ),
            )
            return

        text = "🛒 *Ваша корзина:*\n\n"
        total = 0

        for item in cart_items:
            menu_item = db.get_menu_item(item["item_id"])
            if menu_item:
                subtotal = menu_item["price"] * item["quantity"]
                total += subtotal
                text += (
                    f"• {menu_item['name']}\n"
                    f"  {item['quantity']} × {menu_item['price']}₽ = {subtotal}₽\n"
                )

        text += f"\n*Итого: {total}₽*"

        keyboard = (
            (InlineKeyboardButton("✅ Оформить заказ", callback_data="confirm_order"),),
            (InlineKeyboardButton("🗑 Очистить корзину", callback_data="clear_cart"),),
            (InlineKeyboardButton("🔙 В меню", callback_data="menu"),),
        )

        await message(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    except Exception as e:
        # Если произошла ошибка, отправляем новое сообщение
        if update.callback_query:
            await update.callback_query.message.reply_text(
                "Произошла ошибка. Попробуйте снова.",
                reply_markup=InlineKeyboardMarkup(
                    ((InlineKeyboardButton("🔙 В меню", callback_data="menu"),),)
                ),
            )
        print(f"Error in view_cart: {e}")


async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистить корзину"""
    query = update.callback_query
    await query.answer()

    context.user_data["cart"] = []
    await query.edit_message_text(
        "Корзина очищена!",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 В меню", callback_data="menu")]]
        ),
    )


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение заказа"""
    query = update.callback_query
    await query.answer()

    cart_items = context.user_data.get("cart", [])
    if not cart_items:
        await query.edit_message_text(
            "Ваша корзина пуста!",
            reply_markup=InlineKeyboardMarkup(
                ((InlineKeyboardButton("🔙 В меню", callback_data="menu"),),)
            ),
        )
        return

    # Показываем варианты времени
    keyboard = (
        (InlineKeyboardButton("⚡️ Как можно быстрее", callback_data="time_asap"),),
        (InlineKeyboardButton("⏰ Через 15 минут", callback_data="time_15"),),
        (InlineKeyboardButton("⏰ Через 30 минут", callback_data="time_30"),),
        (InlineKeyboardButton("⏰ Через 45 минут", callback_data="time_45"),),
        (InlineKeyboardButton("⏰ Через 1 час", callback_data="time_60"),),
        (InlineKeyboardButton("🔙 Назад", callback_data="view_cart"),),
    )

    await query.edit_message_text(
        "🕒 *Выберите желаемое время получения заказа:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def handle_order_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора времени заказа"""
    try:
        query = update.callback_query
        try:
            await query.answer()
        except Exception:
            pass

        time_option = query.data.split("_")[1]

        # Сохраняем выбранное время
        if time_option == "asap":
            time_text = "Как можно быстрее"
        else:
            minutes = int(time_option)
            time_text = f"Через {minutes} минут"

        try:
            # Создаем заказ с выбранным временем
            order_id = db.process_order(
                query.from_user.id, context.user_data["cart"], desired_time=time_text
            )

            # Очищаем корзину
            context.user_data["cart"] = []

            # Уведомляем пользователя
            await query.edit_message_text(
                "✅ *Заказ успешно оформлен!*\n\n"
                f"Номер заказа: #{order_id}\n"
                f"Время получения: {time_text}\n"
                "Статус: Принят\n\n"
                "Мы уведомим вас, когда заказ будет готов.\n"
                "Спасибо за заказ! ☕️",
                reply_markup=InlineKeyboardMarkup(
                    (
                        (
                            InlineKeyboardButton(
                                "🔙 В главное меню", callback_data="back_to_main"
                            ),
                        ),
                    )
                ),
                parse_mode="Markdown",
            )

            # Уведомляем всех админов о новом заказе
            await notify_admins_new_order(context, order_id)

        except Exception as e:
            print(f"Error processing order: {e}")
            await query.edit_message_text(
                "Произошла ошибка при оформлении заказа. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup(
                    (
                        (
                            InlineKeyboardButton(
                                "🔙 В главное меню", callback_data="back_to_main"
                            ),
                        ),
                    )
                ),
            )

    except Exception as e:
        print(f"Error in handle_order_time: {e}")
        try:
            await update.callback_query.message.reply_text(
                "Произошла ошибка. Попробуйте оформить заказ заново.",
                reply_markup=InlineKeyboardMarkup(
                    (
                        (
                            InlineKeyboardButton(
                                "🔙 В корзину", callback_data="view_cart"
                            ),
                        ),
                    )
                ),
            )
        except Exception:
            pass


async def notify_admins_new_order(context: ContextTypes.DEFAULT_TYPE, order_id: int):
    """Уведомить всех админов о новом заказе"""
    order_info = db.notify_order_status(order_id)
    if not order_info:
        return

    admins = db.get_all_admins()

    text = (
        "🆕 *Новый заказ!*\n\n"
        f"Номер заказа: #{order_info['order_id']}\n"
        f"Время получения: {order_info['desired_time']}\n\n"
        "Состав заказа:\n"
    )

    for item in order_info["items"]:
        text += f"• {item['name']} x{item['quantity']}\n"

    text += f"\nИтого: {order_info['total']}₽\n\n"
    text += f"📱 Контакт клиента: @{order_info['username']}"

    keyboard = (
        (
            InlineKeyboardButton(
                "✅ Заказ готов", callback_data=f"complete_order_{order_id}"
            ),
        ),
    )

    for admin_id in admins:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        except Exception as e:
            print(f"Error sending notification to admin {admin_id}: {e}")


async def admin_menu_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление меню"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к этой функции.")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Добавить товар", callback_data="start_add_item")],
        [InlineKeyboardButton("📋 Список товаров", callback_data="list_menu_items")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")],
    ]

    await query.edit_message_text(
        "🍽 *Управление меню*\n\n" "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def handle_menu_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик действий с меню"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к этой функции.")
        return

    action = query.data

    if action == "start_add_item":
        context.user_data["menu_action"] = "adding_name"
        await query.edit_message_text(
            "Введите название нового товара:\n" "(для отмены нажмите кнопку ниже)",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Отмена", callback_data="menu_management")]]
            ),
        )

    elif action == "list_menu_items":
        menu_items = db.get_menu_items()
        if not menu_items:
            await query.edit_message_text(
                "Меню пусто. Добавьте товары!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Назад", callback_data="menu_management"
                            )
                        ]
                    ]
                ),
            )
            return

        text = "*Список товаров в меню:*\n\n"
        keyboard = []
        for item in menu_items:
            text += f"• {item['name']} - {item['price']}₽\n"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"❌ Удалить {item['name']}",
                        callback_data=f"delete_item_{item['id']}",
                    )
                ]
            )

        keyboard.append(
            [InlineKeyboardButton("🔙 Назад", callback_data="menu_management")]
        )

        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    elif action.startswith("delete_item_"):
        item_id = int(action.split("_")[-1])
        if db.delete_menu_item(item_id):
            await query.edit_message_text(
                "✅ Товар успешно удален",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 К списку товаров", callback_data="list_menu_items"
                            )
                        ]
                    ]
                ),
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка при удалении товара",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 К списку товаров", callback_data="list_menu_items"
                            )
                        ]
                    ]
                ),
            )


async def handle_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений при работе с меню"""
    if "menu_action" not in context.user_data:
        return

    if not db.is_admin(update.effective_user.id):
        return

    action = context.user_data["menu_action"]

    if action == "adding_name":
        # Сохраняем название и запрашиваем цену
        context.user_data["new_item_name"] = update.message.text
        context.user_data["menu_action"] = "adding_price"
        await update.message.reply_text(
            "Введите цену товара (только число):",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Отмена", callback_data="menu_management")]]
            ),
        )

    elif action == "adding_price":
        try:
            price = float(update.message.text)
            if price <= 0:
                raise ValueError

            # Создаем новый товар
            db.add_menu_item(name=context.user_data["new_item_name"], price=price)

            # Очищаем данные
            context.user_data.clear()

            await update.message.reply_text(
                "✅ Товар успешно добавлен в меню!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 В управление меню", callback_data="menu_management"
                            )
                        ]
                    ]
                ),
            )
        except (ValueError, TypeError):
            await update.message.reply_text(
                "❌ Некорректная цена! Введите число (например: 199.99):",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Отмена", callback_data="menu_management"
                            )
                        ]
                    ]
                ),
            )


async def admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление администраторами"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к этой функции.")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Добавить администратора", callback_data="add_admin")],
        [
            InlineKeyboardButton(
                "➖ Удалить администратора", callback_data="remove_admin"
            )
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")],
    ]

    await query.edit_message_text(
        "👥 *Управление администраторами*\n\n" "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик действий с администраторами"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к этой функции.")
        return

    action = query.data

    if action == "add_admin":
        context.user_data["admin_action"] = "adding_admin"
        await query.edit_message_text(
            "Отправьте Telegram ID пользователя, которого хотите сделать администратором:\n\n"
            "(для отмены нажмите кнопку ниже)",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Отмена", callback_data="admin_management")]]
            ),
        )

    elif action == "remove_admin":
        # Получаем список всех администраторов
        admins = db.get_all_admins()

        if not admins:
            await query.edit_message_text(
                "Список администраторов пуст.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Назад", callback_data="admin_management"
                            )
                        ]
                    ]
                ),
            )
            return

        keyboard = []
        for admin_id in admins:
            # Не показываем кнопку удаления для текущего админа
            if admin_id != query.from_user.id:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"❌ Удалить админа ID: {admin_id}",
                            callback_data=f"remove_admin_{admin_id}",
                        )
                    ]
                )

        keyboard.append(
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_management")]
        )

        await query.edit_message_text(
            "Выберите администратора для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def handle_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик удаления администратора через кнопку"""
    query = update.callback_query
    await query.answer()

    if not db.is_admin(query.from_user.id):
        await query.edit_message_text("У вас нет доступа к этой функции.")
        return

    target_id = int(query.data.split("_")[-1])

    if db.remove_admin(query.from_user.id, target_id):
        await query.edit_message_text(
            "✅ Администратор успешно удален!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data="admin_management")]]
            ),
        )
    else:
        await query.edit_message_text(
            "❌ Ошибка при удалении администратора.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Назад", callback_data="admin_management")]]
            ),
        )


async def handle_admin_management_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Обработчик входящих сообщений для управления администраторами"""
    if not update.message:
        return

    if "admin_action" not in context.user_data:
        return

    if not db.is_admin(update.effective_user.id):
        return

    action = context.user_data["admin_action"]

    # Получаем ID пользователя из пересланного сообщения или текста
    if update.message.forward_from:
        target_id = update.message.forward_from.id
    elif update.message.text:
        try:
            target_id = int(update.message.text)
        except ValueError:
            await update.message.reply_text(
                "❌ Некорректный ID! Пожалуйста, перешлите сообщение от пользователя "
                "или отправьте корректный Telegram ID.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Отмена", callback_data="admin_management"
                            )
                        ]
                    ]
                ),
            )
            return
    else:
        await update.message.reply_text(
            "❌ Пожалуйста, перешлите сообщение от пользователя или отправьте его Telegram ID.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Отмена", callback_data="admin_management")]]
            ),
        )
        return

    if action == "adding_admin":
        # Проверяем, не является ли пользователь уже админом
        if db.is_admin(target_id):
            await update.message.reply_text(
                "❌ Этот пользователь уже является администратором!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Назад", callback_data="admin_management"
                            )
                        ]
                    ]
                ),
            )
            return

        if db.add_admin(update.effective_user.id, target_id):
            await update.message.reply_text(
                "✅ Администратор успешно добавлен!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Назад", callback_data="admin_management"
                            )
                        ]
                    ]
                ),
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при добавлении администратора.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 Назад", callback_data="admin_management"
                            )
                        ]
                    ]
                ),
            )

    context.user_data.clear()


def main():
    """Основная функция запуска бота"""
    # Получение токена из переменных окружения
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found in environment variables")

    # Создание и настройка приложения
    application = Application.builder().token(token).build()

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_handler))
    application.add_handler(CommandHandler("orders", orders_handler))
    application.add_handler(CommandHandler("about", about_handler))

    # Добавление обработчиков для кнопок основного меню
    application.add_handler(CallbackQueryHandler(menu_handler, pattern="^menu$"))
    application.add_handler(CallbackQueryHandler(orders_handler, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
    application.add_handler(
        CallbackQueryHandler(back_to_main, pattern="^back_to_main$")
    )
    application.add_handler(CallbackQueryHandler(handle_order, pattern="^order_"))

    # Добавляем обработчики для корзины и заказов
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_to_cart_"))
    application.add_handler(
        CallbackQueryHandler(update_quantity, pattern="^(increase|decrease)_")
    )
    application.add_handler(CallbackQueryHandler(view_cart, pattern="^view_cart$"))
    application.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear_cart$"))
    application.add_handler(
        CallbackQueryHandler(confirm_order, pattern="^confirm_order$")
    )

    # Добавляем обработчик выбора времени (перемещен выше)
    application.add_handler(
        CallbackQueryHandler(handle_order_time, pattern="^time_(asap|15|30|45|60)$")
    )

    # Добавляем обработчики для админ-панели
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
    application.add_handler(
        CallbackQueryHandler(manage_orders, pattern="^manage_orders$")
    )
    application.add_handler(
        CallbackQueryHandler(complete_order, pattern="^complete_order_")
    )

    # Добавляем обработчики для управления меню
    application.add_handler(
        CallbackQueryHandler(admin_menu_management, pattern="^menu_management$")
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_menu_management,
            pattern="^(start_add_item|list_menu_items|delete_item_)",
        )
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_text), group=1
    )

    # Добавляем обработчики для управления администраторами
    application.add_handler(
        CallbackQueryHandler(admin_management, pattern="^admin_management$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_action, pattern="^(add_admin|remove_admin)$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_remove_admin, pattern="^remove_admin_[0-9]+$")
    )
    application.add_handler(
        MessageHandler(
            (filters.TEXT | filters.FORWARDED) & ~filters.COMMAND,
            handle_admin_management_input,
        ),
        group=0,
    )

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()
