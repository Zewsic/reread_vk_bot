import random
from typing import List

from sqlalchemy import exists

import database as DB


class User:
    id: int = -1
    vk_id: int = -1
    first_name: str = "Pavel"
    last_name: str = "Durov"
    domain: str = "durov"
    role: str = "member"
    isBanned: bool = False
    ban_reason: str = "idk"
    voted: bool = False
    expert_nominations: List[int] = []
    accepted_rules = 0

    def get_as_contest_member(self):
        member = ContestMember.get_by_user_id(self.id)
        if member is None:
            member = ContestMember()
            member.user = self
            member.save_to_db()
        return member

    def save_to_db(self):
        session = DB.Session()
        if session.query(exists().where(DB.User.id == self.id)).scalar():
            user = session.query(DB.User).filter_by(id=self.id).first()
            user.vk_id = self.vk_id
            user.first_name = self.first_name
            user.last_name = self.last_name
            user.domain = self.domain
            user.role = self.role
            user.isBanned = self.isBanned
            user.ban_reason = self.ban_reason
            user.voted = self.voted
            user.expert_nominations = ",".join(self.expert_nominations) if len(self.expert_nominations) > 0 else ""
            user.accepted_rules = self.accepted_rules
        else:
            session.add(DB.User(vk_id=self.vk_id, first_name=self.first_name, last_name=self.last_name,
                                domain=self.domain, role=self.role, isBanned=self.isBanned, ban_reason=self.ban_reason, voted=self.voted, expert_nominations=",".join(self.expert_nominations) if len(self.expert_nominations) > 0 else ""),
                        accepted_rules=self.accepted_rules)
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(user_id: int = -1):
        session = DB.Session()
        user = None

        if session.query(exists().where(DB.User.id == user_id)).scalar():
            db_user = session.query(DB.User).filter_by(id=user_id).first()

            user = User()
            user.id = db_user.id
            user.vk_id = db_user.vk_id
            user.first_name = db_user.first_name
            user.last_name = db_user.last_name
            user.domain = db_user.domain
            user.role = db_user.role
            user.isBanned = db_user.isBanned
            user.ban_reason = db_user.ban_reason
            user.voted = db_user.voted
            user.expert_nominations = [int(x) for x in db_user.expert_nominations.split(",")] if len(db_user.expert_nominations) > 0 else []
            user.accepted_rules = db_user.accepted_rules

        session.close()
        return user

    @staticmethod
    def get_by_vk_id(vk_id: int = -1):
        session = DB.Session()
        user = None

        if session.query(exists().where(DB.User.vk_id == vk_id)).scalar():
            db_user = session.query(DB.User).filter_by(vk_id=vk_id).first()

            user = User()
            user.id = db_user.id
            user.vk_id = db_user.vk_id
            user.first_name = db_user.first_name
            user.last_name = db_user.last_name
            user.domain = db_user.domain
            user.role = db_user.role
            user.isBanned = db_user.isBanned
            user.ban_reason = db_user.ban_reason
            user.voted = db_user.voted
            user.expert_nominations = [int(x) for x in db_user.expert_nominations.split(",")] if len(db_user.expert_nominations) > 0 else []
            user.accepted_rules = db_user.accepted_rules

        session.close()
        return user

    @staticmethod
    def get_all_members_by_role(role: str = "member"):
        session = DB.Session()
        users = [User.get_by_id(x.id) for x in session.query(DB.User).filter_by(role=role).all()]
        session.close()
        return users


