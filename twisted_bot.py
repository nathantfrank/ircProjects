from twisted.words.protocols import irc
from twisted.internet import protocol


class Bot(irc.IRCClient):

    def __init__(self):
        self.identity = "bot"

    @property
    def nickname(self):
        return self.factory.nickname

    @property
    def first_name(self):
        return self.factory.first_name

    @property
    def last_name(self):
        return self.factory.last_name

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s." % self.nickname

    def joined(self, channel):
        print "Joined %s." % channel

    def privmsg(self, user, channel, msg):
        print msg

class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def __init__(self, channel, nickname):
        self.channel = channel
        self.nickname = nickname + "_Bot"
        self.first_name = nickname 
        self.last_name = "Bot"

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)
