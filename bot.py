import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import threading
import os

# === Prometheus метрики (с защитой от падения) ===
try:
    from prometheus_client import Counter, start_http_server

    ORDERS_TOTAL = Counter('streetfood_orders_total', 'Общее количество заказов', ['payment'])
    ORDERS_BY_DISH = Counter('streetfood_orders_by_dish', 'Заказы по блюдам', ['dish'])

    def start_metrics_server():
        try:
            start_http_server(8000)
            print("Prometheus metrics server started on port 8000")
        except Exception as e:
            print(f"Failed to start metrics server: {e}")

    threading.Thread(target=start_metrics_server, daemon=True).start()
except Exception as e:
    print(f"Failed to import or start Prometheus metrics: {e}")
    ORDERS_TOTAL = None
    ORDERS_BY_DISH = None

# === Google Sheets (с защитой от падения) ===
sheet = None
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_path = '/app/credentials.json'  # Путь из volumeMount в deployment.yaml
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    SHEET_ID = '1H_WmW28sCbymuhO8quPkvoOH6bYyzuoJ_8qjO09d34o'
    WORKSHEET_NAME = 'FastFoodOrders'
    sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    print("Google Sheets connected successfully")
except Exception as e:
    print(f"Failed to connect to Google Sheets: {e}")
    print("Bot will run without saving orders to Sheets!")

# === Конфиг ===
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN', '8464227500:AAF0qcol9pzCOSG4VJlz0KsZcdgVh5IeL6g')
OPERATOR_ID = 1888083882

MENU_ITEMS = {
    'Burger 🍔': 20000,
    'Pizza 🍕': 50000,
    'Fries 🍟': 10000,
    'Hot Dog 🌭': 15000,
    'Shawarma 🥙': 25000,
    'Sandwich 🥪': 18000,
    'Chicken Nuggets 🍗': 22000,
    'Salad 🥗': 15000,
    'Ice Cream 🍨': 10000,
    'Soda 🥤': 5000
}

