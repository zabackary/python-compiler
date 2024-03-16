from main import main

__COMPILED__ = False
if not __COMPILED__:
    from other_mod import hello_world
    print(hello_world("not compiled!"))
else:
    print("is compiled, no import!")

print("1+1 is {}".format(1+1-3))
print("True and True and True is {}".format(True and True or False))


for msg in main():
    print(msg)