class Contest:
    id: int = -1
    start_date: int = -1
    finish_date: int = -1
    rates_date: int = -1
    winners_date: int = -1
    time_for_send: int = -1
    price: int = -1

    def save_to_db(self):
        session = DB.Session()
        if session.query(exists().where(DB.Contest.id == self.id)).scalar():
            contest = session.query(DB.Contest).filter_by(id=self.id).first()
            contest.start_date = self.start_date
            contest.finish_date = self.finish_date
            contest.rates_date = self.rates_date
            contest.winners_date = self.winners_date
            contest.time_for_send = self.time_for_send
            contest.price = self.price
        else:
            session.add(DB.Contest(id=self.id, start_date=self.start_date, finish_date=self.finish_date,
                                   rates_date=self.rates_date,
                                   winners_date=self.winners_date, time_for_send=self.time_for_send, price=self.price))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(contest_id: int = -1):
        session = DB.Session()
        contest = None

        if session.query(exists().where(DB.Contest.id == contest_id)).scalar():
            db_contest = session.query(DB.Contest).filter_by(id=contest_id).first()

            contest = Contest()
            contest.id = db_contest.id
            contest.start_date = db_contest.start_date
            contest.finish_date = db_contest.finish_date
            contest.rates_date = db_contest.rates_date
            contest.winners_date = db_contest.winners_date
            contest.time_for_send = db_contest.time_for_send
            contest.price = db_contest.price

        session.close()
        return contest


class ContestRateType:
    id: int = -1
    name: str = "len"
    min_value: int = -1
    max_value: int = -1

    def save_to_db(self):
        session = DB.Session()
        if session.query(exists().where(DB.ContestRateType.id == self.id)).scalar():
            contest_rate_type = session.query(DB.ContestRateType).filter_by(id=self.id).first()
            contest_rate_type.name = self.name
            contest_rate_type.min_value = self.min_value
            contest_rate_type.max_value = self.max_value
        else:
            session.add(
                DB.ContestRateType(name=self.name, min_value=self.min_value, max_value=self.max_value))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(contest_rate_type_id: int = -1):
        session = DB.Session()
        contest_rate_type = None

        if session.query(exists().where(DB.ContestRateType.id == contest_rate_type_id)).scalar():
            db_contest_rate_type = session.query(DB.ContestRateType).filter_by(id=contest_rate_type_id).first()

            contest_rate_type = ContestRateType()
            contest_rate_type.id = db_contest_rate_type.id
            contest_rate_type.name = db_contest_rate_type.name
            contest_rate_type.min_value = db_contest_rate_type.min_value
            contest_rate_type.max_value = db_contest_rate_type.max_value

        session.close()
        return contest_rate_type

    @staticmethod
    def get_all_rate_types():
        session = DB.Session()
        rate_types = [ContestRateType.get_by_id(rt.id) for rt in session.query(DB.ContestRateType).all()]
        session.close()
        return rate_types

    def delete_from_db(self):
        session = DB.Session()
        session.query(DB.ContestRateType).filter_by(id=self.id).delete()
        session.commit()
        session.close()



class ContestNomination:
    id: int = -1
    name: str = "good_speaking"

    def save_to_db(self):
        session = DB.Session()
        if session.query(exists().where(DB.ContestNomination.id == self.id)).scalar():
            contest_rate_type = session.query(DB.ContestNomination).filter_by(id=self.id).first()
            contest_rate_type.name = self.name
        else:
            session.add(DB.ContestNomination(name=self.name))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(contest_nomination_id: int = -1):
        session = DB.Session()
        contest_nomination = None

        if session.query(exists().where(DB.ContestNomination.id == contest_nomination_id)).scalar():
            db_contest_nomination = session.query(DB.ContestNomination).filter_by(id=contest_nomination_id).first()

            contest_nomination = ContestNomination()
            contest_nomination.id = db_contest_nomination.id
            contest_nomination.name = db_contest_nomination.name

        session.close()
        return contest_nomination

    @staticmethod
    def get_all_nominations():
        session = DB.Session()
        nominations = [ContestNomination.get_by_id(nom.id) for nom in session.query(DB.ContestNomination).all()]
        session.close()
        return nominations

    def delete_from_db(self):
        session = DB.Session()
        session.query(DB.ContestNomination).filter_by(id=self.id).delete()
        session.commit()
        session.close()

        for text in ContestText.get_all_texts(nomination_id=self.id):
            text.delete_from_db()


