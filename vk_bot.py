import datetime
import time

from vkbottle import Keyboard, Callback, Text, KeyboardButtonColor, OpenLink
from vkbottle.bot import Bot, Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadContainsRule, AttachmentTypeRule
from vkbottle_types.events import GroupEventType

import config
import task_executer
from config import Constants
from reread_types import *

bot = Bot(config.VK.TOKEN)
userbot = Bot(config.VK.USER_TOKEN)
users_actions = {}
runTasks = False


async def post_user_contest(user_contest: UserContest):
    await userbot.api.wall.post(owner_id="-" + config.VK.GROUP_ID, from_group=True, message=config.Constants.POST_TEXT % (user_contest.id, user_contest.group.name, user_contest.nomination.name, user_contest.text.author,
                                                                                                                          user_contest.text.name,
                                                                                                                          f"https://vk.com/write-{config.VK.GROUP_ID}?ref={user_contest.id}&ref_source=user_vote"),
                                attachments=user_contest.sended_work)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "join_contest"}))
async def join_contest(event: MessageEvent):
    state = event.payload.get("state", "start")
    user_id = event.user_id

    if state == "start":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)

        await event.edit_message("Заполните анкету участника, отправив сообщение в следующем формате:\n\n Фамилия Имя участника\nМесто обучения\nПочта для связи\nНаставник (преподаватель) кому вручать грамоту.\nКонтактный "
                                 "телефон.\n\n\nФормат сообщения:\nИванов Иван \nМБОУ СОШ №41\nnkodinov@mail.ru\nПетров Петр Петрович\n+7 800 555 35 35\n\nЕсли вы не хотите указывать какую-либо информацию, поставьте дефис, "
                                 "или прочерк на ее месте.", keyboard=Keyboard(inline=True).row().add(
            Text(Constants.MAIN_MENU_TEXT), color=KeyboardButtonColor.NEGATIVE).get_json())

        users_actions[event.user_id] = {"state": "fill_member_info"}
    elif state == "select_group":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)

        groups_keyboard = Keyboard(inline=True)
        for group in ContestGroup.get_all_groups():
            groups_keyboard.add(
                Callback(group.name, payload=event.payload | {"state": "select_nomination", "group": group.id}))
            groups_keyboard.row()
        groups_keyboard.add(Text(Constants.MAIN_MENU_TEXT), color=KeyboardButtonColor.NEGATIVE)
        await event.edit_message(Constants.MEMBER_SELECT_GROUP_MESSAGE, keyboard=groups_keyboard.get_json())
    elif state == "select_nomination":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)

        nomination_keyboard = Keyboard(inline=True)
        for nomination in ContestNomination.get_all_nominations():
            nomination_keyboard.add(Callback(nomination.name, payload=event.payload | {"state": "verify_selection",
                                                                                       "nomination": nomination.id}))
            nomination_keyboard.row()
        nomination_keyboard.add(Callback(Constants.PREV_TEXT, event.payload | {"state": "select_group"}),
                                color=KeyboardButtonColor.NEGATIVE)
        await event.edit_message(Constants.MEMBER_SELECT_NOMINATION_MESSAGE, keyboard=nomination_keyboard.get_json())
    elif state == "verify_selection":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)

        await event.edit_message(Constants.MEMBER_VERIFY_SELECTION_TEXT % (
            ContestNomination.get_by_id(event.payload.get("nomination", -1)).name,
            ContestGroup.get_by_id(event.payload.get("group", -1)).name, Contest.get_by_id(-1).time_for_send,
            Contest.get_by_id(-1).price, event.payload.get("member_name"), event.payload.get("member_school"), event.payload.get("member_email"), event.payload.get("member_phone"), event.payload.get("member_teacher"),),
                                 keyboard=Keyboard(inline=True)
                                 .add(Callback(Constants.VERIFY_TEXT, event.payload | {"state": "pay" if Contest.get_by_id(-1).price != 0 else "verify_pay"}),
                                      color=KeyboardButtonColor.POSITIVE).row()
                                 .add(Text(Constants.CANCEL_TEXT), color=KeyboardButtonColor.NEGATIVE).get_json())
    elif state == "pay":
        await event.edit_message(Constants.NEED_PAY_MESSAGE, keyboard=Keyboard(inline=True).add(
            OpenLink("https://example.com", f"Оплатить ({Contest.get_by_id(-1).price})"))
                                 .row().add(Callback(Constants.VERIFY_TEXT, event.payload | {"state": "verify_pay"}),
                                            color=KeyboardButtonColor.POSITIVE).get_json())  # TODO: Add payment
    elif state == "verify_pay":
        if len([222]) == 1 or Contest.get_by_id(-1).price == 0:
            await event.show_snackbar(Constants.PAY_FOUND_MESSAGE)
            new = UserContest()
            new.group = ContestGroup.get_by_id(event.payload.get("group"))
            new.nomination = ContestNomination.get_by_id(event.payload.get("nomination"))

            new.name = event.payload.get("member_name")
            new.school = event.payload.get("member_school")
            new.email = event.payload.get("member_email")
            new.teacher = event.payload.get("member_teacher")
            new.phone_number = event.payload.get("member_phone")

            new.can_send_work = True
            new.is_banned = False
            new.is_checking = False
            new.is_approved = True
            new.text = ContestText.get_random_text(new.group.id, new.nomination.id)
            new.contest_member = User.get_by_vk_id(event.user_id).get_as_contest_member()
            new.contest = Contest.get_by_id(-1)
            new.sended_work = None
            new.started = time.time()
            new.deadline = time.time() + Contest.get_by_id(-1).time_for_send * 60
            new.finished = -1
            new.save_to_db()

            await event.edit_message(Constants.PAYED_SUCCESS, keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PLAYS_TEXT, payload={"cmd": "my_plays"})).get_json())

            for admin in User.get_all_members_by_role("admin"):
                await bot.api.messages.send(user_id=admin.vk_id, message=f"Новое участие в конкурсе #{new.id}.\n\nНоминация: {new.nomination.name}\nГруппа: {new.group.name}\n\nИнформация о номинанте:\nФ.И.О.: {new.name}\nШкола: "
                                                                         f"{new.school}\nEmail: {new.email}\nТелефон: {new.phone_number}\nУчитель: {new.teacher}\n\nОтправитель: @id{event.user_id} ("
                                                                         f"{User.get_by_vk_id(event.user_id).first_name} {User.get_by_vk_id(event.user_id).last_name})\nПолученный текст: {new.text.author}. {new.text.name}", random_id=0)

        else:
            await event.show_snackbar(Constants.PAY_NOT_FOUND_MESSAGE)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "my_plays"}))
