from starshift import *



def run():
    class Test(Shift):
        val: int = MISSING

    test = Test()
    assert test.val == MISSING
    test = Test(**{})
    assert test.val == MISSING

if __name__ == '__main__':
    run()