class ContestGroup:
    id: int = -1
    name: str = "womans"

    def save_to_db(self):
        session = DB.Session()
        if session.query(exists().where(DB.ContestGroup.id == self.id)).scalar():
            contest_rate_type = session.query(DB.ContestGroup).filter_by(id=self.id).first()
            contest_rate_type.name = self.name
        else:
            session.add(DB.ContestGroup(name=self.name))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(contest_group_id: int = -1):
        session = DB.Session()
        contest_group = None

        if session.query(exists().where(DB.ContestGroup.id == contest_group_id)).scalar():
            db_contest_group = session.query(DB.ContestGroup).filter_by(id=contest_group_id).first()

            contest_group = ContestGroup()
            contest_group.id = db_contest_group.id
            contest_group.name = db_contest_group.name

        session.close()
        return contest_group

    @staticmethod
    def get_all_groups():
        session = DB.Session()
        nominations = [ContestGroup.get_by_id(gr.id) for gr in session.query(DB.ContestGroup).all()]
        session.close()
        return nominations

    def delete_from_db(self):
        session = DB.Session()
        session.query(DB.ContestGroup).filter_by(id=self.id).delete()
        session.commit()
        session.close()

        for text in ContestText.get_all_texts(group_id=self.id):
            text.delete_from_db()

class ContestText:
    id: int = -1
    group: ContestGroup = None
    nomination: ContestNomination = None
    name: str = "history of alisher"
    author: str = "oxxxymiron"
    text: str = '''The clown is so looking for love and a little warmth The clown is afraid of love Wears a cap, but it's spiked The clown wants to be friends Only something is wrong with him The clown is bitterly sarcastic It hurts in my chest, again rejection I've been dissed by the clown Maybe I should pass by? I've been dissed by a clown What should I do with him? (What should I do with him?) I'd ignore the clown, but this clown is too serious But this clown is too serious He wants to be cooler, he's a clown, he's an annoying, annoying prickle An ugly year waddles into the sunset Knee-deep in blood It's my business to entertain you with trifles during the war And what's more trifling than an artist's fragile ego? Don't let a joker commit suicide There's no one more vulnerable than a postironist I don't want to give it to anyone I don't want to dig around in my head, bitch I'm afraid they'll dig something up E-yo, grandson, understand Your diss is a love letter Morgen-Stan, pure mashups Golden quotes, ala, you make up everything I didn't pull your pigtails I don't like you I don't like you Shit! You want it back so bad, but why the fuck do they need another dreadlocked farm boy? They've got SHAMAN's "Dick, Penis, Dick" - it's a hit, no doubt about it But where have you been for eight years? Parody But you didn't have the charisma to portray me You're a satire on Satire! Don't read any more! Fuck, of course you're hurt by my beats You're getting fucked by Oxxxymiron type beats Explain to your fucking kids How you called me out on "Legendary Dust" On "Million Dollar", on "12", on "Last One" And every time I said no, I got a hit Cause you need a Mark To do the marketing I'm the new Pusha T, fuck Six-Six-Six Break your forehead to XXX, change your name and passport.'''

    def save_to_db(self):
        session = DB.Session()
        if session.query(exists().where(DB.ContextText.id == self.id)).scalar():
            contest_text = session.query(DB.ContextText).filter_by(id=self.id).first()
            contest_text.name = self.name
            contest_text.author = self.author
            contest_text.text = self.text
            contest_text.nomination_id = self.nomination.id
            contest_text.group_id = self.group.id
        else:
            session.add(DB.ContextText(name=self.name, author=self.author, text=self.text, nomination_id=self.nomination.id, group_id=self.group.id))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(contest_text_id: int = -1):
        session = DB.Session()
        contest_text = None

        if session.query(exists().where(DB.ContextText.id == contest_text_id)).scalar():
            db_contest_text = session.query(DB.ContextText).filter_by(id=contest_text_id).first()

            contest_text = ContestText()
            contest_text.id = db_contest_text.id
            contest_text.name = db_contest_text.name
            contest_text.author = db_contest_text.author
            contest_text.text = db_contest_text.text
            contest_text.nomination = ContestNomination.get_by_id(db_contest_text.nomination_id)
            contest_text.group = ContestGroup.get_by_id(db_contest_text.group_id)

        session.close()
        return contest_text

    @staticmethod
    def get_all_texts(group_id: int = None, nomination_id: int = None):
        session = DB.Session()
        texts = []
        if group_id is None and nomination_id is None:
            texts = [ContestText.get_by_id(x.id) for x in session.query(DB.ContextText).all()]
        elif group_id is not None and nomination_id is None:
            texts = [ContestText.get_by_id(x.id) for x in session.query(DB.ContextText).filter_by(group_id=group_id).all()]
        elif group_id is None and nomination_id is not None:
            texts = [ContestText.get_by_id(x.id) for x in session.query(DB.ContextText).filter_by(nomination_id=nomination_id).all()]
        elif group_id is not None and nomination_id is not None:
            texts = [ContestText.get_by_id(x.id) for x in session.query(DB.ContextText).filter_by(group_id=group_id, nomination_id=nomination_id).all()]
        session.close()
        return texts

    @staticmethod
    def get_random_text(group_id: int, nomination_id: int):
        texts = ContestText.get_all_texts(group_id, nomination_id)
        random.shuffle(texts)
        return texts[0]

    def delete_from_db(self):
        session = DB.Session()
        session.query(DB.ContextText).filter_by(id=self.id).delete()
        session.commit()
        session.close()