TRANSLATIONS = {
    'eng': {
        'start': "Welcome! Choose your language:",
        'menu': "Main Menu",
        'order': "Place Order",
        'contact': "Contact Operator",
        'details': "My Orders",
        'choose_dish': "Choose dishes:",
        'cart': "Cart",
        'confirm_order': "Confirm Order",
        'clear_cart': "Clear Cart",
        'back': "Back",
        'payment': "Payment method:",
        'cash': "Cash 💵",
        'card': "Card 💳",
        'share_location': "Share location for delivery:",
        'order_confirmed': "Order placed! Waiting for operator.",
        'no_orders': "No orders yet.",
        'my_orders_info': "Order №{num} ({time})\nDishes: {dishes}\nFood: {food} UZS\nDelivery: {deliv} UZS\nTotal: {total} UZS\nPayment: {payment}\nStatus: {status}\n\n",
        'new_order_notify': "New order №{num}!\nClient: {username}\nLocation: {location_link}\nDishes: {dishes}\nTotal food: {total} UZS\nPayment: {payment}",
        'confirm': "Confirm",
        'set_delivery': "Set Delivery Cost",
        'decline': "Decline",
        'enter_delivery': "Enter delivery cost in UZS (e.g. 15000):",
        'delivery_set': "Delivery set: {cost} UZS. Total: {total} UZS. Order confirmed.",
        'show_history': "Show All Orders",
        'clear_sheet': "Clear All Orders",
        'operator_dashboard': "Operator Dashboard",
        'contact_method': "How to contact you?",
        'pm': "Message",
        'call': "Call",
        'share_contact': "Share phone number",
        'contact_sent': "Request sent to operator!",
    },
    'rus': {
        'start': "Добро пожаловать! Выберите язык:",
        'menu': "Главное меню",
        'order': "Оформить заказ",
        'contact': "Связаться с оператором",
        'details': "Мои заказы",
        'choose_dish': "Выберите блюда:",
        'cart': "Корзина",
        'confirm_order': "Подтвердить заказ",
        'clear_cart': "Очистить корзину",
        'back': "Назад",
        'payment': "Способ оплаты:",
        'cash': "Наличными 💵",
        'card': "Картой 💳",
        'share_location': "Поделитесь геолокацией:",
        'order_confirmed': "Заказ принят! Ожидайте подтверждения.",
        'no_orders': "Заказов пока нет.",
        'my_orders_info': "Заказ №{num} ({time})\nБлюда: {dishes}\nЕда: {food} UZS\nДоставка: {deliv} UZS\nИтого: {total} UZS\nОплата: {payment}\nСтатус: {status}\n\n",
        'new_order_notify': "Новый заказ №{num}!\nКлиент: {username}\nГеолокация: {location_link}\nБлюда: {dishes}\nСумма еды: {total} UZS\nОплата: {payment}",
        'confirm': "Подтвердить",
        'set_delivery': "Указать доставку",
        'decline': "Отклонить",
        'enter_delivery': "Введите стоимость доставки в UZS (например: 15000):",
        'delivery_set': "Доставка: {cost} UZS. Итого: {total} UZS. Заказ подтверждён.",
        'show_history': "Показать все заказы",
        'clear_sheet': "Очистить все заказы",
        'operator_dashboard': "Панель оператора",
        'contact_method': "Как с вами связаться?",
        'pm': "Сообщение",
        'call': "Позвонить",
        'share_contact': "Поделиться номером",
        'contact_sent': "Запрос отправлен оператору!",
    },
    'uzb': {
        'start': "Xush kelibsiz! Tilni tanlang:",
        'menu': "Asosiy menyu",
        'order': "Buyurtma berish",
        'contact': "Operator bilan bog'lanish",
        'details': "Mening buyurtmalarim",
        'choose_dish': "Taomlarni tanlang:",
        'cart': "Savatcha",
        'confirm_order': "Buyurtmani tasdiqlash",
        'clear_cart': "Savatchani tozalash",
        'back': "Orqaga",
        'payment': "To'lov turi:",
        'cash': "Naqd 💵",
        'card': "Karta 💳",
        'share_location': "Yetkazib berish uchun joylashuvni yuboring:",
        'order_confirmed': "Buyurtma qabul qilindi! Operator tasdiqlashini kuting.",
        'no_orders': "Hozircha buyurtmalar yo'q.",
        'my_orders_info': "Buyurtma №{num} ({time})\nTaomlar: {dishes}\nOvqat: {food} UZS\nYetkazib berish: {deliv} UZS\nJami: {total} UZS\nTo'lov: {payment}\nHolati: {status}\n\n",
        'new_order_notify': "Yangi buyurtma №{num}!\nMijoz: {username}\nJoylashuv: {location_link}\nTaomlar: {dishes}\nOvqat summasi: {total} UZS\nTo'lov: {payment}",
        'confirm': "Tasdiqlash",
        'set_delivery': "Yetkazib berish narxini belgilash",
        'decline': "Rad etish",
        'enter_delivery': "Yetkazib berish narxini UZS da kiriting (masalan: 15000):",
        'delivery_set': "Yetkazib berish: {cost} UZS. Jami: {total} UZS. Buyurtma tasdiqlandi.",
        'show_history': "Barcha buyurtmalarni ko'rsatish",
        'clear_sheet': "Barcha buyurtmalarni tozalash",
        'operator_dashboard': "Operator paneli",
        'contact_method': "Siz bilan qanday bog'lanaylik?",
        'pm': "Xabar",
        'call': "Qo'ng'iroq",
        'share_contact': "Telefon raqamni yuboring",
        'contact_sent': "So'rov operatorga yuborildi!",
    }
}

user_data = {}
operator_state = {}

bot = telebot.TeleBot(BOT_TOKEN)

def get_text(user_id, key, **kwargs):
    lang = user_data.get(user_id, {}).get('lang', 'rus')
    return TRANSLATIONS.get(lang, TRANSLATIONS['rus'])[key].format(**kwargs)

