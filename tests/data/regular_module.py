import other_mod


def regular_function():
    return "returned value from regular_function"


class RegularClass:
    def __init__(self):
        print("Initialized regular_module.RegularClass!", other_mod.hello_world())

    def regular_method(self):
        return "returned value from RegularClass.regular_method"
