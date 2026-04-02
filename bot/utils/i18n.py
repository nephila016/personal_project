"""Internationalization: Russian + Uzbek translations."""

TRANSLATIONS = {
    # ===== General =====
    "lang_selected": {
        "ru": "Язык установлен: Русский 🇷🇺",
        "uz": "Til tanlandi: O'zbekcha 🇺🇿",
    },
    "choose_language": {
        "ru": "Выберите язык / Tilni tanlang:",
        "uz": "Tilni tanlang / Выберите язык:",
    },
    "error_generic": {
        "ru": "Произошла ошибка. Попробуйте позже.",
        "uz": "Xatolik yuz berdi. Keyinroq urinib ko'ring.",
    },
    "register_first": {
        "ru": "Сначала зарегистрируйтесь через /start",
        "uz": "Avval /start orqali ro'yxatdan o'ting",
    },
    "account_deactivated": {
        "ru": "Ваш аккаунт деактивирован. Обратитесь в поддержку.",
        "uz": "Hisobingiz o'chirilgan. Qo'llab-quvvatlash xizmatiga murojaat qiling.",
    },

    # ===== Start / Registration =====
    "welcome_back": {
        "ru": "С возвращением, {name}!\n\nИспользуйте /order для нового заказа, /myorders для просмотра заказов или /help для списка всех команд.",
        "uz": "Qaytganingiz bilan, {name}!\n\n/order — yangi buyurtma, /myorders — buyurtmalar tarixi, /help — barcha buyruqlar.",
    },
    "welcome_new": {
        "ru": "Добро пожаловать в бот доставки воды! 💧\n\nДавайте зарегистрируем вас. Введите ваше полное имя:",
        "uz": "Suv yetkazib berish botiga xush kelibsiz! 💧\n\nRo'yxatdan o'tamiz. To'liq ismingizni kiriting:",
    },
    "enter_name": {
        "ru": "Введите ваше полное имя:",
        "uz": "To'liq ismingizni kiriting:",
    },
    "invalid_name": {
        "ru": "Имя должно содержать от 2 до 100 символов. Попробуйте ещё раз:",
        "uz": "Ism 2 dan 100 gacha belgi bo'lishi kerak. Qaytadan urinib ko'ring:",
    },
    "enter_address": {
        "ru": "Отлично! Теперь введите адрес доставки:",
        "uz": "Ajoyib! Endi yetkazib berish manzilini kiriting:",
    },
    "invalid_address": {
        "ru": "Адрес должен содержать от 1 до 500 символов. Попробуйте ещё раз:",
        "uz": "Manzil 1 dan 500 gacha belgi bo'lishi kerak. Qaytadan urinib ko'ring:",
    },
    "enter_phone": {
        "ru": "Теперь введите номер телефона (например, +998901234567):",
        "uz": "Telefon raqamingizni kiriting (masalan, +998901234567):",
    },
    "invalid_phone": {
        "ru": "Неверный номер телефона. Введите корректный номер (7-15 цифр, можно начинать с +):",
        "uz": "Noto'g'ri telefon raqami. To'g'ri raqam kiriting (7-15 raqam, + bilan boshlanishi mumkin):",
    },
    "phone_taken": {
        "ru": "Этот номер телефона уже зарегистрирован. Введите другой номер:",
        "uz": "Bu telefon raqami allaqachon ro'yxatdan o'tgan. Boshqa raqam kiriting:",
    },
    "confirm_registration": {
        "ru": "Пожалуйста, подтвердите данные регистрации:\n\nИмя: {name}\nАдрес: {address}\nТелефон: {phone}",
        "uz": "Ro'yxatdan o'tish ma'lumotlarini tasdiqlang:\n\nIsm: {name}\nManzil: {address}\nTelefon: {phone}",
    },
    "registration_complete": {
        "ru": "Регистрация завершена! ✅\n\nТеперь вы можете оформить заказ с помощью /order.\nИспользуйте /help для списка всех команд.",
        "uz": "Ro'yxatdan o'tish yakunlandi! ✅\n\n/order orqali buyurtma bering.\n/help — barcha buyruqlar ro'yxati.",
    },
    "registration_error": {
        "ru": "Ошибка регистрации: {error}\nПопробуйте снова с /start.",
        "uz": "Ro'yxatdan o'tishda xatolik: {error}\n/start orqali qaytadan urinib ko'ring.",
    },
    "registration_missing": {
        "ru": "Данные регистрации отсутствуют. Начните заново с /start.",
        "uz": "Ro'yxatdan o'tish ma'lumotlari topilmadi. /start orqali qaytadan boshlang.",
    },
    "registration_cancelled": {
        "ru": "Регистрация отменена. Вы можете начать заново в любое время с /start.",
        "uz": "Ro'yxatdan o'tish bekor qilindi. /start orqali istalgan vaqtda qaytadan boshlashingiz mumkin.",
    },

    # ===== Order =====
    "how_many_bottles": {
        "ru": "Сколько бутылок вы хотите заказать?",
        "uz": "Necha shisha buyurtma qilmoqchisiz?",
    },
    "enter_bottle_count": {
        "ru": "Введите количество бутылок (1-{max}):",
        "uz": "Shishalar sonini kiriting (1-{max}):",
    },
    "invalid_bottle_count": {
        "ru": "Неверное число. Введите число от 1 до {max}:",
        "uz": "Noto'g'ri son. 1 dan {max} gacha son kiriting:",
    },
    "delivery_notes_prompt": {
        "ru": "Примечания к доставке (ориентиры, инструкции)?\n\nНапишите или нажмите Пропустить.",
        "uz": "Yetkazib berish uchun izoh (mo'ljal, ko'rsatma)?\n\nYozing yoki O'tkazib yuborish tugmasini bosing.",
    },
    "notes_too_long": {
        "ru": "Примечания слишком длинные (макс. 500 символов). Сократите:",
        "uz": "Izoh juda uzun (maks. 500 belgi). Qisqartiring:",
    },
    "confirm_order": {
        "ru": "Подтвердите заказ:\n\nБутылки: {bottles}\nАдрес: {address}",
        "uz": "Buyurtmani tasdiqlang:\n\nShishalar: {bottles}\nManzil: {address}",
    },
    "confirm_order_notes": {
        "ru": "\nПримечания: {notes}",
        "uz": "\nIzoh: {notes}",
    },
    "order_placed": {
        "ru": "Заказ #{id} оформлен! ✅\n{bottles} бут. по адресу: {address}\n\nВы получите уведомление, когда администратор примет ваш заказ.",
        "uz": "#{id}-buyurtma qabul qilindi! ✅\n{bottles} shisha, manzil: {address}\n\nAdministrator buyurtmani qabul qilganda xabar olasiz.",
    },
    "order_error": {
        "ru": "Не удалось создать заказ: {error}",
        "uz": "Buyurtma yaratib bo'lmadi: {error}",
    },
    "order_cancelled": {
        "ru": "Заказ отменён.",
        "uz": "Buyurtma bekor qilindi.",
    },
    "enter_new_address": {
        "ru": "Введите новый адрес доставки:",
        "uz": "Yangi yetkazib berish manzilini kiriting:",
    },
    "enter_new_notes": {
        "ru": "Введите новые примечания к доставке (или 'нет' для очистки):",
        "uz": "Yangi yetkazib berish izohini kiriting (yoki 'yoq' tozalash uchun):",
    },
    "customer_not_found": {
        "ru": "Профиль не найден. Зарегистрируйтесь с помощью /start.",
        "uz": "Profil topilmadi. /start orqali ro'yxatdan o'ting.",
    },

    # ===== Reorder =====
    "no_previous_orders": {
        "ru": "У вас нет предыдущих доставленных заказов для повтора.\nИспользуйте /order для нового заказа.",
        "uz": "Takrorlash uchun oldingi yetkazilgan buyurtmalar yo'q.\n/order orqali yangi buyurtma bering.",
    },
    "reorder_confirm": {
        "ru": "Повторить последний заказ:\n\nБутылки: {bottles}\nАдрес: {address}\n\nПодтвердить или изменить количество?",
        "uz": "Oxirgi buyurtmani takrorlash:\n\nShishalar: {bottles}\nManzil: {address}\n\nTasdiqlash yoki miqdorni o'zgartirish?",
    },
    "reorder_cancelled": {
        "ru": "Повторный заказ отменён.",
        "uz": "Takroriy buyurtma bekor qilindi.",
    },
    "reorder_updated": {
        "ru": "Обновлённый заказ:\n\nБутылки: {count}\nАдрес: {address}\n\nПодтвердить или изменить снова?",
        "uz": "Yangilangan buyurtma:\n\nShishalar: {count}\nManzil: {address}\n\nTasdiqlash yoki qayta o'zgartirish?",
    },

    # ===== My Orders =====
    "no_orders_yet": {
        "ru": "У вас пока нет заказов.\nИспользуйте /order для оформления первого заказа!",
        "uz": "Sizda hali buyurtmalar yo'q.\n/order orqali birinchi buyurtmangizni bering!",
    },
    "your_orders_page": {
        "ru": "Ваши заказы (стр. {page}/{total}):",
        "uz": "Buyurtmalaringiz ({page}/{total}-sahifa):",
    },

    # ===== Cancel =====
    "no_pending_to_cancel": {
        "ru": "У вас нет ожидающих заказов для отмены.",
        "uz": "Bekor qilish uchun kutayotgan buyurtmalar yo'q.",
    },
    "cancel_this_order": {
        "ru": "Отменить этот заказ?",
        "uz": "Bu buyurtmani bekor qilasizmi?",
    },
    "which_order_cancel": {
        "ru": "Какой заказ вы хотите отменить?",
        "uz": "Qaysi buyurtmani bekor qilmoqchisiz?",
    },
    "order_cancelled_success": {
        "ru": "Заказ #{id} отменён.",
        "uz": "#{id}-buyurtma bekor qilindi.",
    },
    "order_cancel_failed": {
        "ru": "Не удалось отменить заказ #{id}. Возможно, он уже принят или отменён.",
        "uz": "#{id}-buyurtmani bekor qilib bo'lmadi. Ehtimol, u allaqachon qabul qilingan yoki bekor qilingan.",
    },
    "cancel_kept": {
        "ru": "Заказ сохранён. Изменения не внесены.",
        "uz": "Buyurtma saqlandi. O'zgarishlar kiritilmadi.",
    },
    "cancel_aborted": {
        "ru": "Отмена прервана.",
        "uz": "Bekor qilish to'xtatildi.",
    },
    "cancel_flow_exited": {
        "ru": "Отмена заказа прервана.",
        "uz": "Buyurtmani bekor qilish to'xtatildi.",
    },
    "not_needed": {
        "ru": "Не нужно",
        "uz": "Kerak emas",
    },

    # ===== Profile =====
    "your_profile": {
        "ru": "Ваш профиль\n-----------------------------\nИмя: {name}\nАдрес: {address}\nТелефон: {phone}\n-----------------------------\nСтатистика бутылок\n-----------------------------\n{stats}",
        "uz": "Profilingiz\n-----------------------------\nIsm: {name}\nManzil: {address}\nTelefon: {phone}\n-----------------------------\nShisha statistikasi\n-----------------------------\n{stats}",
    },
    "enter_new_name": {
        "ru": "Введите новое имя:",
        "uz": "Yangi ismni kiriting:",
    },
    "name_updated": {
        "ru": "Имя обновлено: {name}\n\nИспользуйте /profile для просмотра профиля.",
        "uz": "Ism yangilandi: {name}\n\n/profile orqali profilingizni ko'ring.",
    },
    "enter_new_delivery_address": {
        "ru": "Введите новый адрес доставки:",
        "uz": "Yangi yetkazib berish manzilini kiriting:",
    },
    "address_updated": {
        "ru": "Адрес обновлён: {address}\n\nИспользуйте /profile для просмотра профиля.",
        "uz": "Manzil yangilandi: {address}\n\n/profile orqali profilingizni ko'ring.",
    },
    "enter_new_phone": {
        "ru": "Введите новый номер телефона:",
        "uz": "Yangi telefon raqamini kiriting:",
    },
    "phone_updated": {
        "ru": "Телефон обновлён: {phone}\n\nИспользуйте /profile для просмотра профиля.",
        "uz": "Telefon yangilandi: {phone}\n\n/profile orqali profilingizni ko'ring.",
    },
    "profile_edit_cancelled": {
        "ru": "Редактирование профиля отменено.",
        "uz": "Profil tahrirlash bekor qilindi.",
    },

    # ===== Help =====
    "help_customer": {
        "ru": (
            "Команды клиента\n"
            "-----------------------------\n"
            "/start - Регистрация\n"
            "/order - Оформить заказ\n"
            "/reorder - Повторить последний заказ\n"
            "/myorders - История заказов\n"
            "/cancel - Отменить заказ\n"
            "/profile - Просмотр профиля\n"
            "/lang - Сменить язык\n"
            "/help - Показать команды"
        ),
        "uz": (
            "Mijoz buyruqlari\n"
            "-----------------------------\n"
            "/start - Ro'yxatdan o'tish\n"
            "/order - Buyurtma berish\n"
            "/reorder - Oxirgi buyurtmani takrorlash\n"
            "/myorders - Buyurtmalar tarixi\n"
            "/cancel - Buyurtmani bekor qilish\n"
            "/profile - Profilni ko'rish\n"
            "/lang - Tilni o'zgartirish\n"
            "/help - Buyruqlarni ko'rsatish"
        ),
    },
    "help_admin": {
        "ru": (
            "Команды администратора\n"
            "-----------------------------\n"
            "/pending - Ожидающие заказы\n"
            "/myactive - Ваши активные заказы\n"
            "/receive - Записать получение\n"
            "/returns - Записать возврат\n"
            "/customer - Поиск клиента\n"
            "/stock - Склад бутылок\n"
            "/help - Показать команды"
        ),
        "uz": (
            "Administrator buyruqlari\n"
            "-----------------------------\n"
            "/pending - Kutayotgan buyurtmalar\n"
            "/myactive - Faol buyurtmalaringiz\n"
            "/receive - Qabul qilishni yozish\n"
            "/returns - Qaytarishni yozish\n"
            "/customer - Mijozni qidirish\n"
            "/stock - Shisha ombori\n"
            "/help - Buyruqlarni ko'rsatish"
        ),
    },
    "help_not_registered": {
        "ru": "Вы ещё не зарегистрированы.\nИспользуйте /start для регистрации.",
        "uz": "Siz hali ro'yxatdan o'tmagansiz.\nRo'yxatdan o'tish uchun /start ni bosing.",
    },

    # ===== Notifications to customer =====
    "notif_order_preparing": {
        "ru": "Ваш заказ #{id} принят и готовится к доставке! 🚚",
        "uz": "#{id}-buyurtmangiz qabul qilindi va yetkazib berishga tayyorlanmoqda! 🚚",
    },
    "notif_order_delivered": {
        "ru": "Ваш заказ #{id} доставлен! ✅",
        "uz": "#{id}-buyurtmangiz yetkazib berildi! ✅",
    },
    "notif_order_cancelled": {
        "ru": "Ваш заказ #{id} отменён.\nПричина: {reason}\n\nИспользуйте /order для нового заказа.",
        "uz": "#{id}-buyurtmangiz bekor qilindi.\nSabab: {reason}\n\n/order orqali yangi buyurtma bering.",
    },

    # ===== Admin: Pending =====
    "no_pending_orders": {
        "ru": "Нет ожидающих заказов.",
        "uz": "Kutayotgan buyurtmalar yo'q.",
    },
    "pending_orders_header": {
        "ru": "Ожидающие заказы ({showing} из {total}):",
        "uz": "Kutayotgan buyurtmalar ({showing} / {total}):",
    },
    "claimed_order": {
        "ru": "Вы взяли заказ #{id}! ✅\n\nКлиент: {name}\nТелефон: {phone}\nАдрес: {address}\nБутылки: {bottles}",
        "uz": "#{id}-buyurtma qabul qilindi! ✅\n\nMijoz: {name}\nTelefon: {phone}\nManzil: {address}\nShishalar: {bottles}",
    },
    "claimed_notes": {
        "ru": "\nПримечания: {notes}",
        "uz": "\nIzoh: {notes}",
    },
    "already_claimed": {
        "ru": "Заказ #{id} уже взят другим администратором.",
        "uz": "#{id}-buyurtma boshqa administrator tomonidan qabul qilingan.",
    },

    # ===== Admin: Active =====
    "no_active_orders": {
        "ru": "У вас нет активных заказов. Используйте /pending для просмотра новых.",
        "uz": "Faol buyurtmalaringiz yo'q. /pending orqali yangilarini ko'ring.",
    },
    "your_active_orders": {
        "ru": "Ваши активные заказы:",
        "uz": "Faol buyurtmalaringiz:",
    },
    "order_delivered_success": {
        "ru": "Заказ #{id} доставлен! ✅\nОстаток на складе: {stock} бутылок.",
        "uz": "#{id}-buyurtma yetkazildi! ✅\nOmborda qoldiq: {stock} shisha.",
    },
    "insufficient_stock": {
        "ru": "Недостаточно запасов! У вас {stock} бутылок, а нужно {needed}.\nИспользуйте /receive для пополнения.",
        "uz": "Zaxira yetarli emas! Sizda {stock} shisha, kerak {needed}.\n/receive orqali to'ldiring.",
    },
    "enter_cancel_reason": {
        "ru": "Укажите причину отмены:",
        "uz": "Bekor qilish sababini kiriting:",
    },
    "admin_order_cancelled": {
        "ru": "Заказ #{id} отменён.",
        "uz": "#{id}-buyurtma bekor qilindi.",
    },
    "order_update_failed": {
        "ru": "Не удалось обновить заказ. Попробуйте снова.",
        "uz": "Buyurtmani yangilab bo'lmadi. Qaytadan urinib ko'ring.",
    },

    # ===== Admin: Receive =====
    "how_many_received": {
        "ru": "Сколько бутылок вы получили от поставщика?",
        "uz": "Yetkazib beruvchidan necha shisha oldingiz?",
    },
    "invalid_quantity": {
        "ru": "Введите корректное положительное число:",
        "uz": "To'g'ri musbat son kiriting:",
    },
    "receipt_notes_prompt": {
        "ru": "Примечания (поставщик, номер накладной)?\n\nНапишите или нажмите Пропустить.",
        "uz": "Izoh (yetkazuvchi, hujjat raqami)?\n\nYozing yoki O'tkazib yuborish tugmasini bosing.",
    },
    "confirm_receipt": {
        "ru": "Записать получение {qty} бутылок?",
        "uz": "{qty} shisha qabul qilinganini yozasizmi?",
    },
    "receipt_notes_line": {
        "ru": "\nПримечания: {notes}",
        "uz": "\nIzoh: {notes}",
    },
    "receipt_recorded": {
        "ru": "Записано! ✅ Получено {qty} бутылок.\nТекущий запас: {stock} бутылок.",
        "uz": "Yozildi! ✅ {qty} shisha qabul qilindi.\nJoriy zaxira: {stock} shisha.",
    },
    "receipt_cancelled": {
        "ru": "Запись отменена.",
        "uz": "Yozuv bekor qilindi.",
    },

    # ===== Admin: Returns =====
    "select_customer_for_return": {
        "ru": "Выберите клиента или введите номер телефона:",
        "uz": "Mijozni tanlang yoki telefon raqamini kiriting:",
    },
    "customer_not_found_returns": {
        "ru": "Клиент не найден. Введите номер телефона или /cancel для выхода.",
        "uz": "Mijoz topilmadi. Telefon raqamini kiriting yoki /cancel bosing.",
    },
    "how_many_returned": {
        "ru": "{name} ({in_hand} бут. на руках)\nСколько бутылок вернул?",
        "uz": "{name} ({in_hand} shisha qo'lida)\nNecha shisha qaytardi?",
    },
    "invalid_return_qty": {
        "ru": "Неверное количество. У клиента {in_hand} бутылок на руках.",
        "uz": "Noto'g'ri miqdor. Mijozda {in_hand} shisha bor.",
    },
    "confirm_return": {
        "ru": "Записать возврат {qty} бутылок от {name}?",
        "uz": "{name} dan {qty} shisha qaytarilganini yozasizmi?",
    },
    "return_recorded": {
        "ru": "Записано! ✅ {name} вернул {qty} бутылок.\nОсталось на руках: {remaining}.",
        "uz": "Yozildi! ✅ {name} {qty} shisha qaytardi.\nQo'lida qoldi: {remaining}.",
    },
    "return_cancelled": {
        "ru": "Запись возврата отменена.",
        "uz": "Qaytarish yozuvi bekor qilindi.",
    },
    "return_error": {
        "ru": "Ошибка: {error}",
        "uz": "Xatolik: {error}",
    },

    # ===== Admin: Customer lookup =====
    "enter_customer_search": {
        "ru": "Введите имя или номер телефона клиента:",
        "uz": "Mijoz ismi yoki telefon raqamini kiriting:",
    },
    "no_customers_found": {
        "ru": "Клиенты не найдены. Попробуйте другой запрос или /cancel.",
        "uz": "Mijozlar topilmadi. Boshqa so'rov kiriting yoki /cancel bosing.",
    },
    "select_customer": {
        "ru": "Найдено {count} клиентов. Выберите:",
        "uz": "{count} ta mijoz topildi. Tanlang:",
    },

    # ===== Admin: Stock =====
    "stock_header": {
        "ru": "Ваш склад бутылок",
        "uz": "Shisha omboringiz",
    },
    "stock_received": {
        "ru": "Получено от поставщика:  {n}",
        "uz": "Yetkazuvchidan olingan:  {n}",
    },
    "stock_delivered": {
        "ru": "Доставлено клиентам:     {n}",
        "uz": "Mijozlarga yetkazilgan:  {n}",
    },
    "stock_current": {
        "ru": "Текущий запас (полных):  {n}",
        "uz": "Joriy zaxira (to'la):    {n}",
    },
    "stock_empties": {
        "ru": "Собрано пустых:          {n}",
        "uz": "Yig'ilgan bo'sh:         {n}",
    },
    "stock_pending": {
        "ru": "Ожидание: {bottles} бут. в {orders} заказах",
        "uz": "Kutmoqda: {bottles} shisha {orders} ta buyurtmada",
    },
    "stock_low_warning": {
        "ru": "⚠️ Мало запасов! Используйте /receive для пополнения.",
        "uz": "⚠️ Zaxira kam! /receive orqali to'ldiring.",
    },

    # ===== Status labels =====
    "status_pending": {
        "ru": "Ожидание",
        "uz": "Kutmoqda",
    },
    "status_in_progress": {
        "ru": "В процессе",
        "uz": "Jarayonda",
    },
    "status_delivered": {
        "ru": "Доставлен",
        "uz": "Yetkazildi",
    },
    "status_canceled": {
        "ru": "Отменён",
        "uz": "Bekor qilindi",
    },

    # ===== Bottle stats =====
    "bs_total_ordered": {
        "ru": "Всего заказано:      {n}",
        "uz": "Jami buyurtma:       {n}",
    },
    "bs_total_delivered": {
        "ru": "Всего доставлено:    {n}",
        "uz": "Jami yetkazilgan:    {n}",
    },
    "bs_returned": {
        "ru": "Возвращено:          {n}",
        "uz": "Qaytarilgan:         {n}",
    },
    "bs_in_hand": {
        "ru": "Сейчас на руках:     {n}",
        "uz": "Hozir qo'lida:       {n}",
    },
    "bs_pending": {
        "ru": "Ожидание:            {n}",
        "uz": "Kutmoqda:            {n}",
    },

    # ===== Admin: Pending (extra) =====
    "pending_orders_page_header": {
        "ru": "Ожидающие заказы (стр. {page}/{total_pages}, всего {total})\n",
        "uz": "Kutayotgan buyurtmalar ({page}/{total_pages}-sahifa, jami {total})\n",
    },
    "order_line": {
        "ru": "#{id} - {name}\n{bottles} бутылок | {address}",
        "uz": "#{id} - {name}\n{bottles} shisha | {address}",
    },
    "order_line_notes": {
        "ru": "Примечание: {notes}",
        "uz": "Izoh: {notes}",
    },
    "claimed_order_full": {
        "ru": "Вы взяли заказ #{id}!\n\nЗаказ #{id}\nКлиент: {name}\nТелефон: {phone}\nАдрес: {address}\nБутылки: {bottles}",
        "uz": "#{id}-buyurtma qabul qilindi!\n\nBuyurtma #{id}\nMijoz: {name}\nTelefon: {phone}\nManzil: {address}\nShishalar: {bottles}",
    },
    "notif_order_accepted": {
        "ru": "Ваш заказ #{id} принят водителем и уже в пути!",
        "uz": "#{id}-buyurtmangiz haydovchi tomonidan qabul qilindi va yo'lda!",
    },

    # ===== Admin: Active (extra) =====
    "order_cannot_deliver": {
        "ru": "Заказ #{id} не может быть доставлен (уже доставлен, отменён или конфликт версий).",
        "uz": "#{id}-buyurtmani yetkazib bo'lmadi (allaqachon yetkazilgan, bekor qilingan yoki versiya ziddiyati).",
    },
    "insufficient_stock_deliver": {
        "ru": "Недостаточно запасов для доставки заказа #{id}.",
        "uz": "#{id}-buyurtmani yetkazish uchun zaxira yetarli emas.",
    },
    "order_delivered_stock": {
        "ru": "Заказ #{id} доставлен!\nОстаток на складе: {stock} бутылок.",
        "uz": "#{id}-buyurtma yetkazildi!\nOmborda qoldiq: {stock} shisha.",
    },
    "notif_order_delivered_customer": {
        "ru": "Ваш заказ #{id} ({bottles} бутылок) доставлен!",
        "uz": "#{id}-buyurtmangiz ({bottles} shisha) yetkazib berildi!",
    },
    "cancel_order_prompt": {
        "ru": "Отмена заказа #{id}.\nУкажите причину отмены (или /cancel для возврата):",
        "uz": "#{id}-buyurtmani bekor qilish.\nSababini kiriting (yoki /cancel qaytish uchun):",
    },
    "order_not_selected": {
        "ru": "Заказ не выбран. Используйте /myactive для начала.",
        "uz": "Buyurtma tanlanmagan. /myactive orqali boshlang.",
    },
    "order_cannot_cancel": {
        "ru": "Заказ #{id} не может быть отменён (уже доставлен, отменён или конфликт версий).",
        "uz": "#{id}-buyurtmani bekor qilib bo'lmadi (allaqachon yetkazilgan, bekor qilingan yoki versiya ziddiyati).",
    },
    "notif_order_cancelled_driver": {
        "ru": "Ваш заказ #{id} отменён водителем.\nПричина: {reason}",
        "uz": "#{id}-buyurtmangiz haydovchi tomonidan bekor qilindi.\nSabab: {reason}",
    },
    "cancel_aborted_admin": {
        "ru": "Отмена прервана.",
        "uz": "Bekor qilish to'xtatildi.",
    },

    # ===== Admin: Receive (extra) =====
    "how_many_received_full": {
        "ru": "Сколько бутылок вы получили от поставщика?\n(1 - {max})",
        "uz": "Yetkazib beruvchidan necha shisha oldingiz?\n(1 - {max})",
    },
    "enter_valid_quantity": {
        "ru": "Введите число от 1 до {max}.",
        "uz": "1 dan {max} gacha son kiriting.",
    },
    "add_receipt_note_prompt": {
        "ru": "Добавить примечание? (например, имя поставщика, номер накладной)\nВведите текст или нажмите Пропустить.",
        "uz": "Izoh qo'shasizmi? (masalan, yetkazuvchi nomi, hujjat raqami)\nMatn kiriting yoki O'tkazib yuborish tugmasini bosing.",
    },
    "confirm_receipt_text": {
        "ru": "Подтвердите приёмку:\n  Количество: {qty} бутылок",
        "uz": "Qabul qilishni tasdiqlang:\n  Miqdor: {qty} shisha",
    },
    "confirm_receipt_notes_line": {
        "ru": "  Примечание: {notes}",
        "uz": "  Izoh: {notes}",
    },
    "receipt_recorded_full": {
        "ru": "Записано! (приёмка #{id})\n  Добавлено: {qty} бутылок.\n  Ваш текущий запас: {stock} бутылок.",
        "uz": "Yozildi! (qabul #{id})\n  Qo'shildi: {qty} shisha.\n  Joriy zaxirangiz: {stock} shisha.",
    },
    "receipt_error": {
        "ru": "Произошла ошибка. Попробуйте /receive заново.",
        "uz": "Xatolik yuz berdi. /receive orqali qaytadan urinib ko'ring.",
    },
    "receipt_cancelled_admin": {
        "ru": "Приёмка отменена.",
        "uz": "Qabul qilish bekor qilindi.",
    },

    # ===== Admin: Returns (extra) =====
    "select_customer_or_phone": {
        "ru": "Выберите клиента или введите номер телефона для поиска.",
        "uz": "Mijozni tanlang yoki telefon raqamini kiriting.",
    },
    "no_recent_deliveries": {
        "ru": "Недавних доставок не найдено.\nВведите номер телефона клиента для поиска.",
        "uz": "Yaqinda yetkazilgan buyurtmalar topilmadi.\nMijoz telefon raqamini kiriting.",
    },
    "invalid_phone_format": {
        "ru": "Неверный формат номера. Введите корректный номер телефона.",
        "uz": "Noto'g'ri telefon formati. To'g'ri telefon raqamini kiriting.",
    },
    "customer_not_found_try_again": {
        "ru": "Клиент с таким номером не найден. Попробуйте снова или /cancel.",
        "uz": "Bu raqamli mijoz topilmadi. Qaytadan urinib ko'ring yoki /cancel bosing.",
    },
    "customer_not_found_short": {
        "ru": "Клиент не найден.",
        "uz": "Mijoz topilmadi.",
    },
    "return_customer_info": {
        "ru": "Клиент: {name}\nБутылок на руках: {in_hand}\n\nСколько бутылок вернул клиент?",
        "uz": "Mijoz: {name}\nQo'lidagi shishalar: {in_hand}\n\nMijoz necha shisha qaytardi?",
    },
    "enter_qty_range": {
        "ru": "Введите число от 1 до {max}.",
        "uz": "1 dan {max} gacha son kiriting.",
    },
    "customer_only_has": {
        "ru": "У клиента только {in_hand} бутылок. Введите корректное число.",
        "uz": "Mijozda faqat {in_hand} shisha bor. To'g'ri son kiriting.",
    },
    "add_note_or_skip": {
        "ru": "Добавить примечание? Введите текст или нажмите Пропустить.",
        "uz": "Izoh qo'shasizmi? Matn kiriting yoki O'tkazib yuborish tugmasini bosing.",
    },
    "confirm_return_text": {
        "ru": "Подтвердите возврат бутылок:\n  Клиент: {name}\n  Количество: {qty}",
        "uz": "Shisha qaytarishni tasdiqlang:\n  Mijoz: {name}\n  Miqdor: {qty}",
    },
    "confirm_return_notes_line": {
        "ru": "  Примечание: {notes}",
        "uz": "  Izoh: {notes}",
    },
    "return_recorded_full": {
        "ru": "Возврат записан (#{id}).\n  {qty} бутылок возвращено от {name}.\n  Бутылок на руках: {remaining}",
        "uz": "Qaytarish yozildi (#{id}).\n  {name} dan {qty} shisha qaytarildi.\n  Qo'lidagi shishalar: {remaining}",
    },
    "return_error_full": {
        "ru": "Ошибка: {error}",
        "uz": "Xatolik: {error}",
    },
    "return_error_retry": {
        "ru": "Произошла ошибка. Попробуйте /returns заново.",
        "uz": "Xatolik yuz berdi. /returns orqali qaytadan urinib ko'ring.",
    },
    "return_cancelled_admin": {
        "ru": "Запись возврата отменена.",
        "uz": "Qaytarish yozuvi bekor qilindi.",
    },

    # ===== Admin: Customer lookup (extra) =====
    "enter_name_or_phone": {
        "ru": "Введите имя или номер телефона клиента:",
        "uz": "Mijoz ismi yoki telefon raqamini kiriting:",
    },
    "enter_name_or_phone_short": {
        "ru": "Введите имя или номер телефона.",
        "uz": "Ism yoki telefon raqamini kiriting.",
    },
    "customers_not_found": {
        "ru": "Клиенты не найдены. Попробуйте другой запрос или /cancel.",
        "uz": "Mijozlar topilmadi. Boshqa so'rov kiriting yoki /cancel bosing.",
    },
    "found_n_customers": {
        "ru": "Найдено {count} клиентов. Выберите:",
        "uz": "{count} ta mijoz topildi. Tanlang:",
    },
    "customer_profile_header": {
        "ru": "Профиль клиента",
        "uz": "Mijoz profili",
    },
    "customer_detail_name": {
        "ru": "Имя:      {name}",
        "uz": "Ism:      {name}",
    },
    "customer_detail_phone": {
        "ru": "Телефон:  {phone}",
        "uz": "Telefon:  {phone}",
    },
    "customer_detail_address": {
        "ru": "Адрес:    {address}",
        "uz": "Manzil:   {address}",
    },
    "customer_detail_active": {
        "ru": "Активен:  {value}",
        "uz": "Faol:     {value}",
    },
    "customer_detail_registered": {
        "ru": "Дата рег: {date}",
        "uz": "Ro'yxatdan: {date}",
    },
    "yes": {"ru": "Да", "uz": "Ha"},
    "no": {"ru": "Нет", "uz": "Yo'q"},
    "na": {"ru": "Н/Д", "uz": "N/A"},
    "bottle_stats_header": {
        "ru": "Статистика бутылок",
        "uz": "Shisha statistikasi",
    },
    "recent_orders_header": {
        "ru": "Последние заказы (всего {total})",
        "uz": "Oxirgi buyurtmalar (jami {total})",
    },
    "no_orders_yet_short": {
        "ru": "Заказов пока нет.",
        "uz": "Hali buyurtmalar yo'q.",
    },
    "customer_search_cancelled": {
        "ru": "Поиск клиента отменён.",
        "uz": "Mijoz qidirish bekor qilindi.",
    },

    # ===== Admin: Stock (extra) =====
    "stock_separator": {
        "ru": "-----------------------------",
        "uz": "-----------------------------",
    },
    "stock_low_warning_full": {
        "ru": "Ваш запас ({current}) ниже порога предупреждения ({threshold}). Используйте /receive для пополнения.",
        "uz": "Zaxirangiz ({current}) ogohlantirish chegarasidan ({threshold}) past. /receive orqali to'ldiring.",
    },
    "stock_insufficient_for_pending": {
        "ru": "Ваш запас ({current}) меньше, чем требуется для ожидающих доставок ({pending} бутылок в {orders} заказах). Некоторые доставки могут быть невозможны.",
        "uz": "Zaxirangiz ({current}) kutayotgan yetkazishlar uchun yetarli emas ({pending} shisha {orders} ta buyurtmada). Ba'zi yetkazishlar amalga oshmasligi mumkin.",
    },

    # ===== Admin: keyboard (extra) =====
    "btn_claim_order": {"ru": "Взять #{id}", "uz": "Qabul #{id}"},
    "btn_delivered_order": {"ru": "Доставлен #{id}", "uz": "Yetkazildi #{id}"},
    "btn_cancel_order": {"ru": "Отменить #{id}", "uz": "Bekor #{id}"},
    "btn_on_hand_display": {"ru": "{name} - {in_hand} на руках", "uz": "{name} - {in_hand} qo'lida"},

    # ===== Keyboard labels =====
    "btn_confirm": {"ru": "Подтвердить", "uz": "Tasdiqlash"},
    "btn_cancel": {"ru": "Отмена", "uz": "Bekor qilish"},
    "btn_skip": {"ru": "Пропустить", "uz": "O'tkazib yuborish"},
    "btn_change_address": {"ru": "Изменить адрес", "uz": "Manzilni o'zgartirish"},
    "btn_change_notes": {"ru": "Изменить примечания", "uz": "Izohni o'zgartirish"},
    "btn_change_amount": {"ru": "Изменить количество", "uz": "Miqdorni o'zgartirish"},
    "btn_yes_cancel": {"ru": "Да, отменить", "uz": "Ha, bekor qilish"},
    "btn_no_keep": {"ru": "Нет, оставить", "uz": "Yo'q, qoldirish"},
    "btn_edit_name": {"ru": "Изменить имя", "uz": "Ismni o'zgartirish"},
    "btn_edit_address": {"ru": "Изменить адрес", "uz": "Manzilni o'zgartirish"},
    "btn_edit_phone": {"ru": "Изменить телефон", "uz": "Telefonni o'zgartirish"},
    "btn_prev": {"ru": "< Назад", "uz": "< Orqaga"},
    "btn_next": {"ru": "Вперёд >", "uz": "Oldinga >"},
    "btn_other": {"ru": "Другое", "uz": "Boshqa"},
    "btn_claim": {"ru": "Взять", "uz": "Qabul qilish"},
    "btn_delivered": {"ru": "Доставлен", "uz": "Yetkazildi"},
    "bottles_short": {"ru": "бут.", "uz": "shisha"},
    "btn_not_needed": {"ru": "Не нужно", "uz": "Kerak emas"},
    "btn_on_hand": {"ru": "на руках", "uz": "qo'lida"},
}