def show_main_menu(chat_id, user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    if user_id == OPERATOR_ID:
        markup.add(KeyboardButton(get_text(user_id, 'show_history')))
        markup.add(KeyboardButton(get_text(user_id, 'clear_sheet')))
        bot.send_message(chat_id, "🔧 " + get_text(user_id, 'operator_dashboard'), reply_markup=markup)
    else:
        markup.add(KeyboardButton(get_text(user_id, 'order') + " 📝"))
        markup.add(KeyboardButton(get_text(user_id, 'contact') + " 📞"))
        markup.add(KeyboardButton(get_text(user_id, 'details') + " ℹ️"))
        bot.send_message(chat_id, "🍔 " + get_text(user_id, 'menu'), reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(KeyboardButton('English 🇬🇧'), KeyboardButton('Русский 🇷🇺'), KeyboardButton('Oʻzbek 🇺🇿'))
    bot.send_message(message.chat.id, "🌟 " + get_text(user_id, 'start'), reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ['English 🇬🇧', 'Русский 🇷🇺', 'Oʻzbek 🇺🇿'])
def choose_language(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    lang_map = {'English 🇬🇧': 'eng', 'Русский 🇷🇺': 'rus', 'Oʻzbek 🇺🇿': 'uzb'}
    user_data[user_id]['lang'] = lang_map[message.text]
    show_main_menu(message.chat.id, user_id)

@bot.message_handler(func=lambda m: get_text(m.from_user.id, 'order') in m.text and m.from_user.id != OPERATOR_ID)
def place_order(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    markup = InlineKeyboardMarkup(row_width=2)
    for dish, price in MENU_ITEMS.items():
        markup.add(InlineKeyboardButton(f"{dish} ({price} UZS)", callback_data=f"add_{dish}"))
    markup.add(InlineKeyboardButton(get_text(user_id, 'cart') + " 🛒", callback_data="view_cart"))
    markup.add(InlineKeyboardButton(get_text(user_id, 'clear_cart') + " ❌", callback_data="clear_cart"))
    markup.add(InlineKeyboardButton(get_text(user_id, 'back') + " 🔙", callback_data="back"))
    bot.send_message(message.chat.id, "🍽️ " + get_text(user_id, 'choose_dish'), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def add_to_cart(call):
    user_id = call.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    dish = call.data[4:]
    user_data[user_id]['cart'][dish] = user_data[user_id]['cart'].get(dish, 0) + 1
    bot.answer_callback_query(call.id, f"Добавлено: {dish}")

@bot.callback_query_handler(func=lambda call: call.data == 'view_cart')
def view_cart(call):
    user_id = call.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    cart = user_data[user_id]['cart']
    if not cart:
        bot.answer_callback_query(call.id, "Корзина пуста!")
        return
    total = sum(MENU_ITEMS[d] * q for d, q in cart.items())
    text = "\n".join([f"{d} x{q} = {MENU_ITEMS[d]*q} UZS" for d, q in cart.items()])
    msg = f"🛒 Корзина:\n{text}\n\nИтого: {total} UZS"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(get_text(user_id, 'confirm_order') + " ✅", callback_data="confirm_order"))
    markup.add(InlineKeyboardButton(get_text(user_id, 'back'), callback_data="back"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_order')
def confirm_order(call):
    user_id = call.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_text(user_id, 'cash')), KeyboardButton(get_text(user_id, 'card')))
    bot.send_message(call.message.chat.id, "💰 " + get_text(user_id, 'payment'), reply_markup=markup)
    user_data[user_id]['state'] = 'payment'

@bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'payment')
def get_payment(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    if message.text not in [get_text(user_id, 'cash'), get_text(user_id, 'card')]:
        return
    user_data[user_id]['payment'] = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_text(user_id, 'share_location'), request_location=True))
    bot.send_message(message.chat.id, get_text(user_id, 'share_location'), reply_markup=markup)
    user_data[user_id]['state'] = 'location'

@bot.message_handler(content_types=['location'], func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'location')
def save_order(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    if not user_data[user_id].get('cart', {}):
        bot.send_message(message.chat.id, "Корзина пуста!")
        return

    lat = message.location.latitude
    lon = message.location.longitude
    location_coords = f"{lat},{lon}"
    location_link = f"https://maps.google.com/?q={lat},{lon}"

    username = message.from_user.username if message.from_user.username else "не указан"
    username_display = f"@{username}" if username != "не указан" else username

    cart = user_data[user_id]['cart']
    payment = user_data[user_id]['payment']
    order_total = sum(MENU_ITEMS[d] * q for d, q in cart.items())
    dishes_text = ", ".join([f"{d} x{q}" for d, q in cart.items()])
    timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    # Сохранение в Google Sheets (если доступно)
    if sheet:
        try:
            all_rows = sheet.get_all_values()
            order_num = len(all_rows) if all_rows else 1

            row = [
                order_num,
                timestamp,
                user_id,
                username_display,
                dishes_text,
                order_total,
                0,
                order_total,
                payment,
                "pending",
                location_coords
            ]
            sheet.append_row(row)
        except Exception as e:
            print(f"Failed to save order to Sheets: {e}")
            order_num = "N/A (Sheets unavailable)"
    else:
        order_num = "N/A (Sheets unavailable)"

    # === МЕТРИКИ (защищённо) ===
    if ORDERS_TOTAL:
        ORDERS_TOTAL.labels(payment=payment).inc()
    if ORDERS_BY_DISH:
        for dish, qty in cart.items():
            ORDERS_BY_DISH.labels(dish=dish).inc(qty)

    bot.send_message(message.chat.id, f"✅ Заказ №{order_num} принят! Ожидайте подтверждения.")
    show_main_menu(message.chat.id, user_id)
    user_data[user_id]['cart'] = {}
    if 'state' in user_data[user_id]:
        del user_data[user_id]['state']

    # Уведомление оператору
    msg = get_text(OPERATOR_ID, 'new_order_notify', num=order_num, username=username_display, location_link=location_link, dishes=dishes_text, total=order_total, payment=payment)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(get_text(OPERATOR_ID, 'confirm'), callback_data=f"confirm_{order_num}"))
    markup.add(InlineKeyboardButton(get_text(OPERATOR_ID, 'set_delivery'), callback_data=f"delivery_{order_num}"))
    markup.add(InlineKeyboardButton(get_text(OPERATOR_ID, 'decline'), callback_data=f"decline_{order_num}"))
    bot.send_message(OPERATOR_ID, f"🔔 {msg}", reply_markup=markup)

# Остальные handlers (без изменений, они стабильные)
@bot.message_handler(func=lambda m: get_text(m.from_user.id, 'contact') in m.text and m.from_user.id != OPERATOR_ID)
def contact_operator(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_text(user_id, 'pm')), KeyboardButton(get_text(user_id, 'call')))
    bot.send_message(message.chat.id, get_text(user_id, 'contact_method'), reply_markup=markup)
    user_data[user_id]['state'] = 'contact_method'

@bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'contact_method')
def choose_contact_method(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    method = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(get_text(user_id, 'share_contact'), request_contact=True))
    bot.send_message(message.chat.id, get_text(user_id, 'share_contact'), reply_markup=markup)
    user_data[user_id]['contact_method'] = method
    user_data[user_id]['state'] = 'share_contact'

