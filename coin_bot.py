import random
import re

# import argparse

from twisted_bot import Bot, BotFactory
from twisted.internet import reactor


class CoinBot(Bot):

    def __init__(self):
        self.command_words = ["flip", "heads or tails", "heads", "tails", "help"]
        self.sides = ["Heads!", "Tails"]

    def command(self, prefix, msg):
        flip = False
        for com in self.command_words:
            if com in msg.lower():
                flip = True
        if flip:
            self.coin_toss(prefix)

    def coin_toss(self, prefix):
        self.describe(self.factory.channel, "is flipping the coin.")
        self.say(self.factory.channel, prefix + "It was, " + self.sides[random.randint(0, 1)])
    
    def privmsg(self, user, channel, msg):
        if not user:
            return
        com_regex = re.compile(self.first_name + "[ _]" + self.last_name + "[:,]* ?", re.I)
        if com_regex.search(msg):
            msg = com_regex.sub("", msg)
            prefix = "%s: " % (user.split("!", 1)[0], )
        else:
            prefix = ""
        if prefix:
            self.command(prefix, msg)


class CoinBotFactory(BotFactory):
    protocol = CoinBot

    def __init__(self, channel, nickname):
        BotFactory.__init__(self, channel, nickname)


if __name__ == "__main__":
    host = "coop.test.adtran.com"
    port = 6667
    chan = "THE_MAGIC_CONCH_ROOM" # "THE_MAGIC_CONCH_ROOM" "test" 
    reactor.connectTCP(host, port, CoinBotFactory("#" + chan, "Coin"))
    reactor.run()
