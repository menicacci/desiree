import re


def check_tuple(input_str: str):
    pattern = r'^(.+?),\s+(.+)$'
    match = re.match(pattern, input_str)
    if match:
        return match.groups()
    else:
        return None


def check_claim(claim: str):
    if len(claim) > 2 and claim[0] == '<' and claim[-1] == '>':
        claim = claim[1:-1]

        if claim.startswith('{') and '>}' in claim:
            specifications, scientific_result = claim.split('>}', 1)
            specifications = specifications[1:] + '>'
            pattern = r'<\s*[^<>]*\s*>'
            if re.match(rf'^{pattern}(,\s*{pattern})*$', specifications):
                specs_list = re.findall(r'<\s*([^<>]*)\s*>', specifications)

                if scientific_result == '' or scientific_result.startswith(', '):
                    specifications_values = []

                    for spec in specs_list:
                        name_value = check_tuple(spec)
                        if name_value is None:
                            print(spec)
                            return None

                        specifications_values.append(name_value)

                    measure = None
                    outcome = None
                    if scientific_result != '':
                        measure_outcome = check_tuple(scientific_result[2:])
                        if measure_outcome is None:
                            return None

                        measure = measure_outcome[0]
                        outcome = measure_outcome[1]

                    return {
                        'specifications': specifications_values,
                        'measure': measure,
                        'outcome': outcome
                    }

    else:
        return None
