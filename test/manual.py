from starshift import *



def run():
    class A(Shift):
        ref: "B"

    class B(Shift):
        val: int

    test = A(ref=B(val=10))

if __name__ == '__main__':
    run()