from supybot import conf


def configure(advanced):
    conf.registerPlugin("Soccer", True)


Soccer = conf.registerPlugin("Soccer")