class ContestMember:
    id: int = -1
    user: User = None

    def get_user_contests(self):
        session = DB.Session()

        user_contests = []
        db_user_contests = session.query(DB.UserContest).filter_by(member_id=self.id).all()

        for ucd in db_user_contests:
            user_contest = UserContest()
            user_contest.id = ucd.id
            user_contest.contest_member = self
            user_contest.text = ContestText.get_by_id(ucd.text_id)
            user_contest.contest = Contest.get_by_id(ucd.contest_id)
            user_contest.group = ContestGroup.get_by_id(ucd.group_id)
            user_contest.nomination = ContestNomination.get_by_id(ucd.nomination_id)
            user_contests.append(user_contest)

        return user_contests

    def save_to_db(self):
        session = DB.Session()
        if session.query(exists().where(DB.ContestMember.user_id == self.user.id)).scalar():
            contest_member = session.query(DB.ContestMember).filter_by(id=self.id).first()
            contest_member.user_id = self.user.id
        else:
            session.add(DB.ContestMember(user_id=self.user.id))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(contest_member_id: int = -1):
        session = DB.Session()
        contest_member = None

        if session.query(exists().where(DB.ContestMember.id == contest_member_id)).scalar():
            db_contest_text = session.query(DB.ContestMember).filter_by(id=contest_member_id).first()

            contest_member = ContestMember()
            contest_member.id = db_contest_text.id
            contest_member.user = User.get_by_id(db_contest_text.user_id)

        session.close()
        return contest_member

    @staticmethod
    def get_by_user_id(user_id: int = -1):
        session = DB.Session()
        contest_member = None

        if session.query(exists().where(DB.ContestMember.user_id == user_id)).scalar():
            db_contest_text = session.query(DB.ContestMember).filter_by(user_id=user_id).first()

            contest_member = ContestMember()
            contest_member.id = db_contest_text.id
            contest_member.user = User.get_by_id(user_id)

        session.close()
        return contest_member