async def my_plays(event: MessageEvent):
    state = event.payload.get("state", "list_plays")
    user = User.get_by_vk_id(event.user_id)
    member = user.get_as_contest_member()

    print(event.payload)

    if state == "list_plays":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)
        page = event.payload.get("page", 0)

        plays_keyboard = Keyboard(inline=True)
        user_contests = member.get_user_contests()[::-1]

        if len(user_contests) == 0:
            await event.edit_message(Constants.NO_PLAYS_MESSAGE, keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.LETS_PLAY_TEXT,
                         payload={"cmd": "join_contest", "state": "select_group"})).get_json())
            return

        use_pages = True

        for user_contest in user_contests[page * 4:page * 4 + 4]:
            nomination = ContestNomination.get_by_id(user_contest.nomination.id)
            group = ContestGroup.get_by_id(user_contest.group.id)
            plays_keyboard.add(Callback(f"{group.name}, {nomination.name}",
                                        payload=event.payload | {"state": "show_play",
                                                                 "user_contest": user_contest.id}),
                               color=KeyboardButtonColor.POSITIVE if user_contest.finished != -1 else KeyboardButtonColor.PRIMARY)
            plays_keyboard.row()

        if use_pages:
            if page > 0:
                plays_keyboard.add(Callback("Предыдущая страница", payload=event.payload | {"page": page - 1}),
                                   color=KeyboardButtonColor.SECONDARY)

            if page < len(user_contests) // 5:
                plays_keyboard.add(Callback("Следующая страница", payload=event.payload | {"page": page + 1}),
                                   color=KeyboardButtonColor.SECONDARY)

            plays_keyboard.add(Text(Constants.MAIN_MENU_TEXT), color=KeyboardButtonColor.NEGATIVE)

        else:
            plays_keyboard.add(Text(Constants.MAIN_MENU_TEXT), color=KeyboardButtonColor.NEGATIVE)

        await event.edit_message(Constants.PLAYS_LABEL, keyboard=plays_keyboard.get_json())
    elif state == "show_play":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)
        user_contest = UserContest.get_by_id(int(event.payload.get("user_contest")))
        if user_contest is None:
            await event.edit_message(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                     keyboard=Constants.SUPPORT_KEYBOARD)
            return

        nomination = ContestNomination.get_by_id(user_contest.nomination.id)
        group = ContestGroup.get_by_id(user_contest.group.id)
        text = ContestText.get_by_id(user_contest.text.id)

        plays_keyboard = Keyboard(inline=True)
        if user_contest.sended_work is None:
            plays_keyboard.add(Callback("Отправить работу", payload=event.payload | {"state": "send_work"}),
                               color=KeyboardButtonColor.POSITIVE).row()

        plays_keyboard.add(Callback("Получить текст", payload=event.payload | {"state": "get_text"})).row()
        plays_keyboard.add(
            Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "list_plays"}))

        if user_contest.contest.winners_date < time.time():
            plays_keyboard.add(Callback("Просмотреть результаты", payload=event.payload | {"state": "get_results"}),
                               color=KeyboardButtonColor.SECONDARY)

        # breakpoint()
        await event.edit_message(Constants.USER_CONTEST_INFO % (
            user_contest.id,
            nomination.name,
            group.name,
            datetime.datetime.fromtimestamp(user_contest.started).strftime("%d.%m.%Y %H:%M"),
            datetime.datetime.fromtimestamp(user_contest.finished).strftime("%d.%m.%Y %H:%M"),
            "Завершен" if user_contest.finished != -1 else "Проводится",
            user_contest.name,
            user_contest.school,
            user_contest.email,
            user_contest.phone_number,
            user_contest.teacher,
            text.author + ". " + text.name,
            datetime.datetime.fromtimestamp(user_contest.deadline).strftime("%d.%m.%Y %H:%M"),
            (("Заблокирован" if user_contest.is_banned else ("Проверяется модераторами" if user_contest.is_checking else ("Одобрено" if user_contest.is_approved else "Отклонено модераторами")))
             if user_contest.sended_work else ("Ожидает отправки" if user_contest.is_approved else "Отклонено модераторами") + "\n") + (
                "Причина отклонения: %s\n" % user_contest.declined_reason if not user_contest.is_approved else "") + ("Причина блокировки: %s" % user_contest.ban_reason if user_contest.is_banned else "")),
                                 keyboard=plays_keyboard.get_json(), attachment=user_contest.sended_work)

    elif state == "get_text":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)
        user_contest = UserContest.get_by_id(int(event.payload.get("user_contest")))
        if user_contest is None:
            await event.edit_message(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                     keyboard=Constants.SUPPORT_KEYBOARD)
            return

        await event.edit_message(user_contest.text.author + ". " + user_contest.text.name + "\n\n" + user_contest.text.text, keyboard=Keyboard(inline=True).row().add(
            Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())

    elif state == "send_work":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)
        user_contest = UserContest.get_by_id(int(event.payload.get("user_contest")))
        if user_contest is None:
            await event.edit_message(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                     keyboard=Constants.SUPPORT_KEYBOARD)
            return

        if user_contest.sended_work is not None:
            await event.edit_message("Вы уже отправили работу.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())
            return

        if not user_contest.can_send_work:
            await event.edit_message("Вы не можете отправить работу.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")).get_json())
            return

        if user_contest.finished != -1:
            await event.edit_message("Конкурс завершен.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())
            return

        if time.time() > user_contest.deadline:
            await event.edit_message("Время на отправку работы истекло.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")).get_json())
            return

        users_actions[event.user_id] = {"state": "send_work", "user_contest": user_contest.id}
        await event.edit_message("Пришлите ваш ответ в формате видео или файла", keyboard=Keyboard(inline=True).row().add(
            Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())

    elif state == "get_results":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)
        user_contest = UserContest.get_by_id(int(event.payload.get("user_contest")))
        if user_contest is None:
            await event.edit_message(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                     keyboard=Constants.SUPPORT_KEYBOARD)
            return

        rates = user_contest.get_rates()
        if len(rates) == 0:
            await event.edit_message("Работа еще не оценивалась.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())
            return

        for rate in rates:
            await bot.api.messages.send(user_id=event.user_id, message=f"Эксперт #%s оценил вашу работу в конкурсе #{user_contest.id}.\n%s\n\nКомментарий эксперта:\n%s" %
                                                                       (rate.expert.id, "\n".join([f"{x.contest_rate_type.name}: {x.rate_value}" for x in rate.get_rate_values()]), rate.feedback),
                                        random_id=0)
        await event.edit_message("Результаты выше.", keyboard=Keyboard(inline=True).row().add(
            Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "moderator"}))
