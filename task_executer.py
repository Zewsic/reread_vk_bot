import asyncio
import json
import time

from vkbottle import Bot, Keyboard, Callback, DocUploader, DocMessagesUploader

import config
from reread_types import *

next_experts_notify = 0
next_moderators_notify = 0


def get_full_report():
    return
    full_report = {
        "date_created": time.time(),
        "nominations": []
    }
    for nomination in ContestNomination.get_all_nominations():
        experts = [expert for expert in User.get_all_members_by_role("expert") if expert.expert_nominations.__contains__(nomination.id) or expert.expert_nominations == []]
        nomination_report = {
            "name": nomination.name,
            "contests": [],
        }
        for contest in UserContest.get_all(nomination.id):
            if contest.is_banned or not contest.is_approved or contest.is_checking:
                continue
            contest_report = {
                "vk_id": contest.contest_member.user.vk_id,
                "name": contest.name,
                "school": contest.school,
                "email": contest.email,
                "teacher": contest.teacher,
                "phone_number": contest.phone_number,
                "group": contest.group.name,
                "sended_work": contest.sended_work,
                "avg_rate": contest.get_avg_rate(),
                "avg_rates": [],
                "rates": []
            }

            avg_rates = {k.id: None for k in ContestRateType.get_all_rate_types()}
            full_rates = {expert.id: [] for expert in experts}

            for rate in contest.get_rates():
                for val in rate.get_rate_values():
                    if not full_rates.__contains__(str(rate.expert.id)):
                        full_rates[rate.expert.id] = [{"name": val.contest_rate_type.name, "value": val.rate_value}]
                    else:
                        full_rates[rate.expert.id].append({"name": val.contest_rate_type.name, "value": val.rate_value})
                    if avg_rates[val.contest_rate_type.id] is None:
                        avg_rates[val.contest_rate_type.id] = val.rate_value
                    else:
                        avg_rates[val.contest_rate_type.id] += val.rate_value
                        avg_rates[val.contest_rate_type.id] /= 2

            contest_report["avg_rates"] = [{"name": ContestRateType.get_by_id(k).name, "value": v} for k, v in avg_rates.items()]
            contest_report["rates"] = [{"expert": expert.get_as_contest_member().user.first_name + " " + expert.get_as_contest_member().user.last_name, "rates": full_rates[expert.id]} for expert in experts]

            nomination_report["contests"].append(contest_report)
        full_report["nominations"].append(nomination_report)
    return full_report

async def execute():
    global next_experts_notify, next_moderators_notify
    bot = Bot(config.VK.TOKEN)

    current_time = time.time()

    if current_time >= next_experts_notify:
        next_experts_notify = current_time + (60 * 60 * 12 if Contest.get_by_id(-1).rates_date - current_time >= 60 * 60 * 24 * 3 else 60 * 60 * 24)

        for expert in User.get_all_members_by_role("expert"):
            if len(UserContestRate.get_unrated_contests_by_expert_id(expert.id)) > 0:
                try:
                    await bot.api.messages.send(peer_id=expert.vk_id, message="У вас есть неоцененные конкурсы (%s), оцените их как можно скорее!" % len(UserContestRate.get_unrated_contests_by_expert_id(expert.id)), random_id=0)
                except: ...
    if current_time >= next_moderators_notify:
        next_moderators_notify = current_time + 60 * 60 * 12

        if len(UserContest.get_all_checking()) > 0:
            for moderator in User.get_all_members_by_role("moderator"):
                try:
                    await bot.api.messages.send(peer_id=moderator.vk_id, message="У вас есть непроверенные конкурсы (%s), проверьте их как можно скорее!" % len(UserContest.get_all_checking()), random_id=0)
                except: ...
    if current_time >= Contest.get_by_id(-1).rates_date:
        with open("report.json", "w+") as f:
            f.write(json.dumps(get_full_report(), ensure_ascii=False))

        # for admin in User.get_all_members_by_role("admin"):
        #
        #     photo = await DocMessagesUploader(bot.api).upload(
        #         file_source="report.json",
        #         peer_id=admin.vk_id,
        #         title="Отчёт по конкурсу"
        #     )
        #     await bot.api.messages.send(peer_id=admin.vk_id, message="Начинается процесс подведения итогов конкурса, ожидайте...", random_id=0, attachment=photo)
        Contest.get_by_id(-1).rates_date = 0
        for user_contest in UserContest.get_all_ready_for_votes():
            try:
                await bot.api.messages.send(peer_id=user_contest.contest_member.user.vk_id, message="По вашей работе в конкурсе \"%s\" оставлены оценки экспертами. Перейдите в раздел \"Мои участия\" для просмотра." %
                                                                                                user_contest.contest.name, random_id=0, keyboard=Keyboard(one_time=True, inline=False).add(Callback("Мои участия",
                                                                                                                                                           {"cmd": "plays"})).get_json())
            except:
                ...

