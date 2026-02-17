import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from datetime import datetime, timedelta



InvalidType = object()

@pytest.fixture(autouse=True)
def reset_starshift():
    reset_starshift_globals()
    yield
    reset_starshift_globals()



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
    def _validate_non_empty_lists_and_strs(self, field: ShiftFieldInfo, info: ShiftInfo) -> bool:
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
    def _validate_non_empty_lists_and_strs(self, field: ShiftFieldInfo, info: ShiftInfo) -> bool:
        if len(field.val) == 0:
            raise ShiftError('Group', f"{field.name} cannot be empty")
        return True

class Employee(Shift):
    first_name: str
    last_name: str
    title: Literal['Junior Developer', 'Senior Developer', 'Manager', 'CEO']



    @shift_validator('first_name', 'last_name')
    def _validate_non_empty_name(self, field: ShiftFieldInfo, info: ShiftInfo) -> bool:
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



valid_company_1 = {
    'name': 'Recursion Ltd.',
    'title': 'We put the "base case" in "database"',
    'employees': [
        {
            'first_name': 'Alan',
            'last_name': 'Turing',
            'title': 'Senior Developer'
        },
        {
            'first_name': 'Grace',
            'last_name': 'Hopper',
            'title': 'CEO'
        }
    ],
    'tasks': [
        {
            'title': 'Fix the off-by-one error',
            'description': 'You know, the usual fence post problem',
            'status': 'In Progress',
            'due_date': datetime.now() + timedelta(days=7),
            'sub_tasks': [],
            'groups': [],
            'assignees': [
                {
                    'first_name': 'Alan',
                    'last_name': 'Turing',
                    'title': 'Senior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Alan',
                    'last_name': 'Turing',
                    'title': 'Senior Developer'
                }
            ]
        }
    ],
    'task_groups': [
        {
            'title': 'Sprint 404',
            'description': 'Sprint not found',
            'tasks': [],
            'members': [
                {
                    'first_name': 'Alan',
                    'last_name': 'Turing',
                    'title': 'Senior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Grace',
                    'last_name': 'Hopper',
                    'title': 'CEO'
                }
            ]
        }
    ],
    'admins': [
        {
            'first_name': 'Grace',
            'last_name': 'Hopper',
            'title': 'CEO'
        }
    ]
}

