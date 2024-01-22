import math

import regular_module


def main():
    msgs: list[str] = []
    msgs.append("Hello, world!")
    msgs.append("From regular_module.regular_function: %s" %
                regular_module.regular_function())
    my_regular_class = regular_module.RegularClass()
    msgs.append("From regular_module.RegularClass.regular_method: %s" %
                my_regular_class.regular_method())
    msgs.append("From builtin math, sin of 1 radian: %s" % math.sin(1))
    return msgs


if __name__ == "__main__":
    for msg in main():
        print(msg)
