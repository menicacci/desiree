import random


def check_range_input(float_list: list) -> bool:    
    return not (float_list != sorted(float_list) and any(num <= 0 or num >= 1 for num in float_list))


def generate_ranges(float_list) -> list:
    if not check_range_input(float_list):
        return []

    ranges = []
    prev = 0
    for num in float_list:
        ranges.append((prev, num))
        prev = num
    ranges.append((prev, 1))
    return ranges


def pick_c_from_results(results: list, ranges: list, c: int) -> list:    
    result = []
    for range_start, range_end in ranges:
        filtered_elements = [x for x in results if range_start <= x[1] < range_end]
        
        if len(filtered_elements) < c:
            print(f"Not enough elements in the range ({range_start}, {range_end}) to pick {c} elements.")
            c = len(filtered_elements)

        picked_elements = random.sample(filtered_elements, c)
        result.append(picked_elements)
    
    return result
