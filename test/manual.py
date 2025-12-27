from starshift import *



InvalidType = object()



def run():
    class Test(Shift):
        val: int

    test = Test(val=42)
    print(test.val)
    test = Test(val=81)
    print(test.val)

if __name__ == '__main__':
    run()