DEFAULT_LANG = "ru"


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """Get translated string. Falls back to Russian if key/lang missing."""
    lang = lang or DEFAULT_LANG
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(lang, entry.get(DEFAULT_LANG, f"[{key}]"))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def get_lang(context) -> str:
    """Get user's language from context.user_data."""
    return context.user_data.get("lang", DEFAULT_LANG)


def get_status_label(status: str, lang: str) -> str:
    """Get localized status label."""
    mapping = {
        "pending": "status_pending",
        "in_progress": "status_in_progress",
        "delivered": "status_delivered",
        "canceled": "status_canceled",
    }
    key = mapping.get(status, "")
    return t(key, lang) if key else status


def format_bottle_stats_i18n(stats: dict, lang: str) -> str:
    """Format bottle stats in the user's language."""
    return "\n".join([
        t("bs_total_ordered", lang, n=stats["total_ordered"]),
        t("bs_total_delivered", lang, n=stats["total_delivered"]),
        t("bs_returned", lang, n=stats["total_returned"]),
        t("bs_in_hand", lang, n=stats["bottles_in_hand"]),
        t("bs_pending", lang, n=stats["pending_bottles"]),
    ])


def format_order_short_i18n(data: dict, lang: str) -> str:
    """Format order short line in user's language."""
    status = get_status_label(data.get("status", ""), lang)
    created = data.get("created_at")
    date_str = created.strftime("%d.%m") if created else "—"
    bottles_label = t("bottles_short", lang)
    return f"#{data['id']} | {data['bottle_count']} {bottles_label} | {status} | {date_str}"
