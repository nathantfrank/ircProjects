import random
import re
# import argparse
# import json
import yaml
import time

from twisted_bot import Bot, BotFactory
from twisted.internet import reactor
"""
add leave
add points
add rules section
pick topic
pick topic and phrase
add topic
add phrase
"""

class HangmanBot(Bot):

    def __init__(self):
        self.wait = False
        self.players = []
        self.in_game = False
        self.category = ""
        self.panels = []
        self.phrase = []
        self.answer = ""
        self.used_letters = [""]
        self.turns = False
        self.current_turn = ""
        self.joined_players = set()
        self.current_call_id = None
        with open("hm_phrase_dict.json") as phrase_dict:
            self.phrases = yaml.safe_load(phrase_dict)
        with open("hm_resp_dict.json") as resp_dict:
            self.responses = yaml.safe_load(resp_dict)

    def add_player(self, prefix):
        if prefix not in self.joined_players and (self.wait or self.in_game):
            self.players.append(prefix)
            self.joined_players.add(prefix)
            self.respond("join", prefix)
    
    def command(self, prefix, msg):
        if "help" in msg:
            self.help_info(prefix)
        elif "normal play" in msg and not self.in_game:
            self.start_game(prefix)
        elif "turn play" in msg and not self.in_game:
            self.wait = True
            reactor.callLater(30, self.start_turn_game)
            self.respond("join_now")
            self.add_player(prefix)
        elif "play" in msg and self.in_game:
            self.respond(prefix, "in_game")
        elif "score" in msg or "standings" in msg and self.in_game:
            self.show_standings(prefix)
        else:
            return

    def help_info(self, prefix):
        if prefix:
            prefix += ", "
        self.say(self.factory.channel, "%s %s" % (prefix, self.responses.get("help")))

    def start_game(self, prefix=""):
        self.in_game = True
        category, phrase_list = random.choice(self.phrases.items())
        self.category = category
        self.answer = random.choice(phrase_list)
        self.panels = []
        self.phrase = list(self.answer)
        for index in range(len(self.phrase)):
            if self.phrase[index].isalpha():
                self.panels.append("_")
            elif self.phrase[index] == " ":
                self.panels.append("    ")
            else:
                self.panels.append(self.phrase[index])
        self.respond("start", prefix)
        self.used_letters = [""]
        self.show_standings()

    def start_turn_game(self):
        self.wait = False
        self.turns = True
        self.current_turn = self.players[0]
        self.start_game()
        self.current_call_id = reactor.callLater(15, self.change_turn)

    def change_turn(self):
        new_index = (self.players.index(self.current_turn) + 1) % len(self.players)
        print new_index
        self.current_turn = self.players[new_index]
        if not self.current_call_id.active():
            self.show_standings()
            self.current_call_id = reactor.callLater(15, self.change_turn)
        else:
            self.current_call_id.reset(15)

    def show_standings(self, prefix=""):
        if prefix:
            prefix += ", "
        self.say(self.factory.channel, "%s Category,   %s" % (prefix, self.category.upper()))
        self.say(self.factory.channel, "%s Phrase,   %s" % (prefix, " ".join(self.panels)))
        self.say(self.factory.channel, "%s Used Letters,   %s" % (prefix, " ".join(self.used_letters)))
        if self.turns:
            self.say(self.factory.channel, "%s Current Turn,   %s" % (prefix, self.current_turn))

    def respond(self, resp_type, prefix=""):
        if prefix:
            prefix += ", "
        self.say(self.factory.channel, "%s %s" % (prefix, random.choice(self.responses.get(resp_type))))

    def guess(self, prefix, msg, answer):
        if answer:
            if msg.lower() == self.answer.lower():
                self.respond("win", prefix)
                self.in_game = False
                self.turns = False
                self.current_call_id.cancel()
                self.players = []
                self.joined_players = set()
            else:
                print msg
                print self.answer
                self.respond("wrong", prefix)
                self.show_standings()
        elif self.turns:
            if prefix == self.current_turn:
                self.change_turn()
                if len(msg) == 1:
                    self.update_standings(msg.lower(), prefix)
                else:
                    self.respond("not_letter", prefix)
        else:
            if len(msg) == 1:
                self.update_standings(msg.lower(), prefix)
            else:
                self.respond("not_letter", prefix)

    def update_standings(self, letter, prefix):
        if letter in self.answer.lower() and letter not in self.used_letters:
            self.respond("correct", prefix)
            self.add_letter(letter)
            self.show_standings()
        elif letter in self.used_letters:
            self.respond("used", prefix)
            self.show_standings()
        else:
            self.add_used(letter)
            self.respond("incorrect", prefix)
            self.show_standings()

    def add_letter(self, letter):
        for index in range(len(self.phrase)):
            if letter == self.phrase[index].lower():
                self.panels[index] = self.phrase[index]
        self.add_used(letter)

    def add_used(self, letter):
        self.used_letters.append(letter)
        self.used_letters.sort()

    def privmsg(self, user, channel, msg):
        if not user:
            return
        com_regex = re.compile(self.first_name + "[ _]" + self.last_name + "[:,]* ?", re.I)
        guess_regex = re.compile("(guess|answer)" + "([ :,-_]*)" + "([ '&:,\w]*)", re.I)
        join_regex = re.compile("(join)")
        guess = False
        answer = False
        prefix = "%s" % (user.split("!", 1)[0], )
        if com_regex.search(msg) and not self.wait:
            msg = com_regex.sub("", msg)
        elif guess_regex.search(msg) and not self.wait:
            guess = True
            answer = False
            if guess_regex.search(msg).group(1).lower() == "answer":
                answer = True
            msg = guess_regex.search(msg).group(3)
        elif join_regex.search(msg):
            self.add_player(prefix)
        else:
            prefix = ""
        if prefix:
            if guess and self.in_game:
                self.guess(prefix, msg, answer)
            else:
                self.command(prefix, msg)


class HangmanBotFactory(BotFactory):
    protocol = HangmanBot

    def __init__(self, channel, nickname):
        BotFactory.__init__(self, channel, nickname)

if __name__ == "__main__":
    host = "coop.test.adtran.com"
    port = 6667
    chan = "THE_MAGIC_CONCH_ROOM"  # "THE_MAGIC_CONCH_ROOM" "test"
    reactor.connectTCP(host, port, HangmanBotFactory("#" + chan, "Hm"))
    reactor.run()