class UserContest:
    id: int = -1
    contest_member: ContestMember = None

    text: ContestText = None
    contest: Contest = None
    nomination: ContestNomination = None
    group: ContestGroup = None

    name: str = "alisher"
    school: str = "school"
    email: str = "email"
    phone_number: str = "phone"
    teacher: str = "teacher"

    started: int = -1
    deadline: int = -1
    finished: int = -1
    sended_work: str = None

    is_banned: bool = False
    ban_reason: str = "for fun"

    is_checking: bool = False
    is_approved: bool = False
    declined_reason: str = "lol"

    can_send_work: bool = True
    user_votes: int = 0

    def get_rates(self):
        session = DB.Session()

        rates = []
        db_user_rates = session.query(DB.UserContestRate).filter_by(user_contest_id=self.id).all()

        for r in db_user_rates:
            rate = UserContestRate()
            rate.user_contest = self
            rate.expert = User.get_by_id(r.expert_id)
            rate.feedback = r.feedback
            rates.append(rate)

        session.close()
        return rates

    def save_to_db(self):
        session = DB.Session()
        if session.query(exists().where(DB.UserContest.id == self.id)).scalar():
            user_contest = session.query(DB.UserContest).filter_by(id=self.id).first()
            user_contest.member_id = self.contest_member.id
            user_contest.text_id = self.text.id
            user_contest.contest_id = self.contest.id
            user_contest.nomination_id = self.nomination.id
            user_contest.group_id = self.group.id

            user_contest.name = self.name
            user_contest.school = self.school
            user_contest.email = self.email
            user_contest.phone_number = self.phone_number
            user_contest.teacher = self.teacher

            user_contest.started = self.started
            user_contest.deadline = self.deadline
            user_contest.finished = self.finished
            user_contest.sended_work = self.sended_work

            user_contest.isBanned = self.is_banned
            user_contest.ban_reason = self.ban_reason
            user_contest.isChecking = self.is_checking
            user_contest.isApproved = self.is_approved
            user_contest.declined_reason = self.declined_reason
            user_contest.canSendWork = self.can_send_work
            user_contest.user_votes = self.user_votes
        else:
            session.add(DB.UserContest(member_id=self.contest_member.id, text_id=self.text.id,
                                       contest_id=self.contest.id, nomination_id=self.nomination.id,
                                       group_id=self.group.id,
                                       started=self.started, deadline=self.deadline, finished=self.finished,
                                       isBanned=self.is_banned, ban_reason=self.ban_reason,
                                       isChecking=self.is_checking, isApproved=self.is_approved,
                                       declined_reason=self.declined_reason, canSendWork=self.can_send_work, sended_work=self.sended_work, name=self.name, school=self.school, email=self.email, phone_number=self.phone_number,
                                       teacher=self.teacher, user_votes=self.user_votes))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(user_contest_id: int = -1):
        session = DB.Session()
        user_contest = None

        if session.query(exists().where(DB.UserContest.id == user_contest_id)).scalar():
            db_user_contest = session.query(DB.UserContest).filter_by(id=user_contest_id).first()

            user_contest = UserContest()
            user_contest.id = db_user_contest.id
            user_contest.contest_member = ContestMember.get_by_id(db_user_contest.member_id)
            user_contest.text = ContestText.get_by_id(db_user_contest.text_id)
            user_contest.contest = Contest.get_by_id(db_user_contest.contest_id)
            user_contest.nomination = ContestNomination.get_by_id(db_user_contest.nomination_id)
            user_contest.group = ContestGroup.get_by_id(db_user_contest.group_id)

            user_contest.name = db_user_contest.name
            user_contest.school = db_user_contest.school
            user_contest.email = db_user_contest.email
            user_contest.teacher = db_user_contest.teacher
            user_contest.phone_number = db_user_contest.phone_number

            user_contest.started = db_user_contest.started
            user_contest.deadline = db_user_contest.deadline
            user_contest.finished = db_user_contest.finished
            user_contest.sended_work = db_user_contest.sended_work if db_user_contest.sended_work != "" else None

            user_contest.is_banned = db_user_contest.isBanned
            user_contest.ban_reason = db_user_contest.ban_reason
            user_contest.is_checking = db_user_contest.isChecking
            user_contest.is_approved = db_user_contest.isApproved
            user_contest.declined_reason = db_user_contest.declined_reason
            user_contest.can_send_work = db_user_contest.canSendWork
            user_contest.user_votes = db_user_contest.user_votes

        session.close()
        return user_contest

    @staticmethod
    def get_by_nomination_id_and_group_id(nomination_id: int, group_id: int) -> List:
        session = DB.Session()
        user_contests = [UserContest.get_by_id(x.id) for x in session.query(DB.UserContest).filter_by(nomination_id=nomination_id, group_id=group_id).all()]
        session.close()
        return user_contests

    @staticmethod
    def get_all_checking():
        session = DB.Session()
        user_contests = [UserContest.get_by_id(x.id) for x in session.query(DB.UserContest).filter_by(isChecking=True).all()]
        session.close()
        return user_contests

    def is_ready_for_votes(self):
        return self.is_approved and not self.is_banned and not self.is_checking

    def get_avg_rate(self):
        rates = self.get_rates()
        if len(rates) == 0:
            return 0
        avg = 0
        for rate in rates:
            rate_avg = 0
            for rate_value in rate.get_rate_values():
                rate_avg += rate_value.rate_value
                rate_avg /= 2
            avg += rate_avg
        avg /= len(rates)
        return avg

    @staticmethod
    def get_all_ready_for_votes():
        session = DB.Session()
        user_contests = [UserContest.get_by_id(x.id) for x in session.query(DB.UserContest).filter_by(isChecking=False, isApproved=True, isBanned=False).all()]
        session.close()
        return user_contests

    @staticmethod
    def get_all_non_finished(group=None):
        session = DB.Session()
        if group is None:
            user_contests = [UserContest.get_by_id(x.id) for x in session.query(DB.UserContest).filter_by(finished=-1).all()]
        else:
            user_contests = [UserContest.get_by_id(x.id) for x in session.query(DB.UserContest).filter_by(finished=-1, group_id=group.id).all()]
        session.close()
        return user_contests

    @staticmethod
    def get_all(nomination_id=None):
        session = DB.Session()
        if nomination_id is None:
            user_contests = [UserContest.get_by_id(x.id) for x in session.query(DB.UserContest).all()]
        else:
            user_contests = [UserContest.get_by_id(x.id) for x in session.query(DB.UserContest).filter_by(nomination_id=nomination_id).all()]
        session.close()
        return user_contests