@bot.message_handler(content_types=['contact'], func=lambda m: user_data.get(m.from_user.id, {}).get('state') == 'share_contact')
def receive_contact(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    username = message.from_user.username if message.from_user.username else "не указан"
    username_display = f"@{username}" if username != "не указан" else username
    phone = message.contact.phone_number
    method = user_data[user_id]['contact_method']
    bot.send_message(OPERATOR_ID, f"Запрос связи\nКлиент: {username_display} (ID: {user_id})\nСпособ: {method}\nТелефон: {phone}")
    bot.send_message(message.chat.id, get_text(user_id, 'contact_sent'))
    show_main_menu(message.chat.id, user_id)
    if 'state' in user_data[user_id]:
        del user_data[user_id]['state']

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def confirm_only(call):
    if not sheet:
        bot.answer_callback_query(call.id, "Sheets недоступен")
        return
    order_num = call.data.split('_')[1]
    update_status(order_num, "confirmed")
    bot.answer_callback_query(call.id, "Заказ подтверждён")

@bot.callback_query_handler(func=lambda call: call.data.startswith('decline_'))
def decline_order(call):
    if not sheet:
        bot.answer_callback_query(call.id, "Sheets недоступен")
        return
    order_num = call.data.split('_')[1]
    update_status(order_num, "declined")
    bot.answer_callback_query(call.id, "Заказ отклонён")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delivery_'))
def ask_delivery_cost(call):
    if not sheet:
        bot.answer_callback_query(call.id, "Sheets недоступен")
        return
    order_num = call.data.split('_')[1]
    operator_state[OPERATOR_ID] = {'order_num': order_num}
    bot.send_message(OPERATOR_ID, get_text(OPERATOR_ID, 'enter_delivery'))
    bot.answer_callback_query(call.id, "Жду сумму")

@bot.message_handler(func=lambda m: m.from_user.id == OPERATOR_ID and operator_state.get(OPERATOR_ID))
def set_delivery_cost(message):
    if not sheet:
        bot.send_message(OPERATOR_ID, "Sheets недоступен")
        return
    try:
        cost = int(message.text.strip())
        if cost < 0:
            raise ValueError
        order_num = operator_state[OPERATOR_ID]['order_num']
        rows = sheet.get_all_values()
        for i, row in enumerate(rows):
            if row[0] == str(order_num):
                food_total = int(row[5])
                total = food_total + cost
                sheet.update_cell(i+1, 7, cost)
                sheet.update_cell(i+1, 8, total)
                sheet.update_cell(i+1, 10, "confirmed")
                break
        bot.send_message(OPERATOR_ID, get_text(OPERATOR_ID, 'delivery_set', cost=cost, total=total))
        del operator_state[OPERATOR_ID]
    except:
        bot.send_message(OPERATOR_ID, "Введите число (например: 15000)")

def update_status(order_num, status):
    if not sheet:
        return
    rows = sheet.get_all_values()
    for i, row in enumerate(rows):
        if row[0] == str(order_num):
            sheet.update_cell(i+1, 10, status)
            break

@bot.message_handler(func=lambda m: get_text(m.from_user.id, 'details') in m.text and m.from_user.id != OPERATOR_ID)
def my_orders(message):
    user_id = message.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    if not sheet:
        bot.send_message(message.chat.id, "История заказов недоступна")
        return
    rows = sheet.get_all_values()[1:] if sheet.get_all_values() else []
    user_orders = [r for r in rows if len(r) > 2 and r[2] == str(user_id)]
    if not user_orders:
        bot.send_message(message.chat.id, get_text(user_id, 'no_orders'))
        return
    msg = "📋 Ваши заказы:\n\n"
    for row in user_orders:
        msg += get_text(user_id, 'my_orders_info', num=row[0], time=row[1], dishes=row[4],
                        food=row[5], deliv=row[6], total=row[7], payment=row[8], status=row[9])
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: get_text(m.from_user.id, 'show_history') in m.text and m.from_user.id == OPERATOR_ID)
def all_orders(message):
    if not sheet:
        bot.send_message(message.chat.id, "История недоступна")
        return
    rows = sheet.get_all_values()[1:] if sheet.get_all_values() else []
    if not rows:
        bot.send_message(message.chat.id, "Нет заказов.")
        return
    msg = "📋 Все заказы:\n\n"
    for row in rows:
        location = row[10] if len(row) > 10 else "Не указана"
        location_link = f"https://maps.google.com/?q={location}" if location != "Не указана" else "Не указана"
        msg += f"№{row[0]} | {row[1]} | {row[3]} | {row[4]} | {row[5]} + {row[6]} = {row[7]} UZS | {row[8]} | {row[9]}\nГеолокация: {location_link}\n\n"
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: get_text(m.from_user.id, 'clear_sheet') in m.text and m.from_user.id == OPERATOR_ID)
def clear_all(message):
    if not sheet:
        bot.send_message(message.chat.id, "Sheets недоступен")
        return
    sheet.clear()
    headers = ['Order_Num', 'Timestamp', 'User_ID', 'Username', 'Dishes', 'Order_Total', 'Delivery_Cost', 'Total_With_Delivery', 'Payment_Type', 'Status', 'Location']
    sheet.append_row(headers)
    bot.send_message(message.chat.id, "🗑️ Все заказы очищены. Заголовки в первой строке.")

@bot.callback_query_handler(func=lambda call: call.data in ['back', 'clear_cart'])
def back_handlers(call):
    user_id = call.from_user.id
    user_data[user_id] = user_data.get(user_id, {'cart': {}, 'lang': 'rus'})
    if call.data == 'clear_cart':
        user_data[user_id]['cart'] = {}
        bot.answer_callback_query(call.id, "Корзина очищена")
    show_main_menu(call.message.chat.id, user_id)

print("Bot starting...")
bot.infinity_polling(non_stop=True)