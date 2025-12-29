import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from datetime import datetime, timedelta



InvalidType = object()


class Task(Shift):
    title: str
    description: str = ''
    status: Literal['Not Started', 'In Progress', 'Stuck', 'Done']
    due_date: datetime
    sub_tasks: list['Task']
    groups: list['Group']
    assignees: list['Employee']
    admins: list['Employee']



    @shift_validator('title', 'assignees', 'admins')
    def _validate_non_empty_lists_and_strs(self, field: ShiftField, info: ShiftInfo) -> bool:
        if len(field.val) == 0:
            raise ShiftError('Task', f"{field.name} cannot be empty")
        return True

    @shift_validator('due_date')
    def _validate_due_date(self, val: datetime) -> bool:
        if val <= datetime.now():
            raise ShiftError('Task', f"due date must be in the future")
        return True

    def _validate_all_admins_are_assignees(self):
        for admin in self.admins:
            if admin not in self.assignees:
                raise ShiftError('Task', f"All admins must be assignees")



    def __post_init__(self, info: ShiftInfo):
        self._validate_all_admins_are_assignees()

class Group(Shift):
    title: str
    description: str
    tasks: list[Task]
    members: list['Employee']
    admins: list['Employee']



    @shift_validator('title', 'description', 'members', 'admins')
    def _validate_non_empty_lists_and_strs(self, field: ShiftField, info: ShiftInfo) -> bool:
        if len(field.val) == 0:
            raise ShiftError('Group', f"{field.name} cannot be empty")
        return True

class Employee(Shift):
    first_name: str
    last_name: str
    title: Literal['Junior Developer', 'Senior Developer', 'Manager', 'CEO']



    @shift_validator('first_name', 'last_name')
    def _validate_non_empty_name(self, field: ShiftField, info: ShiftInfo) -> bool:
        if len(field.val) == 0:
            raise ShiftError('Task', f"{field.name} cannot be empty")
        return True

class Company(Shift):
    name: str
    title: str
    employees: list[Employee]
    tasks: list[Task]
    task_groups: list[Group]
    admins: list[Employee]

invalid_task_1 = {
    'title': 'Hire more devs',
    'description': 'We simply dont have enough',
    'status': 'In Progress',
    'due_date': datetime.now() + timedelta(days=7),
    'sub_tasks': [],
    'groups': [],
    'assignees': [

    ],
    'admins': [
        {
            'first_name': 'Alan',
            'last_name': 'Turing',
            'title': 'Senior Developer'
        }
    ]
}

invalid_company_1 = {
    'name': 'Infinite Loop Corp',
    'title': 'while(true) { hire(); }',
    'employees': [
        {
            'first_name': 'Douglas',
            'last_name': 'Hofstadter',
            'title': 'Senior Developer'
        }
    ],
    'tasks': [
        invalid_task_1,
    ],
    'task_groups': [
        {
            'title': 'Paradox Resolution',
            'description': 'This statement is false',
            'tasks': [],
            'members': [
                {
                    'first_name': 'Douglas',
                    'last_name': 'Hofstadter',
                    'title': 'Senior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Douglas',
                    'last_name': 'Hofstadter',
                    'title': 'Senior Developer'
                }
            ]
        }
    ],
    'admins': [
        {
            'first_name': 'Douglas',
            'last_name': 'Hofstadter',
            'title': 'Senior Developer'
        }
    ]
}


def run():
    def date_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
        return isinstance(field.val, datetime)
    date_shift_type = ShiftType(
        validator=date_type_validator,
    )
    register_shift_type(datetime, date_shift_type)

    try:
        _ = Task(**invalid_task_1)
        raise Exception
    except ShiftError as e:
        print(e)

    try:
        _ = Company(**invalid_company_1)
        raise Exception
    except ShiftError as e:
        print(e)


if __name__ == '__main__':
    run()