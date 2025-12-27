from starshift import *



def run():
    class Test(Shift):
        val: None

    test = Test(val=None)
    assert test.val is None
    test = Test(**{"val": None})
    assert test.val is None

if __name__ == '__main__':
    run()