valid_company_2 = {
    'name': 'Quantum Superposition Dynamics',
    'title': 'Our bugs exist in multiple states until observed',
    'employees': [
        {
            'first_name': 'Linus',
            'last_name': 'Torvalds',
            'title': 'Senior Developer'
        },
        {
            'first_name': 'Margaret',
            'last_name': 'Hamilton',
            'title': 'Manager'
        },
        {
            'first_name': 'Dennis',
            'last_name': 'Ritchie',
            'title': 'Senior Developer'
        },
        {
            'first_name': 'Ada',
            'last_name': 'Lovelace',
            'title': 'CEO'
        },
        {
            'first_name': 'Ken',
            'last_name': 'Thompson',
            'title': 'Junior Developer'
        }
    ],
    'tasks': [
        {
            'title': 'Implement distributed monolith architecture',
            'description': 'Take all the disadvantages of both approaches',
            'status': 'Stuck',
            'due_date': datetime.now() + timedelta(days=30),
            'sub_tasks': [
                {
                    'title': 'Write documentation',
                    'description': 'Unlike our actual code',
                    'status': 'Not Started',
                    'due_date': datetime.now() + timedelta(days=14),
                    'sub_tasks': [],
                    'groups': [],
                    'assignees': [
                        {
                            'first_name': 'Ken',
                            'last_name': 'Thompson',
                            'title': 'Junior Developer'
                        }
                    ],
                    'admins': [
                        {
                            'first_name': 'Ken',
                            'last_name': 'Thompson',
                            'title': 'Junior Developer'
                        }
                    ]
                },
                {
                    'title': 'Refactor legacy code',
                    'description': 'Written last Tuesday',
                    'status': 'In Progress',
                    'due_date': datetime.now() + timedelta(days=21),
                    'sub_tasks': [],
                    'groups': [],
                    'assignees': [
                        {
                            'first_name': 'Linus',
                            'last_name': 'Torvalds',
                            'title': 'Senior Developer'
                        },
                        {
                            'first_name': 'Dennis',
                            'last_name': 'Ritchie',
                            'title': 'Senior Developer'
                        }
                    ],
                    'admins': [
                        {
                            'first_name': 'Linus',
                            'last_name': 'Torvalds',
                            'title': 'Senior Developer'
                        }
                    ]
                }
            ],
            'groups': [],
            'assignees': [
                {
                    'first_name': 'Linus',
                    'last_name': 'Torvalds',
                    'title': 'Senior Developer'
                },
                {
                    'first_name': 'Dennis',
                    'last_name': 'Ritchie',
                    'title': 'Senior Developer'
                },
                {
                    'first_name': 'Margaret',
                    'last_name': 'Hamilton',
                    'title': 'Manager'
                }
            ],
            'admins': [
                {
                    'first_name': 'Margaret',
                    'last_name': 'Hamilton',
                    'title': 'Manager'
                }
            ]
        },
        {
            'title': 'Increase test coverage to 100%',
            'description': 'Excluding the parts that might actually break',
            'status': 'Done',
            'due_date': datetime.now() + timedelta(days=60),
            'sub_tasks': [],
            'groups': [],
            'assignees': [
                {
                    'first_name': 'Ken',
                    'last_name': 'Thompson',
                    'title': 'Junior Developer'
                },
                {
                    'first_name': 'Dennis',
                    'last_name': 'Ritchie',
                    'title': 'Senior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Dennis',
                    'last_name': 'Ritchie',
                    'title': 'Senior Developer'
                }
            ]
        }
    ],
    'task_groups': [
        {
            'title': 'Q4 Deliverables',
            'description': 'Time to panic',
            'tasks': [
                {
                    'title': 'Increase test coverage to 100%',
                    'description': 'Excluding the parts that might actually break',
                    'status': 'Done',
                    'due_date': datetime.now() + timedelta(days=60),
                    'sub_tasks': [],
                    'groups': [],
                    'assignees': [
                        {
                            'first_name': 'Ken',
                            'last_name': 'Thompson',
                            'title': 'Junior Developer'
                        },
                        {
                            'first_name': 'Dennis',
                            'last_name': 'Ritchie',
                            'title': 'Senior Developer'
                        }
                    ],
                    'admins': [
                        {
                            'first_name': 'Dennis',
                            'last_name': 'Ritchie',
                            'title': 'Senior Developer'
                        }
                    ]
                }
            ],
            'members': [
                {
                    'first_name': 'Ken',
                    'last_name': 'Thompson',
                    'title': 'Junior Developer'
                },
                {
                    'first_name': 'Dennis',
                    'last_name': 'Ritchie',
                    'title': 'Senior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Margaret',
                    'last_name': 'Hamilton',
                    'title': 'Manager'
                }
            ]
        },
        {
            'title': 'Technical Debt Sprint',
            'description': 'Compounding interest since 2019',
            'tasks': [],
            'members': [
                {
                    'first_name': 'Linus',
                    'last_name': 'Torvalds',
                    'title': 'Senior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Ada',
                    'last_name': 'Lovelace',
                    'title': 'CEO'
                }
            ]
        }
    ],
    'admins': [
        {
            'first_name': 'Ada',
            'last_name': 'Lovelace',
            'title': 'CEO'
        },
        {
            'first_name': 'Margaret',
            'last_name': 'Hamilton',
            'title': 'Manager'
        }
    ]
}

