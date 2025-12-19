from starshift import *



def run():
    class Test(Shift):
        name: str
        age: int
        height: float = 3.14
        relation = {"parent": "someone"}

        @shift_validator('age', 'height')
        def validate_age(self, val):
            return val > 0

    test = Test(name="John", age=25, height=-1.8)

if __name__ == '__main__':
    run()