class UserContestRate:
    id: int = -1
    user_contest: UserContest = None
    expert: User = None
    feedback: str = "all ok"
    voted_by_admin: bool = False

    def get_rate_values(self):
        session = DB.Session()

        rate_values = []
        db_rate_values = session.query(DB.UserContestRateValue).filter_by(user_contest_rate_id=self.id).all()

        for rv in db_rate_values:
            rate_value = UserContestRateValue()
            rate_value.user_contest_rate = self
            rate_value.contest_rate_type = ContestRateType.get_by_id(rv.contest_rate_id)
            rate_value.rate_value = rv.rate_value
            rate_values.append(rate_value)

        session.close()
        return rate_values

    def save_to_db(self):
        session = DB.Session()

        if session.query(exists().where(DB.UserContestRate.id == self.id)).scalar():
            contest_rate = session.query(DB.UserContestRate).filter_by(id=self.id).first()
            contest_rate.user_contest_id = self.user_contest.id
            contest_rate.expert_id = self.expert.id
            contest_rate.feedback = self.feedback
            contest_rate.voted_by_admin = self.voted_by_admin
        else:
            session.add(DB.UserContestRate(user_contest_id=self.user_contest.id, expert_id=self.expert.id,
                                           feedback=self.feedback, voted_by_admin=self.voted_by_admin))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(contest_rate_id: int = -1):
        session = DB.Session()
        contest_rate = None

        if session.query(exists().where(DB.UserContestRate.id == contest_rate_id)).scalar():
            db_user_contest_rate = session.query(DB.UserContestRate).filter_by(id=contest_rate_id).first()

            contest_rate = UserContestRate()
            contest_rate.id = db_user_contest_rate.id
            contest_rate.user_contest = UserContest.get_by_id(db_user_contest_rate.user_contest_id)
            contest_rate.expert = User.get_by_id(db_user_contest_rate.expert_id)
            contest_rate.feedback = db_user_contest_rate.feedback
            contest_rate.voted_by_admin = db_user_contest_rate.voted_by_admin

        session.close()
        return contest_rate

    @staticmethod
    def get_rates_by_user_contest_id_and_expert_id(user_contest_id: int = -1, expert_id: int = -1):
        session = DB.Session()
        contest_rate = session.query(DB.UserContestRate).filter_by(user_contest_id=user_contest_id, expert_id=expert_id).first()
        session.close()
        return contest_rate

    @staticmethod
    def get_rates_by_expert_id(expert_id: int = -1):
        session = DB.Session()
        contest_rates = [UserContestRate.get_by_id(x.id) for x in session.query(DB.UserContestRate).filter_by(expert_id=expert_id).all()]
        session.close()
        return contest_rates

    @staticmethod
    def get_unrated_contests_by_expert_id(expert_id: int = -1):
        session = DB.Session()
        unrated_contests = []
        ready_for_votes = UserContest.get_all_ready_for_votes()
        voted = UserContestRate.get_rates_by_expert_id(expert_id)
        for user_contest in ready_for_votes:
            is_voted = False
            for rate in voted:
                if rate.user_contest.id == user_contest.id:
                    is_voted = True
                    break
            if not is_voted:
                if user_contest.nomination.id in User.get_by_id(expert_id).expert_nominations or User.get_by_id(expert_id).expert_nominations == []:
                    unrated_contests.append(user_contest)
        session.close()
        return unrated_contests

    @staticmethod
    def get_all_rates():
        session = DB.Session()
        rates = [UserContestRate.get_by_id(x.id) for x in session.query(DB.UserContestRate).all()]
        session.close()
        return rates


