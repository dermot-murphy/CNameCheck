"""Generate Robot Framework .robot files from TestSuite objects."""

import re
from .models import TestSuite, TestCase, TestStep

_INDENT = '    '


def _to_kw(name: str) -> str:
    """Convert snake_case or lowercase identifiers to Title Case keyword names.

    Examples:
        supply_voltage  → Supply Voltage
        hardware_reset  → Hardware Reset
        supply_on       → Supply On
    """
    return name.replace('_', ' ').title()


def _rf_val(value: str) -> str:
    """Convert {PARAM} references to Robot Framework ${PARAM} variable syntax."""
    return re.sub(r'\{(\w+)\}', r'${\1}', value.strip())


# Action patterns: list of (compiled_regex, generator_callable)
# The generator receives the re.Match object and returns an RF keyword line.
_ACTION_PATTERNS = [
    # SET <subject> TO <value>
    (re.compile(r'^SET\s+(\S+)\s+TO\s+(.+)$', re.I),
     lambda m: f'Set {_to_kw(m.group(1))}    {_rf_val(m.group(2))}'),

    # READ <subject> AT <address>
    (re.compile(r'^READ\s+(\S+)\s+AT\s+(.+)$', re.I),
     lambda m: f'Read {_to_kw(m.group(1))}    {_rf_val(m.group(2))}'),

    # READ <subject>
    (re.compile(r'^READ\s+(\S+)$', re.I),
     lambda m: f'Read {_to_kw(m.group(1))}'),

    # TRIGGER <event>
    (re.compile(r'^TRIGGER\s+(.+)$', re.I),
     lambda m: f'Trigger {_to_kw(m.group(1))}'),

    # WAIT FOR <duration>
    (re.compile(r'^WAIT\s+FOR\s+(.+)$', re.I),
     lambda m: f'Sleep    {_rf_val(m.group(1))}'),

    # SEND <message> TO <target>
    (re.compile(r'^SEND\s+(\S+)\s+TO\s+(\S+)$', re.I),
     lambda m: f'Send {_to_kw(m.group(1))} To {_to_kw(m.group(2))}'),

    # PRESS <button>
    (re.compile(r'^PRESS\s+(.+)$', re.I),
     lambda m: f'Press {_to_kw(m.group(1))}'),

    # CALL <function>
    (re.compile(r'^CALL\s+(.+)$', re.I),
     lambda m: f'{_to_kw(m.group(1))}'),
]

# Expected result patterns: list of (compiled_regex, generator_callable)
# More specific patterns (IS WITHIN) must appear before general ones (IS).
_EXPECTED_PATTERNS = [
    # <subject> IS WITHIN <tolerance> OF <target>
    (re.compile(r'^(\S+)\s+IS\s+WITHIN\s+(\S+)\s+OF\s+(.+)$', re.I),
     lambda m: (f'{_to_kw(m.group(1))} Should Be Within Tolerance'
                f'    {_rf_val(m.group(3))}    {_rf_val(m.group(2))}')),

    # <subject> EQUALS <value>
    (re.compile(r'^(\S+)\s+EQUALS\s+(.+)$', re.I),
     lambda m: f'{_to_kw(m.group(1))} Should Equal    {_rf_val(m.group(2))}'),

    # <subject> IS TRUE
    (re.compile(r'^(\S+)\s+IS\s+TRUE$', re.I),
     lambda m: f'{_to_kw(m.group(1))} Should Be True'),

    # <subject> IS FALSE
    (re.compile(r'^(\S+)\s+IS\s+FALSE$', re.I),
     lambda m: f'{_to_kw(m.group(1))} Should Be False'),

    # <subject> CONTAINS <value>
    (re.compile(r'^(\S+)\s+CONTAINS\s+(.+)$', re.I),
     lambda m: f'{_to_kw(m.group(1))} Should Contain    {_rf_val(m.group(2))}'),

    # <subject> CHANGES TO <value>
    (re.compile(r'^(\S+)\s+CHANGES\s+TO\s+(.+)$', re.I),
     lambda m: f'{_to_kw(m.group(1))} Should Change To    {_rf_val(m.group(2))}'),

    # <subject> IS <state>   (must be last: catches any remaining IS pattern)
    (re.compile(r'^(\S+)\s+IS\s+(.+)$', re.I),
     lambda m: f'{_to_kw(m.group(1))} Should Be    {m.group(2)}'),
]


def _convert_action(action: str) -> str:
    for pattern, generator in _ACTION_PATTERNS:
        m = pattern.match(action)
        if m:
            return generator(m)
    # Fallback: emit as a bare keyword (title-cased)
    return _to_kw(action)


def _convert_expected(expected: str) -> str:
    if not expected:
        return ''
    for pattern, generator in _EXPECTED_PATTERNS:
        m = pattern.match(expected)
        if m:
            return generator(m)
    # Fallback: emit as a comment so the engineer can fill it in
    return f'# TODO: verify    {expected}'


def _render_step(step: TestStep) -> list:
    """Return a list of indented RF lines for one test step."""
    lines = [f'{_INDENT}# Step {step.number}']
    action_line = _convert_action(step.action)
    if action_line:
        lines.append(f'{_INDENT}{action_line}')
    expected_line = _convert_expected(step.expected)
    if expected_line:
        lines.append(f'{_INDENT}{expected_line}')
    return lines


def _render_test_case(tc: TestCase) -> list:
    """Return RF lines for one test case block."""
    lines = []

    # Test case name
    lines.append(f'{tc.id} {tc.title}')

    # [Documentation]
    doc = tc.objective.replace('    ', ' ')
    lines.append(f'{_INDENT}[Documentation]    {doc}')

    # [Tags] — requirements + priority
    tags = tc.requirements[:]
    if tc.priority:
        tags.append(f'priority-{tc.priority.lower()}')
    if tags:
        lines.append(f'{_INDENT}[Tags]    ' + '    '.join(tags))

    # [Setup] / [Teardown]
    if tc.preconditions:
        lines.append(f'{_INDENT}[Setup]    Test Precondition    {tc.preconditions}')
    if tc.postconditions:
        lines.append(f'{_INDENT}[Teardown]    Test Postcondition    {tc.postconditions}')

    # Test-level parameter overrides (Set Test Variable calls at start of body)
    if tc.parameters:
        lines.append(f'{_INDENT}# Test-level parameter overrides')
        for key, value in tc.parameters.items():
            lines.append(f'{_INDENT}Set Test Variable    ${{{key}}}    {value}')

    # Steps
    for step in tc.steps:
        lines.extend(_render_step(step))

    lines.append('')
    return lines


def generate(suite: TestSuite) -> str:
    """Render a TestSuite as a Robot Framework .robot file string."""
    out = []

    # *** Settings ***
    out.append('*** Settings ***')
    out.append(f'Documentation    {suite.title}')
    out.append('Library    Collections')
    out.append('')

    # *** Variables ***
    if suite.config:
        out.append('*** Variables ***')
        for param, value in suite.config.items():
            out.append(f'${{{param}}}    {value}')
        out.append('')

    # *** Test Cases ***
    out.append('*** Test Cases ***')
    for tc in suite.test_cases:
        out.extend(_render_test_case(tc))

    return '\n'.join(out)
