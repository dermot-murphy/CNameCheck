from dataclasses import dataclass, field


@dataclass
class TestStep:
    number: int
    action: str
    expected: str


@dataclass
class TestCase:
    id: str
    title: str
    objective: str
    requirements: list
    priority: str
    preconditions: str
    postconditions: str
    parameters: dict  # test-level overrides
    steps: list


@dataclass
class TestSuite:
    title: str
    config: dict  # suite-level parameters (Parameter → Value)
    test_cases: list
