from starshift import *



def run():
    class A(Shift):
        val: int

    class B(Shift):
        nest: A

    test = B(nest=A(val=1))
    print(repr(test))
    print(test.serialize())

if __name__ == '__main__':
    run()