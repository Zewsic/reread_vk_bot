from vkbottle import Keyboard, Text, OpenLink, Callback, KeyboardButtonColor


class VK:
    TOKEN = "vk1.a.pQJLl1LmrjMZUFa47N94akrLIPl7sk5CmEqg44qCLnLKJ_fP48geAIzI3jDgc0FSt7ta7EhR_-4iQURh5V8o3NVxcA9qKHeSd_TAsTpZ8XAjVcHmA2eIEnoyXmZiJa8zUk5kg5ZPWmg1FYpiiFFxWhzNfum20s5plZdc1NTcQadNcRau-M4C2LBSmNWqj_8NlC8jVFgw0IW1KQXy5wQWAQ"
    GROUP_ID = "223602353"
    USER_TOKEN = "vk1.a.raUxRuazUci4PmrHjPaA3put0wnYQ53pFj_x36EpEx06Gtbm09uedSaKQJr8IEaK5lT9zoeMCib0b9F8bSuGFce4PX7vuyMfXk-GNQyHp3yiRxqMJ1y0Up4CxwQk6YrEtnLEzZyCGYjzuZFyrzw0hhXfH8IMUjKvISc0WQko2dB_i_6pi_8rgp02lzP4PdIKiWC0t5n2yb_fQgjclPfngA"

class DataBase:
    TYPE = "sqlite"  # sqlite or mysql
    SQLITE_PATH = "reread.db"
    MYSQL_HOST = "127.0.0.1"
    MYSQL_PORT = "3388"
    MYSQL_USER = "reread_user"
    MYSQL_PASS = "d6f76dvs5xv67xrx"


class Roles:
    OWNERS = []  # Owners of bot


class Constants:
    SUPPORT_URL = "https://vk.com/zewsic"

    SUPPORT_KEYBOARD = Keyboard(inline=True).add(OpenLink(SUPPORT_URL, "Обратиться в поддержку")).get_json()

    BANNED_MESSAGE = "Ваша учетная запись заблокирована администратором.\nПричина блокировки: %s"
    SOME_ERROR_MESSAGE = "Произошла ошибка: %s\nОбратитесь в поддержку для решения проблемы."
    MEMBER_PROFILE_MESSAGE = "Добрый день, %s!\n\nВы участвуете в %s номинациях."
    MEMBER_SELECT_GROUP_MESSAGE = "Хотите принять участие? Отлично!\nСперва выберите группу."
    MEMBER_SELECT_NOMINATION_MESSAGE = "Отлично! Теперь, выберите номинацию для участия."
    MEMBER_VERIFY_SELECTION_TEXT = ("Обратите внимание, что после оплаты вы не сможете изменить вашу группу и номинацию.\nТакже, у вас будет определенный дедлайн на отправку вашей работы. Если вы не успеете отправить работу, ваша анкета будет аннулирована, деньги вернуть не получится.\n\nНоминация: %s\nГруппа: %s\nВремя на отправку работы: %s минут\nСтоимость участия: %s рублей."
                                    "\n\nИнформация о номинанте:\nФ.И.О.: %s\nШкола: %s\nEmail: %s\nТелефон: %s\nУчитель: %s\n\nПодтвердите ваши намеренья учавствовать.")
    NEED_PAY_MESSAGE = "Оплатите участие для получения текста."
    PAY_NOT_FOUND_MESSAGE = "Оплата не найдена, обратитесь в поддержку."
    PAY_FOUND_MESSAGE = "Оплата обнаружена, благодарим за участие!"
    PLEASE_WAIT_MESSAGE = "Пожалуйста, подождите..."
    PAYED_SUCCESS = "Благодарим за оплату! Для получения текста и другой информацию перейдите в раздел ваших участий."
    NO_PLAYS_MESSAGE = "Вы не участвуете ни в одной номинации."

    VERIFY_TEXT = "Подтвердить"
    CANCEL_TEXT = "Отменить"
    MAIN_MENU_TEXT = "В главное меню"
    PREV_TEXT = "Назад"
    LETS_PLAY_TEXT = "Учавствовать"
    PLAYS_TEXT = "Мои участия"
    PLAYS_LABEL = "Вот список конкурсов в которых вы участвуете:"

    USER_CONTEST_INFO = """Информация об участии #%s
Номинация: %s
Группа: %s
Дата начала: %s
Дата окончания: %s
Статус: %s

Информация о номинанте:
Ф.И.О: %s
Школа: %s
Email: %s
Телефон: %s
Учитель: %s

Текст: %s
Необходимо отправить отклик до: %s
Статус отклика: %s
"""

    POST_TEXT = """Работа: #%s
Категория: #%s
Номинация: #%s

Автор: #%s
Название произведения: %s

Проголосовать за работу можно по ссылке ниже: 
%s"""