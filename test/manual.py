from starshift import *



def run():
    class Test(Shift):
        name: str
        age: int
        height: float = 3.14
        relation = {"parent": "someone"}

    test = Test(name="John", age=25, height=1.8)

if __name__ == '__main__':
    run()