async def moderator(event: MessageEvent):
    state = event.payload.get("state", "approve")
    if state in ["approve", "decline"]:
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)
        user_contest = UserContest.get_by_id(int(event.payload.get("user_contest")))
        if not user_contest.is_checking:
            await event.edit_message("Работа уже проверена.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())
            return
        if user_contest is None:
            await event.edit_message(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                     keyboard=Constants.SUPPORT_KEYBOARD)
            return

        if state == "approve":
            user_contest.is_approved = True
            user_contest.is_checking = False
            user_contest.save_to_db()

            await bot.api.messages.send(user_id=user_contest.contest_member.user.vk_id, message=f"Ваш отклик в конкурсе #{user_contest.id} принят модератором. Выступление будет опубликовано в группе и передано экспертам для дальнейшей "
                                                                                                f"оценки.", random_id=0,
                                        keyboard=Keyboard(inline=True).row().add(
                                            Callback("Открыть участие", payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")))

            await event.edit_message("Работа одобрена!", keyboard=Keyboard(inline=True).row().add(
                Text("Продолжить"), color=KeyboardButtonColor.SECONDARY).get_json())

            for admin in User.get_all_members_by_role("admin"):
                await bot.api.messages.send(user_id=admin.vk_id,
                                            message=f"Модератор одобрил работу #{user_contest.id}.\n\nНоминация: {user_contest.nomination.name}\nГруппа: {user_contest.group.name}\n\nИнформация о номинанте:\nФ.И.О.:"
                                                    f" {user_contest.name}\nШкола: "
                                                    f"{user_contest.school}\nEmail: {user_contest.email}\nТелефон: {user_contest.phone_number}\nУчитель: {user_contest.teacher}\n\nОтправитель: @id"
                                                    f"{User.get_by_vk_id(user_contest.contest_member.user.vk_id).vk_id} ("
                                                    f"{User.get_by_vk_id(user_contest.contest_member.user.vk_id).first_name} {User.get_by_vk_id(user_contest.contest_member.user.vk_id).last_name})\nПолученный текст: {user_contest.text.author}. "
                                                    f"{user_contest.text.name}", attachment=user_contest.sended_work, random_id=0)

            await post_user_contest(user_contest)

            experts = User.get_all_members_by_role("expert")
            for expert in experts:
                if user_contest.nomination.id in expert.expert_nominations or expert.expert_nominations == []:
                    await bot.api.messages.send(user_id=expert.vk_id, message=f"Новое выступление ожидает вашей оценки.", random_id=0,
                                                keyboard=Keyboard(inline=True).row().add(
                                                    Text("Оценить"), color=KeyboardButtonColor.POSITIVE))
        elif state == "decline":
            users_actions[event.user_id] = {"cmd": "moderator", "state": "decline", "user_contest": user_contest.id}
            await event.edit_message("Пришлите причину отклонения.")
            return
        elif state == "ban":
            await event.edit_message("Недоступно.")
            return


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "expert"}))
async def expert(event: MessageEvent):
    state = event.payload.get("state", "vote")
    if state == "vote":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)
        user_contest = UserContest.get_by_id(int(event.payload.get("user_contest")))
        if user_contest is None:
            await event.edit_message(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                     keyboard=Constants.SUPPORT_KEYBOARD)
            return

        rated = event.payload.get("rated", {})
        unrated = [x.id for x in ContestRateType.get_all_rate_types() if x.id not in [int(y) for y in list(rated.keys())]]

        for rate_type_id in unrated:
            rate_type = ContestRateType.get_by_id(rate_type_id)
            users_actions[event.user_id] = {"cmd": "expert", "state": "vote", "user_contest": user_contest.id, "rate_type": rate_type_id, "rated": rated}
            await event.edit_message(f"Пришлите вашу оценку для {rate_type.name}.\nОценка должна быть в пределе от %s до %s." % (rate_type.min_value, rate_type.max_value))
            return

        users_actions[event.user_id] = {"cmd": "expert", "state": "vote", "user_contest": user_contest.id, "rate_type": -1, "rated": rated}
        await event.edit_message(f"Пришлите комментарий для пользователя.")

    elif state == "vote_confirm":
        await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)
        user_contest = UserContest.get_by_id(int(event.payload.get("user_contest")))
        if user_contest is None:
            await event.edit_message(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                     keyboard=Constants.SUPPORT_KEYBOARD)
            return

        rated = event.payload.get("rated", {})
        contest_rate = UserContestRate()
        contest_rate.user_contest = user_contest
        contest_rate.feedback = event.payload.get("comment")

        if User.get_by_vk_id(event.user_id).role == "admin":
            import vk_admin_bot

            contest_rate.voted_by_admin = True
            expert_id = User.get_by_vk_id(vk_admin_bot.admins_as_experts[event.user_id]).id
        else:
            expert_id = User.get_by_vk_id(event.user_id).id

        contest_rate.expert = User.get_by_id(expert_id)
        contest_rate.save_to_db()

        del contest_rate
        contest_rate = UserContestRate.get_rates_by_user_contest_id_and_expert_id(user_contest.id, expert_id)

        for rate_type_id in rated.keys():
            contest_rate_value = UserContestRateValue()
            contest_rate_value.user_contest_rate = contest_rate
            contest_rate_value.contest_rate_type = ContestRateType.get_by_id(rate_type_id)
            contest_rate_value.rate_value = int(rated[rate_type_id])
            contest_rate_value.save_to_db()

        del users_actions[event.user_id]
        await event.edit_message("Ваша оценка принята!", keyboard=Keyboard(inline=True).row().add(
            Text("Продолжить"), color=KeyboardButtonColor.SECONDARY).get_json())

        for admin in User.get_all_members_by_role("admin"):
            await bot.api.messages.send(user_id=admin.vk_id,
                                        message=f"Эксперт оценил работу #{user_contest.id}.\n\nНоминация: {user_contest.nomination.name}\nГруппа: {user_contest.group.name}\n\nИнформация о номинанте:\nФ.И.О.:"
                                                f" {user_contest.name}\nШкола: "
                                                f"{user_contest.school}\nEmail: {user_contest.email}\nТелефон: {user_contest.phone_number}\nУчитель: {user_contest.teacher}\n\nОтправитель: @id"
                                                f"{User.get_by_vk_id(user_contest.contest_member.user.vk_id).vk_id} ("
                                                f"{User.get_by_vk_id(user_contest.contest_member.user.vk_id).first_name} {User.get_by_vk_id(user_contest.contest_member.user.vk_id).last_name})\nПолученный текст: {user_contest.text.author}. "
                                                f"{user_contest.text.name}\n\n" + [f'{ContestRateType.get_by_id(t).name}: {v}/{ContestRateType.get_by_id(t).max_value}\n' for t, v in
                                                                                   rated.items()] + f'Комментарий: {event.payload.get("comment")}',
                                        attachment=user_contest.sended_work,
                                        random_id=0)

        await bot.api.messages.send(user_id=user_contest.contest_member.user.vk_id, message=f"Ваше выступление в конкурсе #{user_contest.id} оценено экспертом. Средняя оценка: %s.\n\nКомментарий эксперта: %s" % (sum(rated.values()) / len(
            rated.values()), event.payload.get("comment")), random_id=0,
                                    keyboard=Keyboard(inline=True).row().add(
                                        Callback("Открыть участие", payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")))


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadContainsRule({"cmd": "vote"}))
async def vote(event: MessageEvent):
    await task_executer.execute()

    await event.show_snackbar(Constants.PLEASE_WAIT_MESSAGE)

    user_contest = UserContest.get_by_id(int(event.payload.get("user_contest")))
    if user_contest is None:
        await event.edit_message(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                 keyboard=Constants.SUPPORT_KEYBOARD)
        return

    if user_contest.contest.winners_date < time.time():
        await event.edit_message("Конкурс уже завершен.", keyboard=Keyboard(inline=True).row().add(
            Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())
        return

    if not user_contest.is_approved:
        await event.edit_message("Работа не была одобрена.", keyboard=Keyboard(inline=True).row().add(
            Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())
        return

    user = User.get_by_vk_id(event.user_id)
    if user.voted:
        await event.edit_message("Вы уже голосовали.", keyboard=Keyboard(inline=True).row().add(
            Callback(Constants.PREV_TEXT, payload=event.payload | {"state": "show_play"})).get_json())
        return

    user.voted = True
    user.save_to_db()

    user_contest.user_votes += 1
    user_contest.save_to_db()

    await event.edit_message("Спасибо за ваш голос!", keyboard=Keyboard(inline=True).row().add(
        Text(Constants.MAIN_MENU_TEXT)).get_json())


@bot.on.message(text="<msg>")
async def one_message(message: Message, msg: str = ""):
    global runTasks
    import vk_admin_bot

    await task_executer.execute()

    vk_user = await message.get_user()
    user = User.get_by_vk_id(vk_user.id)

    if user is None:
        user = User()

    user.vk_id = vk_user.id
    user.first_name = vk_user.first_name
    user.last_name = vk_user.last_name
    user.domain = vk_user.domain
    user.save_to_db()

    if user.accepted_rules is None:
        if message.text == "Принять":
            user.accepted_rules = time.time()
            user.save_to_db()
        else:
            await message.answer("Перед использованием бота вам необходимо принять наши правила.", keyboard=Keyboard(inline=True).add(
                OpenLink("https://example.com/", "Правила")).row().add(
                Text("Принять", {"cmd": "accept_rules"})
            ).get_json())
            return

    if user.isBanned:
        await message.answer(Constants.BANNED_MESSAGE % user.ban_reason, keyboard=Constants.SUPPORT_KEYBOARD)
        return
    if message.ref_source == "user_vote":
        if user.voted:
            await message.answer("Вы уже голосовали.", keyboard=config.Constants.SUPPORT_KEYBOARD)
            return

        await message.answer("Вы уверены, что хотите проголосовать за данное выступление?", keyboard=Keyboard(inline=True).row().add(
            Callback("Проголосовать", payload={"cmd": "vote", "user_contest": message.ref})).row().add(
            Text("Отменить"), color=KeyboardButtonColor.NEGATIVE).get_json())
        return

    if user.role == "member":
        member = user.get_as_contest_member()

        if vk_user.id in users_actions and "главное меню" not in msg.lower():
            if users_actions[vk_user.id]["state"] == "send_work":
                user_contest = UserContest.get_by_id(int(users_actions[vk_user.id]["user_contest"]))
                await message.answer("Неверный формат файла.", keyboard=Keyboard(inline=True).row().add(
                    Callback(Constants.PREV_TEXT, payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).get_json())
            if users_actions[vk_user.id]["state"] == "fill_member_info":
                member_info = message.text.split("\n")
                if len(member_info) != 5:
                    await message.answer("Неверный формат сообщения.", keyboard=Keyboard(inline=True).row().add(
                        Callback(Constants.PREV_TEXT, payload={"cmd": "join_contest", "state": "start"})).get_json())
                    return

                groups_keyboard = Keyboard(inline=True)
                for group in ContestGroup.get_all_groups():
                    groups_keyboard.add(
                        Callback(group.name, payload={"cmd": "join_contest", "state": "select_nomination", "group": group.id} | {"member_name": member_info[0], "member_school": member_info[1], "member_email": member_info[2],
                                                                                                                                 "member_teacher": member_info[3], "member_phone": member_info[4]}))
                    groups_keyboard.row()
                groups_keyboard.add(Text(Constants.MAIN_MENU_TEXT), color=KeyboardButtonColor.NEGATIVE)
                await message.answer(Constants.MEMBER_SELECT_GROUP_MESSAGE, keyboard=groups_keyboard.get_json())
                return

            del users_actions[vk_user.id]
        await message.answer(Constants.MEMBER_PROFILE_MESSAGE % (user.first_name, len(member.get_user_contests())),
                             keyboard=Keyboard(inline=True).add(
                                 Callback(Constants.LETS_PLAY_TEXT, {"cmd": "join_contest", "state": "start"}))
                             .row().add(Callback(Constants.PLAYS_TEXT, payload={"cmd": "my_plays"})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")).get_json())
    elif user.role == "moderator":
        if "меню админ" in msg.lower():
            await vk_admin_bot.one_message(message, msg, user)
            return
        if vk_user.id in users_actions:
            if users_actions[vk_user.id]["state"] == "decline":
                user_contest = UserContest.get_by_id(int(users_actions[vk_user.id]["user_contest"]))
                user_contest.is_approved = False
                user_contest.is_checking = False
                user_contest.can_send_work = True
                user_contest.sended_work = None
                user_contest.declined_reason = message.text
                user_contest.deadline += time.time() + user_contest.contest.time_for_send * 60
                user_contest.save_to_db()

                for admin in User.get_all_members_by_role("admin"):
                    await bot.api.messages.send(user_id=admin.vk_id,
                                                message=f"Модератор отклонил работу #{user_contest.id}.\n\nНоминация: {user_contest.nomination.name}\nГруппа: {user_contest.group.name}\n\nИнформация о номинанте:\nФ.И.О.:"
                                                        f" {user_contest.name}\nШкола: "
                                                        f"{user_contest.school}\nEmail: {user_contest.email}\nТелефон: {user_contest.phone_number}\nУчитель: {user_contest.teacher}\n\nОтправитель: @id"
                                                        f"{User.get_by_vk_id(user_contest.contest_member.user.vk_id).vk_id} ("
                                                        f"{User.get_by_vk_id(user_contest.contest_member.user.vk_id).first_name} {User.get_by_vk_id(user_contest.contest_member.user.vk_id).last_name})\nПолученный текст: {user_contest.text.author}. "
                                                        f"{user_contest.text.name}\n\nПричина отклонения: {message.text}", attachment=user_contest.sended_work, random_id=0)

                await bot.api.messages.send(user_id=user_contest.contest_member.user.vk_id, message=f"Ваш отклик в конкурсе #{user_contest.id} отклонен модератором по причине: {message.text}", random_id=0,
                                            keyboard=Keyboard(inline=True).row().add(
                                                Callback("Открыть участие", payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")))

                await message.answer("Работа отклонена!")
            elif users_actions[vk_user.id]["state"] == "ban":
                user_contest = UserContest.get_by_id(int(users_actions[vk_user.id]["user_contest"]))
                user_contest.is_approved = False
                user_contest.is_checking = False
                user_contest.can_send_work = False
                user_contest.is_banned = True
                user_contest.ban_reason = message.text
                user_contest.save_to_db()

                await bot.api.messages.send(user_id=user_contest.contest_member.user.vk_id, message=f"Ваше участие в конкурсе #{user_contest.id} заблокировано модератором по причине: {message.text}", random_id=0,
                                            keyboard=Keyboard(inline=True).row().add(
                                                Callback("Открыть участие", payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")))

                await message.answer("Пользователь забанен!")
            del users_actions[vk_user.id]

        checking = UserContest.get_all_checking()
        if len(checking) == 0:
            await message.answer("Нет работ на проверку.", keyboard=Keyboard(inline=True).row().add(
                Text(Constants.MAIN_MENU_TEXT), color=KeyboardButtonColor.NEGATIVE).get_json())
            return

        for user_contest in checking:
            await message.answer(f"Работа #%s\n\n{user_contest.text.author}. {user_contest.text.name}\n{user_contest.text.text}" % user_contest.id, attachment=user_contest.sended_work, keyboard=Keyboard(inline=True).row().add(
                Callback("Принять", payload={"cmd": "moderator", "state": "approve", "user_contest": user_contest.id})).add(
                Callback("Отклонить", payload={"cmd": "moderator", "state": "decline", "user_contest": user_contest.id}), color=KeyboardButtonColor.NEGATIVE).row().add(
                Text("Меню администратора")).get_json())
            break
    elif user.role == "expert" or vk_user.id in vk_admin_bot.admins_as_experts:
        voting = UserContestRate.get_unrated_contests_by_expert_id(user.id)
        voted = UserContestRate.get_rates_by_expert_id(user.id)
        if "главное меню" in msg.lower():
            kb = Keyboard(inline=True).row().add(
                Text("Проверить работы"), color=KeyboardButtonColor.NEGATIVE)
            if user.role == "admin":
                kb.row().add(Callback("Админ-панель", payload={"cmd": "admin_expert"}))
            users_actions[vk_user.id]["state"] = ""
            await message.answer("Добрый день.\n\nВы проверили %s работ из %s." % (len(voted), len(voted) + len(voting)), keyboard=kb.get_json() if len(voting) != 0 else None)
            return

        if vk_user.id in users_actions:
            if users_actions[vk_user.id]["state"] == "vote":
                user_contest = UserContest.get_by_id(int(users_actions[vk_user.id]["user_contest"]))
                if user_contest is None:
                    await message.answer(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                         keyboard=Constants.SUPPORT_KEYBOARD)
                    return

                if users_actions[vk_user.id]["rate_type"] == -1:
                    reply_text = "Подтвердите отправку оценок для работы #%s:\n" % user_contest.id
                    for rate_type_id, rate in users_actions[vk_user.id]["rated"].items():
                        rate_type = ContestRateType.get_by_id(rate_type_id)
                        reply_text += "%s: %s / %s\n" % (rate_type.name, rate, rate_type.max_value)

                    reply_text += "\nКомментарий: %s" % message.text

                    await message.answer(reply_text, keyboard=Keyboard(inline=True).row().add(
                        Callback("Продолжить", payload={"cmd": "expert", "state": "vote_confirm", "user_contest": user_contest.id, "rated": users_actions[vk_user.id]["rated"], "comment": message.text}),
                        color=KeyboardButtonColor.POSITIVE).add(
                        Callback("Отменить", payload={"cmd": "expert", "state": "vote", "user_contest": user_contest.id, "rated": {}}), color=KeyboardButtonColor.NEGATIVE).get_json())
                    return
                else:
                    rate_type = ContestRateType.get_by_id(int(users_actions[vk_user.id]["rate_type"]))
                    try:
                        rate = int(msg)
                        if rate < rate_type.min_value or rate > rate_type.max_value:
                            await message.answer("Оценка должна быть в пределе от %s до %s." % (rate_type.min_value, rate_type.max_value))
                            return
                    except:
                        await message.answer("Неверный формат оценки. Повторите попытку.", keyboard=Keyboard(inline=True).row().add(
                            Callback(Constants.MAIN_MENU_TEXT, payload={"cmd": "expert", "state": "vote", "user_contest": user_contest.id})).get_json())
                        return

                    await message.answer("Вы поставили оценку %s для %s.\nПришлите новую оценку, если хотите её изменить." % (rate, rate_type.name), keyboard=Keyboard(inline=True).row().add(
                        Callback("Продолжить", payload={"cmd": "expert", "state": "vote", "user_contest": user_contest.id, "rated": users_actions[vk_user.id]["rated"] | {rate_type.id: rate}}), color=KeyboardButtonColor.POSITIVE).add(
                        Callback("Отменить", payload={"cmd": "expert", "state": "vote", "user_contest": user_contest.id, "rated": {}}), color=KeyboardButtonColor.NEGATIVE).get_json())
                    return
        if len(voting) == 0:
            await message.answer("Нет работ на оценку.", keyboard=Keyboard(inline=True).row().add(
                Text(Constants.MAIN_MENU_TEXT), color=KeyboardButtonColor.NEGATIVE).get_json())
            return

        for user_contest in voting:
            await message.answer(f"Работа #%s\n\n{user_contest.text.author}. {user_contest.text.name}\n{user_contest.text.text}" % user_contest.id, attachment=user_contest.sended_work, keyboard=Keyboard(inline=True)
                                 .add(Callback("Голосовать", payload={"cmd": "expert", "state": "vote", "user_contest": user_contest.id}), color=KeyboardButtonColor.POSITIVE)
                                 .row().add(Text("Главное меню админа"), color=KeyboardButtonColor.NEGATIVE).get_json())
            break
    elif user.role == "admin":
        await vk_admin_bot.one_message(message, msg, user)
    else:
        await message.answer(Constants.SOME_ERROR_MESSAGE % "Invalid user role", keyboard=Constants.SUPPORT_KEYBOARD)

    return


@bot.on.message(AttachmentTypeRule(["video", "doc", "text"]))
async def doc_handler(message: Message):
    vk_user = await message.get_user()
    user = User.get_by_vk_id(vk_user.id)

    if user is None:
        user = User()

    user.vk_id = vk_user.id
    user.first_name = vk_user.first_name
    user.last_name = vk_user.last_name
    user.domain = vk_user.domain
    user.save_to_db()

    if user.isBanned:
        await message.answer(Constants.BANNED_MESSAGE % user.ban_reason, keyboard=Constants.SUPPORT_KEYBOARD)
        return

    if not vk_user.id in users_actions:
        return
    elif not "state" in users_actions[vk_user.id]:
        return

    if users_actions[vk_user.id]["state"] == "send_work":
        user_contest = UserContest.get_by_id(int(users_actions[vk_user.id]["user_contest"]))
        if user_contest is None:
            await message.answer(Constants.SOME_ERROR_MESSAGE % "User contest not found",
                                 keyboard=Constants.SUPPORT_KEYBOARD)
            return

        if user_contest.sended_work is not None:
            await message.answer("Вы уже отправили работу.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).get_json())
            return

        if not user_contest.can_send_work:
            await message.answer("Вы не можете отправить работу.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")).get_json())
            return

        if user_contest.finished != -1:
            await message.answer("Конкурс завершен.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).get_json())
            return

        if time.time() > user_contest.deadline:
            await message.answer("Время на отправку работы истекло.", keyboard=Keyboard(inline=True).row().add(
                Callback(Constants.PREV_TEXT, payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).row().add(OpenLink(Constants.SUPPORT_URL, "Обратиться в поддержку")).get_json())
            return

        if message.attachments[0].type.value == "video":
            data = message.attachments[0].video
        else:
            data = message.attachments[0].doc

        user_contest.sended_work = f"{message.attachments[0].type.value}{data.owner_id}_{data.id}_{data.access_key}"
        user_contest.is_checking = True
        user_contest.is_approved = False
        user_contest.can_send_work = False
        user_contest.save_to_db()

        await message.answer("Работа отправлена!", keyboard=Keyboard(inline=True).row().add(
            Callback(Constants.PREV_TEXT, payload={"cmd": "my_plays", "state": "show_play", "user_contest": user_contest.id})).get_json())

        for admin in User.get_all_members_by_role("admin"):
            await bot.api.messages.send(user_id=admin.vk_id,
                                        message=f"Пользователь отправил работу на участие #{user_contest.id}.\n\nНоминация: {user_contest.nomination.name}\nГруппа: {user_contest.group.name}\n\nИнформация о номинанте:\nФ.И.О.: {user_contest.name}\nШкола: "
                                                f"{user_contest.school}\nEmail: {user_contest.email}\nТелефон: {user_contest.phone_number}\nУчитель: {user_contest.teacher}\n\nОтправитель: @id{message.from_id} ("
                                                f"{User.get_by_vk_id(message.from_id).first_name} {User.get_by_vk_id(message.from_id).last_name})\nПолученный текст: {user_contest.text.author}. "
                                                f"{user_contest.text.name}", attachment=user_contest.sended_work, random_id=0)

        for moderator in User.get_all_members_by_role("moderator"):
            await bot.api.messages.send(user_id=moderator.vk_id, message=f"Появилась новая работа, необходимо проверить её как можно скорее!\n\n{user_contest.text.author}. {user_contest.text.name}\n{user_contest.text.text}", random_id=0,
                                        attachment=user_contest.sended_work,
                                        keyboard=Keyboard(inline=True).row().add(
                                            Callback("Принять", payload={"cmd": "moderator", "state": "approve", "user_contest": user_contest.id})).row().add(
                                            Callback("Отклонить", payload={"cmd": "moderator", "state": "decline", "user_contest": user_contest.id})).row().get_json())
        return


def run():
    bot.run_forever()
