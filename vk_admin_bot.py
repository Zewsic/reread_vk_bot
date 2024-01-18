import time
from datetime import datetime

from vkbottle import Keyboard, Callback, Text, KeyboardButtonColor
from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadContainsRule
from vkbottle_types.events import GroupEventType

from config import Constants
from reread_types import *
from vk_bot import users_actions, bot


def get_vk_from_txt(string: str):
    prefixxes = ["https://vk.com/", "https://vk.com/id", "vk.com/", "vk.com/id", "id", "@id"]
    for prefix in prefixxes:
        if string.startswith(prefix):
            string = string[len(prefix):]
    return int(string)


def text_to_date(text: str):
    try:
        return datetime.strptime(text, "%d.%m.%Y %H:%M").timestamp()
    except:
        return None


admins_as_experts = {}


async def one_message(message: Message, msg: str = "", user: User = None):
    vk_user = await message.get_user()
    if "главное меню" in msg.lower() or users_actions.get(vk_user.id, None) is None:
        users_actions[vk_user.id] = None

        all_active_contests = UserContest.get_all_non_finished()
        group_active_contests = {}
        for group in ContestGroup.get_all_groups():
            group_active_contests[group.id] = []
            for contest in all_active_contests:
                if contest.group.id == group.id:
                    group_active_contests[group.id].append(contest)
        nomination_group_len_matrix = {}
        for nomination in ContestNomination.get_all_nominations():
            nomination_group_len_matrix[nomination.id] = {}
            for group in ContestGroup.get_all_groups():
                nomination_group_len_matrix[nomination.id][group.id] = 0
        for contest in all_active_contests:
            nomination_group_len_matrix[contest.nomination.id][contest.group.id] += 1

        await message.answer("Меню администратора\n\n"
                             "Участников: %s = %s\n"
                             "( %s )\n"
                             "%s\n\n"
                             "Дата начала приема заявок: %s\n"
                             "Дата окончания приема заявок: %s\n"
                             "Дата подведения итогов: %s\n"
                             "Количество времени на подготовку: %s минут\n"
                             "Стоимость участия: %s руб." % (
                                 len(all_active_contests),
                                 " / ".join([str(len(group_active_contests[group.id])) for group in ContestGroup.get_all_groups()]),
                                 " / ".join([group.name for group in ContestGroup.get_all_groups()]),
                                 "\n".join(["%s: %s" % (nomination.name, " / ".join([str(nomination_group_len_matrix[nomination.id][group.id]) for group in ContestGroup.get_all_groups()])) for nomination in
                                            ContestNomination.get_all_nominations()]),
                                 datetime.fromtimestamp(Contest.get_by_id(-1).start_date).strftime("%d.%m.%Y %H:%M"),
                                 datetime.fromtimestamp(Contest.get_by_id(-1).finish_date).strftime("%d.%m.%Y %H:%M"),
                                 datetime.fromtimestamp(Contest.get_by_id(-1).winners_date).strftime("%d.%m.%Y %H:%M"),
                                 Contest.get_by_id(-1).time_for_send,
                                 Contest.get_by_id(-1).price
                             ),
                             keyboard=Keyboard(inline=True)
                             .add(Callback("Настройка текстов", {"cmd": "admin_texts"})).row()
                             .add(Callback("Рейтинг", {"cmd": "admin_raiting"})).row()
                             .add(Callback("Эксперты", {"cmd": "admin_expert"})).row()
                             .add(Callback("Пользователи", {"cmd": "admin_users"})).row()
                             .add(Callback("Параметры конкурса", {"cmd": "admin_settings"})).get_json())

        return

    if users_actions[vk_user.id]["cmd"] == "edit_text_param":
        text_id = users_actions[vk_user.id]["text_id"]
        param = users_actions[vk_user.id]["param"]

        text = ContestText.get_by_id(text_id)
        if param == "name":
            text.name = msg
        elif param == "author":
            text.author = msg
        elif param == "text":
            text.text = msg
        text.save_to_db()

        await message.answer("Изменено", keyboard=Keyboard(inline=True).add(Callback("К тексту", {"cmd": "admin_texts", "type": "edit_text", "text_id": text_id, "nomination_id": text.nomination.id, "group_id": text.group.id})).get_json())
        users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "add_expert":
        try:
            if users_actions[vk_user.id].get("expert_id") is None:
                users_actions[vk_user.id]["expert_id"] = get_vk_from_txt(msg)
                await message.answer("Введите id номинаций через пробел: \n\n" + "\n".join(["%s: %s" % (nomination.id, nomination.name) for nomination in ContestNomination.get_all_nominations()]),
                                     keyboard=Keyboard(inline=True).add(Text("Все")).add(Callback("Назад", {"cmd": "admin_expert", "type": "add"})).get_json())
            else:
                expert = User.get_by_vk_id(users_actions[vk_user.id]["expert_id"])
                if expert is None:
                    await message.answer("Пользователь не найден", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_expert", "type": "add"})).get_json())
                    return
                if msg.lower() == "все":
                    nominations = []
                else:
                    nominations = [int(x) for x in msg.split(" ")]
                    for nomination_id in nominations:
                        nomination = ContestNomination.get_by_id(nomination_id)
                        if nomination is None:
                            await message.answer("Одна из номинаций не найдена", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_expert", "type": "add"})).get_json())
                            return
                expert.role = "expert"
                expert.expert_nominations = nominations
                expert.save_to_db()
                await message.answer("Эксперт добавлен", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_expert", "type": "main"})).get_json())
                users_actions[vk_user.id] = None
        except:
            await message.answer("Ошибка", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_expert", "type": "main"})).get_json())
            users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "delete_expert":
        expert_id = users_actions[vk_user.id].get("expert_id", None)
        expert = User.get_by_vk_id(get_vk_from_txt(msg) if expert_id is None else expert_id)
        if expert is None:
            await message.answer("Пользователь не найден", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_expert", "type": "delete"})).get_json())
            return
        if expert_id is None:
            users_actions[vk_user.id]["expert_id"] = get_vk_from_txt(msg)
            await message.answer("Вы уверены, что хотите удалить эксперта %s %s @id%s?" % (expert.first_name, expert.last_name, expert.vk_id), keyboard=Keyboard(inline=True).add(Text("Да")).add(
                Callback("Нет", {"cmd": "admin_expert", "type": "main"})).get_json())
        else:
            expert.role = "member"
            expert.expert_nominations = []
            expert.save_to_db()
            await message.answer("Эксперт удален", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_expert", "type": "main"})).get_json())
            users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "vote_expert":
        expert_id = users_actions[vk_user.id].get("expert_id", None)
        expert = User.get_by_vk_id(get_vk_from_txt(msg) if expert_id is None else expert_id)
        if expert is None:
            await message.answer("Пользователь не найден", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_expert", "type": "vote"})).get_json())
            return
        admins_as_experts[vk_user.id] = expert.vk_id
        await message.answer("Вы вошли в режим оценки от имени %s %s." % (expert.first_name, expert.last_name), keyboard=Keyboard(inline=True).add(Text("главное меню эксперта"))
                             .add(Callback("Назад", {"cmd": "admin_expert", "type": "main"})).get_json())
    elif users_actions[vk_user.id]["cmd"] == "rename_group":
        group_id = users_actions[vk_user.id]["group_id"]
        group = ContestGroup.get_by_id(group_id)
        group.name = msg
        group.save_to_db()

        await message.answer("Изменено", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "groups"})).get_json())
        users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "remove_group":
        group_id = users_actions[vk_user.id]["group_id"]
        group = ContestGroup.get_by_id(group_id)
        group.delete_from_db()

        await message.answer("Удалено", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "groups"})).get_json())
        users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "add_group":
        group = ContestGroup()
        group.id = len(ContestGroup.get_all_groups()) + 1
        group.name = msg
        group.save_to_db()

        await message.answer("Добавлено", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "groups"})).get_json())
        users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "rename_nomination":
        nomination_id = users_actions[vk_user.id]["nomination_id"]
        nomination = ContestNomination.get_by_id(nomination_id)
        nomination.name = msg
        nomination.save_to_db()

        await message.answer("Изменено", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "nominations"})).get_json())
        users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "remove_nomination":
        nomination_id = users_actions[vk_user.id]["nomination_id"]
        nomination = ContestNomination.get_by_id(nomination_id)
        nomination.delete_from_db()

        await message.answer("Удалено", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "nominations"})).get_json())
        users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "add_nomination":
        nomination = ContestNomination()
        nomination.id = len(ContestNomination.get_all_nominations()) + 1
        nomination.name = msg
        nomination.save_to_db()

        await message.answer("Добавлено", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "nominations"})).get_json())
        users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "get_user":
        user_id = get_vk_from_txt(msg)
        user = User.get_by_vk_id(user_id)
        if user is None:
            await message.answer("Пользователь не найден", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "users"})).get_json())
            return
        await message.answer("Информация о пользователе:\n\n"
                             "Имя: %s\n"
                             "Фамилия: %s\n"
                             "Домен: %s\n"
                             "Роль: %s\n"
                             "Забанен: %s\n"
                             "Причина бана: %s\n"
                             "Номинации эксперта: %s\n"
                             "Пользователь отправил %s заявок" % (
                                 user.first_name,
                                 user.last_name,
                                 user.domain,
                                 user.role,
                                 user.isBanned,
                                 user.ban_reason if user.ban_reason is not None else "Не забанен",
                                 ", ".join([ContestNomination.get_by_id(nomination_id).name for nomination_id in user.expert_nominations]) if user.role == 'expert' is not None else "Не эксперт",
                                 len(user.get_as_contest_member().get_user_contests())
                             ),
                             keyboard=Keyboard(inline=True).add(Callback("Открыть участия", {"cmd": "admin_users", "type": "user_plays", "user_id": user_id})).row()
                             .add(Callback("Забанить" if not user.isBanned else "Разбанить", {"cmd": "admin_users", "type": "ban_user", "user_id": user_id})).row()
                             .add(Callback("Изменить роль", {"cmd": "admin_users", "type": "change_role", "user_id": user_id})).add(Callback("Назад", {"cmd": "admin_users", "type": "users"})).get_json())
        users_actions[vk_user.id] = None
        return
    elif users_actions[vk_user.id]["cmd"] == "ban_user":
        user_id = users_actions[vk_user.id]["user_id"]
        user = User.get_by_vk_id(user_id)
        user.isBanned = not user.isBanned
        user.ban_reason = msg
        user.save_to_db()

        await message.answer("Изменено!", keyboard=Keyboard(inline=True).add(Text(str(user_id))).row().add(Callback("Назад", {"cmd": "admin_users", "type": "main"})).get_json())
        users_actions[vk_user.id] = {"cmd": "get_user"}
        return
    elif users_actions[vk_user.id]["cmd"] == "rate_expert":
        expert_id = users_actions[vk_user.id]["expert_id"]
        user_contest_id = users_actions[vk_user.id]["user_contest_id"]

        if expert_id is None or user_contest_id is None:
            await message.answer("Ошибка", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "main"})).get_json())
            return

        expert = User.get_by_vk_id(expert_id)
        user_contest = UserContest.get_by_id(user_contest_id)

        try:
            rates, feedback = msg.split("\n")
            rates = [int(x) for x in rates.split(" ")]
        except:
            await message.answer("Ошибка, попробуйте еще раз", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "main"})).get_json())
            return

        if len(rates) != len(ContestRateType.get_all_rate_types()):
            await message.answer("Неверное количество оценок. Попробуйте еще раз.", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "main"})).get_json())
            return

        values = {}
        for i in range(len(rates)):
            type = ContestRateType.get_by_id(i + 1)
            if rates[i] < type.min_value or rates[i] > type.max_value:
                await message.answer(f"Неверное значение оценки ({type.name}). Попробуйте еще раз.", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_users", "type": "main"})).get_json())
                return
            values[type] = rates[i]

        msg = "Вы собираетесь поставить оценку на участие №%s от имени эксперта @id%s:\n" % (user_contest.id, expert.vk_id)
        for type in values:
            msg += "\n%s: %s/%s" % (type.name, values[type], type.max_value)
        msg += "\n\n\nКомментарий: " + feedback

        await message.answer(msg, keyboard=Keyboard(inline=True).add(Callback("Подтвердить", {"cmd": "admin_users", "type": "rate_expert_confirm", "expert_id": expert_id, "user_contest_id": user_contest_id, "rates": {k.id: v for k,
        v in values.items()}, "feedback": feedback})).row().add(Callback("Назад", {"cmd": "admin_users", "type": "main"})).get_json())
    elif users_actions[vk_user.id]["cmd"] == "edit_param":
        param = users_actions[vk_user.id]["param"]

        await message.answer(f"Подтвердите изменение параметра на {msg}", keyboard=Keyboard(inline=True).add(Callback("Подтвердить", {"cmd": "admin_settings", "type": "edit_param_confirm", "param": param, "value": msg})).row().add(
            Callback("Назад", {"cmd": "admin_users", "type": "main"})).get_json())
    elif users_actions[vk_user.id]["cmd"] == "edit_rate_type":
        try:
            name, dats = msg.split('\n')
            min, max = dats.split(" ")
        except:
            await message.answer("Ошибка", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_settings", "type": "setup_rate_types"})).get_json())
            return

        await message.answer(f"Подтвердите изменение параметра на {name} {min} {max}", keyboard=Keyboard(inline=True).add(Callback("Подтвердить", {"cmd": "admin_settings", "type": "edit_rate_type_confirm", "name": name, "min": min,
                                                                                                                                                   "max": max, "rate_type_id": users_actions[vk_user.id]["rate_type_id"]})).row().add(
            Callback("Назад", {"cmd": "admin_settings", "type": "setup_rate_types"})).get_json())
    elif users_actions[vk_user.id]["cmd"] == "add_rate_type":
        try:
            name, dats = msg.split('\n')
            min, max = dats.split(" ")
        except:
            await message.answer("Ошибка", keyboard=Keyboard(inline=True).add(Callback("Назад", {"cmd": "admin_settings", "type": "setup_rate_types"})).get_json())
            return

        await message.answer(f"Подтвердите добавление параметра {name} {min} {max}",
                             keyboard=Keyboard(inline=True).add(Callback("Подтвердить", {"cmd": "admin_settings", "type": "add_rate_type_confirm", "name": name, "min": min, "max": max})).row().add(
                                 Callback("Назад", {"cmd": "admin_users", "type": "setup_rate_types"})).get_json())


# def can_edit()

@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "admin_texts"}))
async def admin_texts(event: MessageEvent):
    user = User.get_by_vk_id(event.user_id)
    if user is None or user.role not in ("admin", "moderator"):
        return

    cmd_type = event.payload.get("type", "select_nomination")

    if cmd_type == "select_nomination":
        main_keyboard = Keyboard(inline=True)

        nomination_group_len_matrix = {}
        for nomination in ContestNomination.get_all_nominations():
            main_keyboard.add(Callback(nomination.name, {"cmd": "admin_texts", "type": "select_group", "nomination_id": nomination.id})).row()
            nomination_group_len_matrix[nomination.id] = {}
            for group in ContestGroup.get_all_groups():
                nomination_group_len_matrix[nomination.id][group.id] = 0
        for text in ContestText.get_all_texts():
            nomination_group_len_matrix[text.nomination.id][text.group.id] += 1

        main_keyboard.add(Text("Главное меню"))

        await event.edit_message(
            "Настройка текстов\n\n"
            "%s\n\n"
            "Выберите номинацию:" % (
                "\n".join(["%s: %s" % (nomination.name, " / ".join([str(nomination_group_len_matrix[nomination.id][group.id]) for group in ContestGroup.get_all_groups()])) for nomination in
                           ContestNomination.get_all_nominations()])
            ),
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "select_group":
        main_keyboard = Keyboard(inline=True)

        nomination_id = event.payload.get("nomination_id", None)
        if nomination_id is None:
            return

        groups_len = {}
        for group in ContestGroup.get_all_groups():
            main_keyboard.add(Callback(group.name, {"cmd": "admin_texts", "type": "select_text", "nomination_id": nomination_id, "group_id": group.id})).row()
            groups_len[group.id] = 0

        for text in ContestText.get_all_texts(nomination_id=nomination_id):
            groups_len[text.group.id] += 1

        main_keyboard.add(Callback("Назад", {"cmd": "admin_texts", "type": "select_nomination"}))

        await event.edit_message(
            "Настройка текстов\n\n"
            "%s\n\n"
            "Выберите группу:" % (
                "\n".join(["%s: %s" % (group.name, groups_len[group.id]) for group in ContestGroup.get_all_groups()])
            ),
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "select_text":
        main_keyboard = Keyboard(inline=True)

        nomination_id = event.payload.get("nomination_id", None)
        group_id = event.payload.get("group_id", None)
        if nomination_id is None or group_id is None:
            return

        page = event.payload.get("page", 0)
        texts_on_page = 5
        texts = ContestText.get_all_texts(group_id, nomination_id)
        texts_len = len(texts)

        texts = texts[page * texts_on_page:page * texts_on_page + texts_on_page]
        pages = texts_len // texts_on_page + 1 if texts_len % texts_on_page != 0 else texts_len // texts_on_page
        if page > pages:
            page = pages
        if page < 0:
            page = 0

        for text in texts:
            main_keyboard.add(Callback(text.name, {"cmd": "admin_texts", "type": "edit_text", "text_id": text.id, "nomination_id": nomination_id, "group_id": group_id})).row()

        if page > 0:
            main_keyboard.add(Callback("<<", {"cmd": "admin_texts", "type": "select_text", "nomination_id": nomination_id, "group_id": group_id, "page": page - 1}))
        main_keyboard.add(Callback("Назад", {"cmd": "admin_texts", "type": "select_group", "nomination_id": nomination_id}))
        main_keyboard.add(Callback("Добавить", {"cmd": "admin_texts", "type": "edit_text", "nomination_id": nomination_id, "group_id": group_id, "text_id": -1}))
        if page < pages - 1:
            main_keyboard.add(Callback(">>", {"cmd": "admin_texts", "type": "select_text", "nomination_id": nomination_id, "group_id": group_id, "page": page + 1}))

        await event.edit_message(
            "Настройка текстов\n\n"
            "Выберите текст:",
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "edit_text":
        main_keyboard = Keyboard(inline=True)

        nomination_id = event.payload.get("nomination_id", None)
        group_id = event.payload.get("group_id", None)
        text_id = event.payload.get("text_id", None)
        if nomination_id is None or group_id is None or text_id is None:
            return

        if text_id == -1:
            text = ContestText()
            text.nomination = ContestNomination.get_by_id(nomination_id)
            text.group = ContestGroup.get_by_id(group_id)
            text.name = "New text"
            text.author = "Unknown"
            text.text = "Nothing"
            text.id = len(ContestText.get_all_texts()) + 1
            text.save_to_db()
        else:
            text = ContestText.get_by_id(text_id)

        main_keyboard.add(Callback("Название", {"cmd": "admin_texts", "type": "edit_text_param", "text_id": text.id, "param": "name"}))
        main_keyboard.add(Callback("Автор", {"cmd": "admin_texts", "type": "edit_text_param", "text_id": text.id, "param": "author"}))
        main_keyboard.add(Callback("Текст", {"cmd": "admin_texts", "type": "edit_text_param", "text_id": text.id, "param": "text"})).row()
        main_keyboard.add(Callback("Удалить", {"cmd": "admin_texts", "type": "delete_text", "text_id": text.id})).row()

        main_keyboard.add(Callback("Назад", {"cmd": "admin_texts", "type": "select_text", "nomination_id": nomination_id, "group_id": group_id}))

        await event.edit_message(
            "Настройка текстов\n\n"
            "Название: %s\n"
            "Автор: %s\n\n"
            "%s" % (
                text.name,
                text.author,
                text.text
            ),
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "edit_text_param":
        main_keyboard = Keyboard(inline=True)

        text_id = event.payload.get("text_id", None)
        param = event.payload.get("param", None)

        text = ContestText.get_by_id(text_id)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_texts", "type": "edit_text", "text_id": text_id, "nomination_id": text.nomination.id, "group_id": text.group.id}))

        await event.edit_message(
            "Настройка текстов\n\n"
            "Введите новое значение:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "edit_text_param", "text_id": text_id, "param": param}

    elif cmd_type == "delete_text":
        main_keyboard = Keyboard(inline=True)

        text_id = event.payload.get("text_id", None)
        text = ContestText.get_by_id(text_id)

        await event.edit_message(
            "Точно удалить?",
            keyboard=main_keyboard.add(Callback("Да", {"cmd": "admin_texts", "type": "delete_text_confirm", "text_id": text_id})).row()
            .add(Callback("Нет", {"cmd": "admin_texts", "type": "edit_text", "text_id": text_id, "nomination_id": text.nomination.id, "group_id": text.group.id})).get_json()
        )
    elif cmd_type == "delete_text_confirm":
        main_keyboard = Keyboard(inline=True)

        text_id = event.payload.get("text_id", None)
        text = ContestText.get_by_id(text_id)
        text.delete_from_db()

        await event.edit_message(
            "Удалено",
            keyboard=main_keyboard.add(Callback("Назад", {"cmd": "admin_texts", "type": "select_text", "nomination_id": text.nomination.id, "group_id": text.group.id})).get_json()
        )


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "admin_raiting"}))
async def admin_raiting(event: MessageEvent):
    user = User.get_by_vk_id(event.user_id)
    if user is None or user.role not in ("admin", "moderator"):
        return

    cmd_type = event.payload.get("type", "select_nomination")

    if cmd_type == "select_nomination":
        main_keyboard = Keyboard(inline=True)

        nominations = ContestNomination.get_all_nominations()
        for nomination in nominations:
            main_keyboard.add(Callback(nomination.name, {"cmd": "admin_raiting", "type": "show", "nomination_id": nomination.id})).row()

        main_keyboard.add(Text("Главное меню"))

        await event.edit_message(
            "Рейтинг\n\n"
            "Выберите номинацию:",
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "show":
        main_keyboard = Keyboard(inline=True)

        nomination_id = event.payload.get("nomination_id", None)
        if nomination_id is None:
            return

        answer_text = "Список победителей:\n\n"
        for group in ContestGroup.get_all_groups():
            answer_text += "Группа %s:\n" % group.name
            winners = UserContest.get_by_nomination_id_and_group_id(nomination_id, group.id)
            winners.sort(key=lambda x: x.get_avg_rate(), reverse=True)

            if len(winners) == 0:
                answer_text += " - Нет участников\n\n"
                continue

            if winners[0].get_avg_rate() >= 9.7:
                win: UserContest = winners[0]
                answer_text += " - Гранд-при: %s %s @id%s - %s балла, проголосовало %s/%s экспертов\n" % (win.contest_member.user.first_name, win.contest_member.user.last_name, win.contest_member.user.vk_id, win.get_avg_rate(),
                                                                                                          len(win.get_rates()),
                                                                                                          len(User.get_all_members_by_role("expert")))
                winners = winners[1:]

            for i in range(len(winners)):
                if i > 2:
                    break
                win: UserContest = winners[i]
                answer_text += " - %s место: %s %s @id%s - %s балла, проголосовало %s/%s экспертов\n" % (i + 1, win.contest_member.user.first_name, win.contest_member.user.last_name, win.contest_member.user.vk_id, win.get_avg_rate(),
                                                                                                         len(win.get_rates()),
                                                                                                         len(User.get_all_members_by_role("expert")))
            answer_text += "\n"

        main_keyboard.add(Callback("Назад", {"cmd": "admin_raiting", "type": "select_nomination"}))
        await event.edit_message(answer_text, keyboard=main_keyboard.get_json())


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "admin_expert"}))
async def admin_expert(event: MessageEvent):
    user = User.get_by_vk_id(event.user_id)
    if user is None or user.role not in ("admin", "moderator"):
        return

    cmd_type = event.payload.get("type", "main")

    if cmd_type == "main":
        if users_actions.get(event.user_id, None) is not None:
            del users_actions[event.user_id]
        if admins_as_experts.get(event.user_id, None) is not None:
            del admins_as_experts[event.user_id]

        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Добавить эксперта", {"cmd": "admin_expert", "type": "add"})).row()
        main_keyboard.add(Callback("Удалить эксперта", {"cmd": "admin_expert", "type": "delete"})).row()
        main_keyboard.add(Callback("Оценить задания", {"cmd": "admin_expert", "type": "vote"})).row()
        main_keyboard.add(Text("Главное меню"))

        msg = "Эксперты: \n\n"
        for expert in User.get_all_members_by_role("expert"):
            voting = UserContestRate.get_unrated_contests_by_expert_id(expert.id)
            voted = UserContestRate.get_rates_by_expert_id(expert.id)

            msg += "%s %s @id%s - оценено %s/%s работ\n" % (expert.first_name, expert.last_name, expert.vk_id, len(voted), len(voting) + len(voted))

        await event.edit_message(
            msg,
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "add":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_expert", "type": "main"}))

        await event.edit_message(
            "Введите линк пользователя:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "add_expert"}
    elif cmd_type == "delete":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_expert", "type": "main"}))

        await event.edit_message(
            "Введите линк пользователя:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "delete_expert"}
    elif cmd_type == "vote":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_expert", "type": "main"}))

        await event.edit_message(
            "Введите линк пользователя:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "vote_expert"}


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "admin_users"}))
async def admin_users(event: MessageEvent):
    user = User.get_by_vk_id(event.user_id)
    if user is None or user.role not in ("admin", "moderator"):
        return

    cmd_type = event.payload.get("type", "main")

    if cmd_type == "main":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Настройки пользователя", {"cmd": "admin_users", "type": "users"})).row()
        main_keyboard.add(Callback("Настройки групп", {"cmd": "admin_users", "type": "groups"})).row()
        main_keyboard.add(Callback("Настройки номинаций", {"cmd": "admin_users", "type": "nominations"})).row()
        main_keyboard.add(Text("Главное меню"))

        await event.edit_message(
            "Настроки пользователей",
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "users":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "main"}))

        await event.edit_message(
            "Введите линк пользователя:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "get_user"}
    elif cmd_type == "user_plays":
        users_actions[event.user_id] = {"cmd": "get_user"}

        user_id = event.payload.get("user_id", None)
        member = User.get_by_vk_id(user_id).get_as_contest_member()
        page = event.payload.get("page", 0)

        plays_keyboard = Keyboard(inline=True)
        user_contests = member.get_user_contests()[::-1]

        if len(user_contests) == 0:
            await event.edit_message(Constants.NO_PLAYS_MESSAGE, keyboard=Keyboard(inline=True).add(Text(str(user_id))).get_json())
            return

        use_pages = True

        for user_contest in user_contests[page * 4:page * 4 + 4]:
            nomination = ContestNomination.get_by_id(user_contest.nomination.id)
            group = ContestGroup.get_by_id(user_contest.group.id)
            plays_keyboard.add(Callback(f"{group.name}, {nomination.name}",
                                        payload=event.payload | {"cmd": "admin_users", "type": "user_play", "user_id": user_id, "user_contest_id": user_contest.id}),
                               color=KeyboardButtonColor.POSITIVE if user_contest.finished != -1 else KeyboardButtonColor.PRIMARY)
            plays_keyboard.row()

        if use_pages:
            if page > 0:
                plays_keyboard.add(Callback("Предыдущая страница", payload=event.payload | {"page": page - 1}),
                                   color=KeyboardButtonColor.SECONDARY)

            if page < len(user_contests) // 5:
                plays_keyboard.add(Callback("Следующая страница", payload=event.payload | {"page": page + 1}),
                                   color=KeyboardButtonColor.SECONDARY)

        plays_keyboard.add(Text(str(user_id)))
        await event.edit_message(Constants.PLAYS_LABEL, keyboard=plays_keyboard.get_json())
    elif cmd_type == "user_play":
        user_id = event.payload.get("user_id", None)
        user_contest_id = event.payload.get("user_contest_id", None)
        user_contest = UserContest.get_by_id(user_contest_id)

        if user_id is None or user_contest_id is None:
            return

        nomination = ContestNomination.get_by_id(user_contest.nomination.id)
        group = ContestGroup.get_by_id(user_contest.group.id)
        text = ContestText.get_by_id(user_contest.text.id)

        plays_keyboard = Keyboard(inline=True)
        plays_keyboard.add(Callback("Посмотреть работу", payload=event.payload | {"type": "send_work"}),
                           color=KeyboardButtonColor.POSITIVE).row()

        plays_keyboard.add(Callback("Обновить текст", payload=event.payload | {"type": "update_text"})).row()

        plays_keyboard.add(Callback("Просмотреть результаты", payload=event.payload | {"type": "get_results"}),
                           color=KeyboardButtonColor.SECONDARY)

        plays_keyboard.add(Callback("Назад", payload={"cmd": "admin_users", "type": "user_plays", "user_id": user_id}))

        # breakpoint()
        await event.edit_message(Constants.USER_CONTEST_INFO % (
            user_contest.id,
            nomination.name,
            group.name,
            datetime.fromtimestamp(user_contest.started).strftime("%d.%m.%Y %H:%M"),
            datetime.fromtimestamp(user_contest.finished).strftime("%d.%m.%Y %H:%M"),
            "Завершен" if user_contest.finished != -1 else "Проводится",
            user_contest.name,
            user_contest.school,
            user_contest.email,
            user_contest.phone_number,
            user_contest.teacher,
            text.author + ". " + text.name,
            datetime.fromtimestamp(user_contest.deadline).strftime("%d.%m.%Y %H:%M"),
            (("Заблокирован" if user_contest.is_banned else ("Проверяется модераторами" if user_contest.is_checking else ("Одобрено" if user_contest.is_approved else "Отклонено модераторами")))
             if user_contest.sended_work else ("Ожидает отправки" if user_contest.is_approved else "Отклонено модераторами") + "\n") + (
                "Причина отклонения: %s\n" % user_contest.declined_reason if not user_contest.is_approved else "") + ("Причина блокировки: %s" % user_contest.ban_reason if user_contest.is_banned else "")),
                                 keyboard=plays_keyboard.get_json())
    elif cmd_type == "send_work":
        user_id = event.payload.get("user_id", None)
        user_contest_id = event.payload.get("user_contest_id", None)
        user_contest = UserContest.get_by_id(user_contest_id)

        if user_id is None or user_contest_id is None:
            return

        plays_keyboard = Keyboard(inline=True)
        plays_keyboard.add(Callback("Назад", payload={"cmd": "admin_users", "type": "user_play", "user_id": user_id, "user_contest_id": user_contest_id}))

        await event.edit_message(user_contest.text.text, keyboard=plays_keyboard.get_json(), attachment=user_contest.sended_work)
    elif cmd_type == "update_text":
        user_id = event.payload.get("user_id", None)
        user_contest_id = event.payload.get("user_contest_id", None)
        user_contest = UserContest.get_by_id(user_contest_id)

        if user_id is None or user_contest_id is None:
            return

        plays_keyboard = Keyboard(inline=True)
        plays_keyboard.add(Callback("Подтвердить", payload=event.payload | {"type": "update_text_confirm"})).row()
        plays_keyboard.add(Callback("Назад", payload={"cmd": "admin_users", "type": "user_play", "user_id": user_id, "user_contest_id": user_contest_id}))

        await event.edit_message("Вы уверены?", keyboard=plays_keyboard.get_json())
    elif cmd_type == "update_text_confirm":
        user_id = event.payload.get("user_id", None)
        user_contest_id = event.payload.get("user_contest_id", None)
        user_contest = UserContest.get_by_id(user_contest_id)

        if user_id is None or user_contest_id is None:
            return

        user_contest.text = ContestText.get_random_text(user_contest.nomination.id, user_contest.group.id)
        user_contest.deadline = int(time.time()) + Contest.get_by_id(-1).time_for_send * 60
        user_contest.can_send_work = True
        user_contest.is_checking = False
        user_contest.save_to_db()

        plays_keyboard = Keyboard(inline=True)
        plays_keyboard.add(Callback("Назад", payload={"cmd": "admin_users", "type": "user_play", "user_id": user_id, "user_contest_id": user_contest_id}))

        await event.edit_message("Текст обновлен", keyboard=plays_keyboard.get_json())
        await bot.api.messages.send(user_id=user_id, message=f"Ваш текст в участии №{user_contest.id} был обновлен. Вы можете просмотреть его в информации об участии.")
    elif cmd_type == "get_results":
        user_id = event.payload.get("user_id", None)
        user_contest_id = event.payload.get("user_contest_id", None)
        user_contest = UserContest.get_by_id(user_contest_id)
        page = event.payload.get("page", 0)

        if user_id is None or user_contest_id is None:
            return

        plays_keyboard = Keyboard(inline=True)
        all_experts = [u for u in User.get_all_members_by_role('expert') if u.expert_nominations == [] or user_contest.nomination in u.expert_nominations]
        for expert in all_experts[page * 4:page * 4 + 4]:
            rated = expert.id in [rate.expert.id for rate in user_contest.get_rates()]
            plays_keyboard.add(Callback(f"{expert.first_name} {expert.last_name} @id{expert.vk_id}",
                                        payload=event.payload | {"type": "rate_expert" if not rated else "show_rate", "user_id": user_id, "user_contest_id": user_contest_id, "expert_id": expert.vk_id}),
                               color=KeyboardButtonColor.POSITIVE if rated else KeyboardButtonColor.NEGATIVE).row()

        if page > 0:
            plays_keyboard.add(Callback("Предыдущая страница", payload=event.payload | {"page": page - 1}),
                               color=KeyboardButtonColor.SECONDARY)
        plays_keyboard.add(Callback("Назад", payload={"cmd": "admin_users", "type": "user_play", "user_id": user_id, "user_contest_id": user_contest_id}))
        if page < len(all_experts) // 4:
            plays_keyboard.add(Callback("Следующая страница", payload=event.payload | {"page": page + 1}),
                               color=KeyboardButtonColor.SECONDARY)

        await event.edit_message("Результаты:\n\n" + "\n".join(
            [f"@id{rate.expert.vk_id}: {'/'.join([str(val.rate_value) for val in rate.get_rate_values()])} - {sum([val.rate_value for val in rate.get_rate_values()]) / len([str(val.rate_value) for val in rate.get_rate_values()])}" for rate
             in user_contest.get_rates()]) +
                                 f"\n\nОценило {len(user_contest.get_rates())}/{len(all_experts)} экспертов\nСредняя "
                                 f"оценка: {user_contest.get_avg_rate()}\n\nНиже (кнопками) представлены эксперты.",
                                 keyboard=plays_keyboard.get_json())
    elif cmd_type == "rate_expert":
        user_id = event.payload.get("user_id", None)
        user_contest_id = event.payload.get("user_contest_id", None)
        expert_id = event.payload.get("expert_id", None)
        user_contest = UserContest.get_by_id(user_contest_id)

        if user_id is None or user_contest_id is None or expert_id is None:
            return

        msg = f"Вы вошли в режим быстрой оценки от эксперта @id{expert_id}.\nОтправьте оценки по категориям через пробел (например, 5 4 7 4 1):\n"
        for rate_type in ContestRateType.get_all_rate_types():
            msg += f"{rate_type.name} ({rate_type.min_value}-{rate_type.max_value})\n"
        msg += "\nНа следующей строчке укажите комментарий эксперта."

        plays_keyboard = Keyboard(inline=True)
        plays_keyboard.add(Callback("Назад", payload={"cmd": "admin_users", "type": "get_results", "user_id": user_id, "user_contest_id": user_contest_id}))

        await event.edit_message(msg, keyboard=plays_keyboard.get_json())
        users_actions[event.user_id] = {"cmd": "rate_expert", "expert_id": expert_id, "user_contest_id": user_contest_id}
    elif cmd_type == "rate_expert_confirm":
        user_id = event.payload.get("user_id", None)
        user_contest_id = event.payload.get("user_contest_id", None)
        expert_id = event.payload.get("expert_id", None)
        rates = event.payload.get("rates", None)
        feedback = event.payload.get("feedback", None)
        user_contest = UserContest.get_by_id(user_contest_id)

        expert = User.get_by_vk_id(expert_id)
        rate = UserContestRate()
        rate.user_contest = user_contest
        rate.expert = expert
        rate.feedback = feedback
        rate.id = len(UserContestRate.get_all_rates()) + 1

        for type in rates.keys():
            rate_value = UserContestRateValue()
            rate_value.contest_rate_type = ContestRateType.get_by_id(int(type))
            rate_value.rate_value = int(rates[str(type)])
            rate_value.user_contest_rate = rate
            rate_value.save_to_db()

        rate.save_to_db()

        plays_keyboard = Keyboard(inline=True)
        plays_keyboard.add(Callback("Назад", payload={"cmd": "admin_users", "type": "get_results", "user_id": user_id, "user_contest_id": user_contest_id}))

        await event.edit_message("Оценка отправлена", keyboard=plays_keyboard.get_json())

    elif cmd_type == "show_rate":
        user_id = event.payload.get("user_id", None)
        user_contest_id = event.payload.get("user_contest_id", None)
        expert_id = event.payload.get("expert_id", None)
        user_contest = UserContest.get_by_id(user_contest_id)

        if user_id is None or user_contest_id is None or expert_id is None:
            return

        expert = User.get_by_vk_id(expert_id)
        rate = None

        for rate in user_contest.get_rates():
            if rate.expert.id == expert_id:
                break

        if rate is None:
            return

        msg = f"Оценка эксперта @id{expert.vk_id}:\n\n"
        for val in rate.get_rate_values():
            msg += f"{val.contest_rate_type.name}: {val.rate_value}/{val.contest_rate_type.max_value}\n"

        msg += f"\nКомментарий эксперта:\n{rate.feedback}"

        plays_keyboard = Keyboard(inline=True)
        plays_keyboard.add(Callback("Назад", payload={"cmd": "admin_users", "type": "get_results", "user_id": user_id, "user_contest_id": user_contest_id}))

        await event.edit_message(msg, keyboard=plays_keyboard.get_json())
    elif cmd_type == "ban_user":
        main_keyboard = Keyboard(inline=True)

        user_id = event.payload.get("user_id", None)
        if user_id is None:
            return

        user = User.get_by_vk_id(user_id)
        if user is None:
            return

        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "users"}))

        await event.edit_message(
            "Введите причину бана (или введите любой текст для разбана):",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "ban_user", "user_id": user_id}
    elif cmd_type == "change_role":
        main_keyboard = Keyboard(inline=True)

        user_id = event.payload.get("user_id", None)
        if user_id is None:
            return

        user = User.get_by_vk_id(user_id)
        if user is None:
            return

        main_keyboard.add(Callback("Пользователь", {"cmd": "admin_users", "type": "change_role_confirm", "user_id": user_id, "role": "member"})).row()
        main_keyboard.add(Callback("Эксперт", {"cmd": "admin_users", "type": "change_role_confirm", "user_id": user_id, "role": "expert"})).row()
        main_keyboard.add(Callback("Модератор", {"cmd": "admin_users", "type": "change_role_confirm", "user_id": user_id, "role": "moderator"})).row()

        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "users"}))

        await event.edit_message(
            "Выберите роль:",
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "change_role_confirm":
        user_id = event.payload.get("user_id", None)
        role = event.payload.get("role", None)
        if user_id is None or role is None:
            return

        user = User.get_by_vk_id(user_id)
        if user is None:
            return

        user.role = role
        user.save_to_db()

        await event.edit_message(
            "Роль изменена",
            keyboard=Keyboard(inline=True).add(Text(str(user_id))).row().add(Callback("Назад", {"cmd": "admin_users", "type": "main"})).get_json()
        )
        users_actions[event.user_id] = {"cmd": "get_user"}
    elif cmd_type == "groups":
        main_keyboard = Keyboard(inline=True)

        for group in ContestGroup.get_all_groups():
            main_keyboard.add(Callback(group.name, {"cmd": "admin_users", "type": "rename_group", "group_id": group.id}))
            main_keyboard.add(Callback("❌", {"cmd": "admin_users", "type": "remove_group", "group_id": group.id}), color=KeyboardButtonColor.SECONDARY).row()

        main_keyboard.add(Callback("Добавить группу", {"cmd": "admin_users", "type": "add_group"}))
        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "main"}))

        await event.edit_message(
            "Настройка групп\n\nНажмите на группу, чтобы переименовать её, или на ❌, чтобы удалить её.",
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "rename_group":
        main_keyboard = Keyboard(inline=True)

        group_id = event.payload.get("group_id", None)
        if group_id is None:
            return

        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "groups"}))

        await event.edit_message(
            "Введите новое название группы:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "rename_group", "group_id": group_id}
    elif cmd_type == "remove_group":
        main_keyboard = Keyboard(inline=True)

        group_id = event.payload.get("group_id", None)
        if group_id is None:
            return

        group = ContestGroup.get_by_id(group_id)

        main_keyboard.add(Text("Да, я уверен")).row()
        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "groups"}))

        await event.edit_message(
            "Вы уверены, что хотите удалить группу %s? Все связанные тексты будут удалены!" % group.name,
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "remove_group", "group_id": group_id}
    elif cmd_type == "add_group":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "groups"}))

        await event.edit_message(
            "Введите название новой группы:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "add_group"}
    elif cmd_type == "nominations":
        main_keyboard = Keyboard(inline=True)

        for nomination in ContestNomination.get_all_nominations():
            main_keyboard.add(Callback(nomination.name, {"cmd": "admin_users", "type": "rename_nomination", "nomination_id": nomination.id}))
            main_keyboard.add(Callback("❌", {"cmd": "admin_users", "type": "remove_nomination", "nomination_id": nomination.id}), color=KeyboardButtonColor.SECONDARY).row()

        main_keyboard.add(Callback("Добавить номинацию", {"cmd": "admin_users", "type": "add_nomination"}))
        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "main"}))

        await event.edit_message(
            "Настройка номинаций\n\nНажмите на номинацию, чтобы переименовать её, или на ❌, чтобы удалить её.",
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "rename_nomination":
        main_keyboard = Keyboard(inline=True)

        nomination_id = event.payload.get("nomination_id", None)
        if nomination_id is None:
            return

        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "nominations"}))

        await event.edit_message(
            "Введите новое название номинации:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "rename_nomination", "nomination_id": nomination_id}
    elif cmd_type == "remove_nomination":
        main_keyboard = Keyboard(inline=True)

        nomination_id = event.payload.get("nomination_id", None)
        if nomination_id is None:
            return

        nomination = ContestNomination.get_by_id(nomination_id)

        main_keyboard.add(Text("Да, я уверен")).row()
        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "nominations"}))

        await event.edit_message(
            "Вы уверены, что хотите удалить номинацию %s? Все связанные тексты будут удалены!" % nomination.name,
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "remove_nomination", "nomination_id": nomination_id}
    elif cmd_type == "add_nomination":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_users", "type": "nominations"}))

        await event.edit_message(
            "Введите название новой номинации:",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "add_nomination"}


