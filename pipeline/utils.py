SUBDOMAIN_SPAM = [
    ".hwl.li",
    ".skorpil.cz",
    ".cispa.saarland",
    ".glaceon.social",
    ".egirls.gay",
    ".monads.online",
    ".pixie.town",
    ".websec.saarland",
    ".gab.best",
]

def is_spam(instance):
    if instance is None:
        return False
    for spam in SUBDOMAIN_SPAM:
        if spam in instance:
            return True
    return False
