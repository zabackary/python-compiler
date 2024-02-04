__COMPILED__ = False
__TEST__ = "default value"
__FLAG__ = False

if __name__ == "__main__":
    print(__COMPILED__)
    if __FLAG__:
        print("flag!")
    print("__TEST__ is:", __TEST__)
