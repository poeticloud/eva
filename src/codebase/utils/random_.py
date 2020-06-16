import random
import string


def randomstring(length, scope=string.ascii_letters):
    return "".join(random.choice(scope) for i in range(length))
