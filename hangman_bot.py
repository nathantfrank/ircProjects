import random
import re
# import argparse
# import json
import yaml

from twisted_bot import Bot, BotFactory
from twisted.internet import reactor
"""
saving scores and winners
pick topic
pick topic and phrase
add topic
add phrase
add set reveal play to go off at certain times
"""


class Player:
    def __init__(self, name):
        self.name = name
        self.points = 0

    def add_points(self, num):
        self.points += num

    def get_points(self):
        return self.points

    def get_name(self):
        return self.name


class Game:
    def __init__(self, game, word_bank):
        self.game = game
        self.word_bank = word_bank
        self.category = ""
        self.answer = ""
        self.phrase = []
        self.panels = []
        self.used_letters = [""]
        self.current_turn = ""
        self.players = []
        self.reveal_used = set()
        self.reveal_letters = ["r", "s", "t", "l", "n", "e"]
        self.setup()

    def setup(self):
        random.seed()
        category, phrase_list = random.choice(self.word_bank.items())
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

    def add_player_to_game(self, prefix):
        if not self.current_turn and not self.players:
            self.players.append(Player(prefix))
            self.current_turn = self.players[0]
            return True
        already_playing = False
        for player in self.players:
            if player.get_name() == prefix:
                already_playing = True
        if not already_playing:
            self.players.append(Player(prefix))
            return True
        else:
            return False

    def remove_player_from_game(self, prefix):
        for player in self.players:
            if player.get_name() == prefix:
                self.players.remove(player)
                return True
        return False

    def next_players_turn(self):
        new_index = (self.players.index(self.current_turn) + 1) % len(self.players)
        self.current_turn = self.players[new_index]

    def add_letter(self, letter, prefix):
        current_player = None
        if self.game == "turn":
            for player in self.players:
                if player.get_name() == prefix:
                    current_player = player
                    break
        for index in range(len(self.phrase)):
            if letter == self.phrase[index].lower():
                if self.game == "turn":
                    current_player.add_points(1)
                self.panels[index] = self.phrase[index]
        self.add_used(letter)

    def add_used(self, letter):
        self.used_letters.append(letter)
        self.used_letters.sort()

    def player_sort(self):
        index = 0
        sorting = True
        swapped = False
        while sorting:
            if index == len(self.players):
                if not swapped:
                    sorting = False
                else:
                    index = 0
                    swapped = False
            elif index + 1 < len(self.players):
                if self.players[index].get_points() < self.players[index + 1].get_points():
                    swap_player = self.players[index]
                    self.players[index] = self.players[index + 1]
                    self.players[index + 1] = swap_player
                    swapped = True
            index += 1

    def won(self, prefix):
        if self.game == "turn":
            for player in self.players:
                if player.get_name() == prefix:
                    player.add_points(5)
                    break
            self.player_sort()

    def reveal_next_letter(self):
        letter = random.choice(self.phrase).lower()
        while letter in self.reveal_used or letter == " ":
            letter = random.choice(self.phrase).lower()
        for index in range(len(self.phrase)):
            if letter == self.phrase[index].lower():
                self.panels[index] = self.phrase[index]
        self.reveal_used.add(letter)
        self.add_used(letter)

    def reveal_starting_letters(self):
        for letter in self.reveal_letters:
            for index in range(len(self.phrase)):
                if letter == self.phrase[index]:
                    self.panels[index] = self.phrase[index]
            self.reveal_used.add(letter)
            self.add_used(letter)

    def reveal_end(self):
        for char in self.panels:
            if "_" == char:
                return False
        return True

    def get_version(self):
        return self.game

    def get_current_turn(self):
        return self.current_turn

    def get_standings(self):
        return self.category.upper(), " ".join(self.panels), " ".join(self.used_letters)

    def get_used_letters(self):
        return self.used_letters

    def get_answer(self):
        return self.answer

    def get_players(self):
        return self.players