valid_company_3 = {
    'name': 'Blockchain AI Cloud Solutions Inc.',
    'title': 'We use all the buzzwords',
    'employees': [
        {
            'first_name': 'Donald',
            'last_name': 'Knuth',
            'title': 'Senior Developer'
        },
        {
            'first_name': 'Barbara',
            'last_name': 'Liskov',
            'title': 'Senior Developer'
        },
        {
            'first_name': 'Edsger',
            'last_name': 'Dijkstra',
            'title': 'Manager'
        },
        {
            'first_name': 'John',
            'last_name': 'Carmack',
            'title': 'Senior Developer'
        },
        {
            'first_name': 'Tim',
            'last_name': 'Berners-Lee',
            'title': 'CEO'
        },
        {
            'first_name': 'Guido',
            'last_name': 'van Rossum',
            'title': 'Junior Developer'
        },
        {
            'first_name': 'Bjarne',
            'last_name': 'Stroustrup',
            'title': 'Junior Developer'
        }
    ],
    'tasks': [
        {
            'title': 'Migrate to microservices',
            'description': 'Our 3 users demand scalability',
            'status': 'In Progress',
            'due_date': datetime.now() + timedelta(days=90),
            'sub_tasks': [
                {
                    'title': 'Break monolith into services',
                    'description': 'Create distributed monolith',
                    'status': 'In Progress',
                    'due_date': datetime.now() + timedelta(days=45),
                    'sub_tasks': [
                        {
                            'title': 'Design service boundaries',
                            'description': 'Draw lines on whiteboard',
                            'status': 'Done',
                            'due_date': datetime.now() + timedelta(days=15),
                            'sub_tasks': [],
                            'groups': [],
                            'assignees': [
                                {
                                    'first_name': 'Edsger',
                                    'last_name': 'Dijkstra',
                                    'title': 'Manager'
                                }
                            ],
                            'admins': [
                                {
                                    'first_name': 'Edsger',
                                    'last_name': 'Dijkstra',
                                    'title': 'Manager'
                                }
                            ]
                        },
                        {
                            'title': 'Implement service mesh',
                            'description': 'Add complexity to justify our salaries',
                            'status': 'Not Started',
                            'due_date': datetime.now() + timedelta(days=30),
                            'sub_tasks': [],
                            'groups': [],
                            'assignees': [
                                {
                                    'first_name': 'John',
                                    'last_name': 'Carmack',
                                    'title': 'Senior Developer'
                                },
                                {
                                    'first_name': 'Barbara',
                                    'last_name': 'Liskov',
                                    'title': 'Senior Developer'
                                }
                            ],
                            'admins': [
                                {
                                    'first_name': 'Barbara',
                                    'last_name': 'Liskov',
                                    'title': 'Senior Developer'
                                }
                            ]
                        }
                    ],
                    'groups': [],
                    'assignees': [
                        {
                            'first_name': 'Barbara',
                            'last_name': 'Liskov',
                            'title': 'Senior Developer'
                        },
                        {
                            'first_name': 'John',
                            'last_name': 'Carmack',
                            'title': 'Senior Developer'
                        },
                        {
                            'first_name': 'Edsger',
                            'last_name': 'Dijkstra',
                            'title': 'Manager'
                        }
                    ],
                    'admins': [
                        {
                            'first_name': 'Edsger',
                            'last_name': 'Dijkstra',
                            'title': 'Manager'
                        }
                    ]
                },
                {
                    'title': 'Setup Kubernetes cluster',
                    'description': 'Because Docker Compose was too simple',
                    'status': 'Stuck',
                    'due_date': datetime.now() + timedelta(days=60),
                    'sub_tasks': [],
                    'groups': [],
                    'assignees': [
                        {
                            'first_name': 'Guido',
                            'last_name': 'van Rossum',
                            'title': 'Junior Developer'
                        },
                        {
                            'first_name': 'Donald',
                            'last_name': 'Knuth',
                            'title': 'Senior Developer'
                        }
                    ],
                    'admins': [
                        {
                            'first_name': 'Donald',
                            'last_name': 'Knuth',
                            'title': 'Senior Developer'
                        }
                    ]
                }
            ],
            'groups': [],
            'assignees': [
                {
                    'first_name': 'Donald',
                    'last_name': 'Knuth',
                    'title': 'Senior Developer'
                },
                {
                    'first_name': 'Barbara',
                    'last_name': 'Liskov',
                    'title': 'Senior Developer'
                },
                {
                    'first_name': 'Edsger',
                    'last_name': 'Dijkstra',
                    'title': 'Manager'
                },
                {
                    'first_name': 'John',
                    'last_name': 'Carmack',
                    'title': 'Senior Developer'
                },
                {
                    'first_name': 'Guido',
                    'last_name': 'van Rossum',
                    'title': 'Junior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Edsger',
                    'last_name': 'Dijkstra',
                    'title': 'Manager'
                },
                {
                    'first_name': 'Donald',
                    'last_name': 'Knuth',
                    'title': 'Senior Developer'
                }
            ]
        },
        {
            'title': 'Optimize premature optimization',
            'description': 'The root of all evil needs refactoring',
            'status': 'Not Started',
            'due_date': datetime.now() + timedelta(days=120),
            'sub_tasks': [],
            'groups': [],
            'assignees': [
                {
                    'first_name': 'Bjarne',
                    'last_name': 'Stroustrup',
                    'title': 'Junior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Bjarne',
                    'last_name': 'Stroustrup',
                    'title': 'Junior Developer'
                }
            ]
        }
    ],
    'task_groups': [
        {
            'title': 'Infrastructure Modernization',
            'description': 'Replace working system with broken one',
            'tasks': [
                {
                    'title': 'Migrate to microservices',
                    'description': 'Our 3 users demand scalability',
                    'status': 'In Progress',
                    'due_date': datetime.now() + timedelta(days=90),
                    'sub_tasks': [],
                    'groups': [],
                    'assignees': [
                        {
                            'first_name': 'Donald',
                            'last_name': 'Knuth',
                            'title': 'Senior Developer'
                        }
                    ],
                    'admins': [
                        {
                            'first_name': 'Donald',
                            'last_name': 'Knuth',
                            'title': 'Senior Developer'
                        }
                    ]
                }
            ],
            'members': [
                {
                    'first_name': 'Donald',
                    'last_name': 'Knuth',
                    'title': 'Senior Developer'
                },
                {
                    'first_name': 'Barbara',
                    'last_name': 'Liskov',
                    'title': 'Senior Developer'
                },
                {
                    'first_name': 'Guido',
                    'last_name': 'van Rossum',
                    'title': 'Junior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Edsger',
                    'last_name': 'Dijkstra',
                    'title': 'Manager'
                }
            ]
        },
        {
            'title': 'Performance Optimization',
            'description': 'Making things slower, but distributed',
            'tasks': [],
            'members': [
                {
                    'first_name': 'John',
                    'last_name': 'Carmack',
                    'title': 'Senior Developer'
                },
                {
                    'first_name': 'Bjarne',
                    'last_name': 'Stroustrup',
                    'title': 'Junior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': 'Tim',
                    'last_name': 'Berners-Lee',
                    'title': 'CEO'
                }
            ]
        }
    ],
    'admins': [
        {
            'first_name': 'Tim',
            'last_name': 'Berners-Lee',
            'title': 'CEO'
        },
        {
            'first_name': 'Edsger',
            'last_name': 'Dijkstra',
            'title': 'Manager'
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
        {
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
# Should fail: no assignees

invalid_company_2 = {
    'name': 'Validation Nightmare LLC',
    'title': '',  # Empty title - should fail
    'employees': [
        {
            'first_name': 'Richard',
            'last_name': 'Stallman',
            'title': 'Senior Developer'
        },
        {
            'first_name': '',  # Empty first name - should fail
            'last_name': 'Torvalds',
            'title': 'Junior Developer'
        }
    ],
    'tasks': [
        {
            'title': '',  # Empty title - should fail
            'description': 'Fix all the things',
            'status': 'Not Started',
            'due_date': datetime.now() - timedelta(days=10),  # Past due date - should fail
            'sub_tasks': [],
            'groups': [],
            'assignees': [
                {
                    'first_name': 'Richard',
                    'last_name': 'Stallman',
                    'title': 'Senior Developer'
                }
            ],
            'admins': [
                {
                    'first_name': '',
                    'last_name': 'Torvalds',
                    'title': 'Junior Developer'
                }  # Admin not in assignees - should fail
            ]
        },
        {
            'title': 'Procrastinate effectively',
            'description': "I'll add this later",
            'status': 'Done',
            'due_date': datetime.now() + timedelta(days=5),
            'sub_tasks': [],
            'groups': [],
            'assignees': [],  # Empty assignees list - should fail
            'admins': []
        }
    ],
    'task_groups': [
        {
            'title': 'The Void',
            'description': '',  # Empty description - should fail
            'tasks': [],
            'members': [],  # Empty members - should fail
            'admins': []  # Empty admins - should fail
        }
    ],
    'admins': [
        {
            'first_name': 'Richard',
            'last_name': 'Stallman',
            'title': 'Senior Developer'
        }
    ]
}
# Should fail multiple validations:
# - Empty title (Company)
# - Empty first_name (Employee)
# - Empty title (Task)
# - Past due_date (Task)
# - Admin not in assignees (Task)
# - Empty assignees (Task)
# - Empty description (Group)
# - Empty members (Group)
# - Empty admins (Group)



@pytest.mark.application
def test_valid_company_datasets():
    def date_type_validator(instance: Any, field: ShiftFieldInfo, info: ShiftInfo) -> bool:
        return isinstance(field.val, datetime)
    date_shift_type = ShiftType(
        validator=date_type_validator,
    )
    register_shift_type(datetime, date_shift_type)

    _ = Company(**valid_company_1)
    _ = Company(**valid_company_2)
    _ = Company(**valid_company_3)

@pytest.mark.application
def test_invalid_company_datasets():
    def date_type_validator(instance: Any, field: ShiftFieldInfo, info: ShiftInfo) -> bool:
        return isinstance(field.val, datetime)
    date_shift_type = ShiftType(
        validator=date_type_validator,
    )
    register_shift_type(datetime, date_shift_type)

    with pytest.raises(ShiftError):
        _ = Company(**invalid_company_1)
    with pytest.raises(ShiftError):
        _ = Company(**invalid_company_2)