def can_edit(vk_id):
    user = User.get_by_vk_id(vk_id)
    return user.role == "admin" and Contest.get_by_id(-1).start_date > time.time()


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "admin_settings"}))
async def admin_settings(event: MessageEvent):
    user = User.get_by_vk_id(event.user_id)
    if user.role == "admin" or user.role == "moderator":
        return

    cmd_type = event.payload.get("type", "main")

    if cmd_type == "main":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Дата начала", {"cmd": "admin_settings", "type": "edit_param", "param": "start_date"}))
        main_keyboard.add(Callback("Дата окончания", {"cmd": "admin_settings", "type": "edit_param", "param": "end_date"})).row()
        main_keyboard.add(Callback("Дата подведения итогов", {"cmd": "admin_settings", "type": "edit_param", "param": "rates_date"}))
        main_keyboard.add(Callback("Дата оглашения победителей", {"cmd": "admin_settings", "type": "edit_param", "param": "winners_date"})).row()
        main_keyboard.add(Callback("Время на отправку", {"cmd": "admin_settings", "type": "edit_param", "param": "time_for_send"}))
        main_keyboard.add(Callback("Цена участия", {"cmd": "admin_settings", "type": "edit_param", "param": "price"})).row()
        main_keyboard.add(Callback("Настройка критерий", {"cmd": "admin_settings", "type": "setup_rate_types"})).row()

        main_keyboard.add(Text("Главное меню"))

        await event.edit_message(
            "Настройки",
            keyboard=main_keyboard.get_json()
        )

    elif cmd_type == "edit_param" and can_edit(event.user_id):

        main_keyboard = Keyboard(inline=True)

        param = event.payload.get("param", None)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_settings", "type": "main"}))

        await event.edit_message(
            "Введите новое значение(дату необходимо вводить в формате %d.%m.%Y %H:%M)",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "edit_param", "param": param}
    elif cmd_type == "edit_param_confirm":
        param = event.payload.get("param", None)
        value = event.payload.get("value", None)
        contest = Contest.get_by_id(-1)

        try:
            if param == "start_date":
                contest.start_date = text_to_date(value)
            elif param == "finish_date":
                contest.finish_date = text_to_date(value)
            elif param == "rates_date":
                contest.rates_date = text_to_date(value)
            elif param == "winners_date":
                contest.winners_date = text_to_date(value)
            elif param == "time_for_send":
                contest.time_for_send = int(value)
            elif param == "price":
                contest.price = int(value)
            else:
                await event.edit_message("Ошибка")
                return
        except Exception as e:
            await event.edit_message("Ошибка " + str(e))
            return
        contest.save_to_db()

        await event.edit_message(
            "Успешно",
            keyboard=Keyboard(inline=True).add(Text("Главное меню")).get_json()
        )
    else:
        ...
        #TODO("cannot aedit message")
    if cmd_type == "setup_rate_types":
        main_keyboard = Keyboard(inline=True)

        for rate_type in ContestRateType.get_all_rate_types():
            main_keyboard.add(Callback(f"{rate_type.name} ({rate_type.min_value} - {rate_type.max_value})", {"cmd": "admin_settings", "type": "edit_rate_type", "rate_type_id": rate_type.id}))
            main_keyboard.add(Callback("❌", {"cmd": "admin_settings", "type": "remove_rate_type", "rate_type_id": rate_type.id}), color=KeyboardButtonColor.SECONDARY).row()
        main_keyboard.add(Callback("Добавить критерий", {"cmd": "admin_settings", "type": "add_rate_type"}))
        main_keyboard.add(Text("Главное меню"))

        await event.edit_message(
            "Настройка критерий",
            keyboard=main_keyboard.get_json()
        )
    elif cmd_type == "edit_rate_type":
        main_keyboard = Keyboard(inline=True)

        rate_type_id = event.payload.get("rate_type_id", None)
        if rate_type_id is None:
            return

        main_keyboard.add(Callback("Назад", {"cmd": "admin_settings", "type": "setup_rate_types"}))

        await event.edit_message(
            "Введите новое название критерия, на следующей строчке, через пробел, введите максимальную и минимальную оценку.",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "edit_rate_type", "rate_type_id": rate_type_id}
    elif cmd_type == "edit_rate_type_confirm":
        rate_type_id = event.payload.get("rate_type_id", None)
        if rate_type_id is None:
            return

        rate_type = ContestRateType.get_by_id(rate_type_id)
        rate_type.name = event.payload.get("name", None)
        rate_type.min_value = event.payload.get("min", None)
        rate_type.max_value = event.payload.get("max", None)
        rate_type.save_to_db()

        await event.edit_message(
            "Успешно",
            keyboard=Keyboard(inline=True).add(Callback("Главное меню", {"cmd": "admin_settings", "type": "setup_rate_types"})).get_json()
        )
    elif cmd_type == "remove_rate_type":
        main_keyboard = Keyboard(inline=True)

        rate_type_id = event.payload.get("rate_type_id", None)
        if rate_type_id is None:
            return

        rate_type = ContestRateType.get_by_id(rate_type_id)

        main_keyboard.add(Callback("Да, я уверен", {"cmd": "admin_settings", "type": "remove_rate_type_confirm", "rate_type_id": rate_type_id})).row()
        main_keyboard.add(Callback("Назад", {"cmd": "admin_settings", "type": "setup_rate_types"}))

        await event.edit_message(
            "Вы уверены, что хотите удалить критерий %s?" % rate_type.name,
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "remove_rate_type", "rate_type_id": rate_type_id}
    elif cmd_type == "remove_rate_type_confirm":
        rate_type_id = event.payload.get("rate_type_id", None)
        if rate_type_id is None:
            return

        rate_type = ContestRateType.get_by_id(rate_type_id)
        rate_type.delete_from_db()

        await event.edit_message(
            "Успешно",
            keyboard=Keyboard(inline=True).add(Callback("Главное меню", {"cmd": "admin_settings", "type": "setup_rate_types"})).get_json()
        )
    elif cmd_type == "add_rate_type":
        main_keyboard = Keyboard(inline=True)

        main_keyboard.add(Callback("Назад", {"cmd": "admin_settings", "type": "setup_rate_types"}))

        await event.edit_message(
            "Введите название критерия, на следующей строчке, через пробел, введите максимальную и минимальную оценку.",
            keyboard=main_keyboard.get_json()
        )
        users_actions[event.user_id] = {"cmd": "add_rate_type"}
    elif cmd_type == "add_rate_type_confirm":
        name = event.payload.get("name", None)
        min_value = event.payload.get("min", None)
        max_value = event.payload.get("max", None)

        rate_type = ContestRateType()
        rate_type.name = name
        rate_type.min_value = min_value
        rate_type.max_value = max_value
        rate_type.save_to_db()

        await event.edit_message(
            "Успешно",
            keyboard=Keyboard(inline=True).add(Callback("Главное меню", {"cmd": "admin_settings", "type": "setup_rate_types"})).get_json()
        )