class UserContestRateValue:
    id: int = -1
    user_contest_rate: UserContestRate = None
    contest_rate_type: ContestRateType = None
    rate_value: int = -1

    def save_to_db(self):
        session = DB.Session()

        if session.query(exists().where(DB.UserContestRateValue.id == self.id)).scalar():
            contest_rate_value = session.query(DB.UserContestRateValue).filter_by(id=self.id).first()
            contest_rate_value.user_contest_rate_id = self.user_contest_rate.id
            contest_rate_value.contest_rate_id = self.contest_rate_type.id
            contest_rate_value.rate_value = self.rate_value
        else:
            session.add(DB.UserContestRateValue(user_contest_rate_id=self.user_contest_rate.id,
                                                contest_rate_id=self.contest_rate_type.id,
                                                rate_value=self.rate_value))
        session.commit()
        session.close()

    @staticmethod
    def get_by_id(user_contest_rate_value_id: int = -1):
        session = DB.Session()
        contest_rate_value = None

        if session.query(exists().where(DB.UserContestRateValue.id == user_contest_rate_value_id)).scalar():
            db_user_contest_rate = session.query(DB.UserContestRateValue).filter_by(id=user_contest_rate_value_id).first()

            contest_rate_value = UserContestRateValue()
            contest_rate_value.id = db_user_contest_rate.id
            contest_rate_value.user_contest_rate = UserContestRate.get_by_id(db_user_contest_rate.user_contest_rate_id)
            contest_rate_value.contest_rate_type = ContestRateType.get_by_id(db_user_contest_rate.contest_rate_id)
            contest_rate_value.rate_value = db_user_contest_rate.rate_value

        session.close()
        return contest_rate_value
