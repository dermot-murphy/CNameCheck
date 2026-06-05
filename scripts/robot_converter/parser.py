"""Parse ASPICE-compliant Markdown test case files into TestSuite objects."""

import re
from .models import TestSuite, TestCase, TestStep


def _parse_table(lines: list) -> list:
    """Parse markdown table lines into list of dicts keyed by header."""
    rows = []
    headers = None
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('|'):
            break
        # Skip separator rows (|---|---|)
        if re.match(r'^\|[-| :]+\|$', stripped):
            continue
        cells = [c.strip() for c in stripped.strip('|').split('|')]
        if headers is None:
            headers = [h.strip('* ') for h in cells]
        else:
            rows.append(dict(zip(headers, cells)))
    return rows


def _extract_tables(content: str) -> list:
    """Extract all tables from a markdown section as list of row-dicts."""
    tables = []
    table_lines = []
    in_table = False

    for line in content.split('\n'):
        if line.strip().startswith('|'):
            in_table = True
            table_lines.append(line)
        else:
            if in_table and table_lines:
                tables.append(_parse_table(table_lines))
                table_lines = []
            in_table = False

    if table_lines:
        tables.append(_parse_table(table_lines))

    return tables


def _split_h2_sections(content: str) -> dict:
    """Split content into a dict of {section_title: section_body} for ## headings."""
    sections = {}
    current_title = None
    current_lines = []

    for line in content.split('\n'):
        m = re.match(r'^## (.+)$', line)
        if m:
            if current_title is not None:
                sections[current_title] = '\n'.join(current_lines)
            current_title = m.group(1).strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        sections[current_title] = '\n'.join(current_lines)

    return sections


def _parse_config(section_body: str) -> dict:
    """Parse the Configuration section table into {parameter: value} dict."""
    tables = _extract_tables(section_body)
    if not tables:
        return {}
    config = {}
    for row in tables[0]:
        param = row.get('Parameter', '').strip()
        value = row.get('Value', '').strip()
        if param:
            config[param] = value
    return config


def _parse_metadata(rows: list) -> dict:
    """Flatten a Field/Value table into a plain dict."""
    meta = {}
    for row in rows:
        field = row.get('Field', '').strip()
        value = row.get('Value', '').strip()
        if field:
            meta[field] = value
    return meta


def _parse_parameter_overrides(params_str: str) -> dict:
    """Parse 'KEY=VALUE, KEY2=VALUE2' string into a dict."""
    overrides = {}
    if not params_str:
        return overrides
    for pair in params_str.split(','):
        pair = pair.strip()
        if '=' in pair:
            key, _, value = pair.partition('=')
            overrides[key.strip()] = value.strip()
    return overrides


def _parse_test_case(section_title: str, section_body: str) -> TestCase:
    """Parse a TC section into a TestCase object."""
    # Extract TC ID and title from the section heading text
    # Section title format: "TC_SWE4_001: Descriptive Title"
    m = re.match(r'^(TC[\w-]+):\s*(.+)$', section_title)
    if m:
        tc_id = m.group(1).strip()
        tc_title = m.group(2).strip()
    else:
        tc_id = section_title.split(':')[0].strip()
        tc_title = section_title.partition(':')[2].strip() or tc_id

    tables = _extract_tables(section_body)

    metadata = {}
    steps = []

    for table in tables:
        if not table:
            continue
        headers = list(table[0].keys())
        # Metadata table: Field | Value
        if 'Field' in headers and 'Value' in headers:
            metadata = _parse_metadata(table)
        # Steps table: Step | Action | Expected Result
        elif any(h in headers for h in ('Step', 'Step #')):
            for row in table:
                step_num = row.get('Step', row.get('Step #', '')).strip()
                action = row.get('Action', row.get('Action / Stimulus', '')).strip()
                expected = row.get('Expected Result', '').strip()
                if step_num.isdigit():
                    steps.append(TestStep(
                        number=int(step_num),
                        action=action,
                        expected=expected,
                    ))

    requirements = [r.strip() for r in metadata.get('Requirements', '').split(',') if r.strip()]
    parameter_overrides = _parse_parameter_overrides(metadata.get('Parameters', ''))

    return TestCase(
        id=tc_id,
        title=tc_title,
        objective=metadata.get('Objective', ''),
        requirements=requirements,
        priority=metadata.get('Priority', ''),
        preconditions=metadata.get('Preconditions', ''),
        postconditions=metadata.get('Postconditions', ''),
        parameters=parameter_overrides,
        steps=steps,
    )


def parse_file(content: str) -> TestSuite:
    """Parse a full test case Markdown file into a TestSuite object."""
    # Extract H1 title
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    suite_title = title_match.group(1).strip() if title_match else 'Untitled Suite'

    sections = _split_h2_sections(content)

    config = {}
    test_cases = []

    for section_title, section_body in sections.items():
        if section_title.strip() == 'Configuration':
            config = _parse_config(section_body)
        elif re.match(r'^TC[\w-]+:', section_title):
            test_cases.append(_parse_test_case(section_title, section_body))

    return TestSuite(title=suite_title, config=config, test_cases=test_cases)