class HangmanBot(Bot):

    def __init__(self):
        self.wait = False
        self.in_game = False
        self.game = None
        self.call_id = None
        with open("hm_phrase_dict.json") as phrase_dict:
            self.phrases = yaml.safe_load(phrase_dict)
        with open("hm_resp_dict.json") as resp_dict:
            self.responses = yaml.safe_load(resp_dict)

    def add_player(self, prefix):
        if self.wait or self.in_game and self.game.get_version() == "turn":
            player_added = self.game.add_player_to_game(prefix)
            if player_added:
                self.respond("join", prefix)

    def remove_player(self, prefix):
        if self.wait or self.in_game:
            player_removed = self.game.remove_player_from_game(prefix)
            if player_removed:
                self.respond("leave", prefix)
                # check to see if it's his turn currently

    def command(self, prefix, msg):
        if "help" in msg:
            self.info(prefix, "help")
        elif "normal rules" in msg:
            self.info(prefix, "normal_rules")
        elif "turn rules" in msg:
            self.info(prefix, "turn_rules")
        elif "leave" in msg and self.in_game and self.turns:
            self.remove_player(prefix)
        elif "normal play" in msg and not self.in_game:
            self.make_game("normal", prefix)
        elif "turn play" in msg and not self.in_game:
            self.make_game("turn", prefix)
        elif "reveal play" in msg and not self.in_game:
            self.make_game("reveal", prefix)
        elif "play" in msg and self.in_game:
            self.respond(prefix, "in_game")
        else:
            return

    def info(self, prefix, info_type):
        for msg in self.responses.get(info_type):
            self.msg(prefix, msg)

    def make_game(self, version, prefix):
        self.game = Game(version, self.phrases)
        self.respond("start", prefix)
        if version == "normal":
            self.start_game()
        elif version == "turn":
            self.wait = True
            reactor.callLater(30, self.start_game)
            self.respond("join_now")
            self.add_player(prefix)
        elif version == "reveal":
            self.game.reveal_starting_letters()
            self.start_game()

    def start_game(self):
        self.in_game = True
        self.wait = False
        self.show_standings()
        if self.game.get_version() == "turn":
            self.call_id = reactor.callLater(15, self.next_turn)
        elif self.game.get_version() == "reveal":
            self.call_id = reactor.callLater(10, self.reveal_letter)

    def reveal_letter(self):
        self.game.reveal_next_letter()
        self.show_standings()
        if not self.game.reveal_end():
            self.call_id = reactor.callLater(10, self.reveal_letter)

    def next_turn(self):
        self.game.next_players_turn()
        if not self.call_id.active():
            self.show_standings()
            self.call_id = reactor.callLater(15, self.next_turn)
        else:
            self.call_id.reset(15)

    def show_standings(self):
        category, phrase, letters = self.game.get_standings()
        if self.game.get_version() == "turn":
            self.say(self.factory.channel,
                     "Category,  %s\nPhrase,  %s\nUsed Letters,  %s\nCurrent Turn,  %s" %
                     (category, phrase, letters, self.game.get_current_turn().get_name()))
        else:
            self.say(self.factory.channel,
                     "Category,  %s\nPhrase,  %s\nUsed Letters,  %s" %
                     (category, phrase, letters))

    def show_score(self):
        score_sheet = "Scores, "
        for player in self.game.get_players():
            score_sheet += "\n%s: %s" % (player.get_name(), player.get_points())
        self.say(self.factory.channel, score_sheet)

    def respond(self, resp_type, prefix=""):
        if prefix:
            prefix += ", "
        self.say(self.factory.channel, "%s %s" % (prefix, random.choice(self.responses.get(resp_type))))

    def guess(self, prefix, msg, answer):
        if answer:
            if msg == self.game.get_answer().lower():
                self.game.won(prefix)
                if self.game.get_version() == "normal" or self.game.get_version() == "reveal":
                    self.respond("win", prefix)
                elif self.game.get_version() == "turn":
                    self.respond("right", prefix)
                    self.show_score()
                self.in_game = False
                if self.game.get_version() != "normal":
                    if self.call_id.active():
                        self.call_id.cancel()
            else:
                print msg
                print self.game.get_answer()
                self.respond("wrong", prefix)
                reactor.callLater(3, self.show_standings)
        elif self.game.get_version() == "turn":
            if prefix == self.game.get_current_turn().get_name():
                self.next_turn()
                if len(msg) == 1:
                    self.update_standings(msg, prefix)
                else:
                    self.respond("not_letter", prefix)
        else:
            if len(msg) == 1:
                self.update_standings(msg, prefix)
            else:
                self.respond("not_letter", prefix)

    def update_standings(self, letter, prefix):
        if letter in self.game.get_answer().lower() and letter not in self.game.get_used_letters():
            self.respond("correct", prefix)
            self.game.add_letter(letter, prefix)
            reactor.callLater(3, self.show_standings)
        elif letter in self.game.get_used_letters():
            self.respond("used", prefix)
            reactor.callLater(3, self.show_standings)
        else:
            self.game.add_used(letter)
            self.respond("incorrect", prefix)
            reactor.callLater(3, self.show_standings)

    def privmsg(self, user, channel, msg):
        if not user:
            return
        com_regex = re.compile(self.first_name + "[ _]" + self.last_name + "[:,]* ?", re.I)
        guess_regex = re.compile("(guess|answer)" + "([ ]*)" + "([\w~@#$^*()_+=[\]{}|\\,.?: -]*)", re.I)
        join_regex = re.compile("(join)")
        guess = False
        answer = False
        prefix = "%s" % (user.split("!", 1)[0], )
        if com_regex.search(msg) and not self.wait:
            msg = com_regex.sub("", msg).lower()
        elif guess_regex.search(msg) and not self.wait:
            guess = True
            answer = False
            if guess_regex.search(msg).group(1).lower() == "answer":
                answer = True
            msg = guess_regex.search(msg).group(3).lower()
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
