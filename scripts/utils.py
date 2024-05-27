import os
import matplotlib.pyplot as plt
import numpy as np
import re
import difflib


def remove_unicodes(input_string):
    return re.sub(r'[^\x00-\x7F]+', '', input_string)


def remove_duplicates(input_list: list):
    return list(set(input_list))


def check_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


def detect_number(string):
    string = string.replace(' ', '')
    if string == '' or not string[0].isdigit():
        return False

    string = re.sub(r'(?<=\d)\.(?=\d)', '1', string)

    digit_count = sum(c.isdigit() for c in string)
    non_digit_count = len(string) - digit_count

    if digit_count >= 0.5 * (digit_count + non_digit_count):
        numerical_part = re.search(r'[\d.]+', string).group()
        if numerical_part:
            return True

    return False


def count_occurrences(elements):
    occurrences = {}
    for elem in elements:
        if elem in occurrences:
            occurrences[elem] += 1
        else:
            occurrences[elem] = 1

    return occurrences


def remove_items(items, to_remove):
    return [item for item in items if item not in to_remove]


def find_substrings(input_string, search_list, equality_f):
    sub_strings = input_string.split()
    
    output = []
    if len(sub_strings) == 1:
        return output
    

    for sub_s in sub_strings:
        for seach_s in search_list:
            if equality_f(sub_s, seach_s) > 0:
                output.append(seach_s)

    len_output = len(output)
    if len_output < 2:
        return output
    
    to_remove = set()
    for i in range(len_output - 1):
        for j in range(i + 1, len_output):
            if equality_f(output[i], output[j]) > 0:
                sim_to_i = equality_f(input_string, output[i])
                sim_to_j = equality_f(input_string, output[j])

                to_remove.add(output[i] if sim_to_i > sim_to_j else output[j])
    
    output = [s for s in output if s not in to_remove]
    return output


def fuzzy_string_similarity(str_1, str_2, lower=True):
    if lower:
        str_1 = str_1.lower()
        str_2 = str_2.lower()

    return difflib.SequenceMatcher(None, str_1, str_2).ratio()


def print_claim(claim):
    yellow = '\033[93m'
    green = '\033[92m'
    orange = '\033[38;5;208m'
    reset = '\033[0m'

    for key, value in claim.items():
        if isinstance(value, list):
            print(f"\t\t\t{yellow}{key}:{reset}")
            for item in value:
                print(f"\t\t\t\t{orange}{item['name']}: {green}{item['value']},{reset}")
        else:
            print(f"\t\t\t{yellow}{key}:{reset} {green}{value}{reset}")
    print("\n")


def print_table_claims(table_idx, claims, print_extracted=True, print_wrong=True):
    print(f"\tTable Index: {table_idx}")
    if print_extracted:
        print("\t\tExtracted Claims:")
        extracted_claims = claims['extracted_claims']
        for claim in extracted_claims:
            print_claim(claim)

    if print_wrong:
        print("\t\tWrong Claims:")
        for wrong_claim in claims['wrong_claims']:
            print(f"\t\t\t\033[91m{wrong_claim}\033[0m")


def print_claims(data, print_all=True, article_id=None, print_extracted=True, print_wrong=True):
    if print_all:
        for article_id, tables in data.items():
            print(f"Article ID: {article_id}")
            for table_idx, claims in tables.items():
                print_table_claims(table_idx, claims, print_extracted, print_wrong)
    else:
        if article_id is not None and article_id in data:
            tables = data[article_id]
            for table_idx, claims in tables.items():
                print(f"Article ID: {article_id}")
                print_table_claims(table_idx, claims, print_extracted, print_wrong)


def print_specifications(specs_map):
    for spec_name, spec_info in specs_map.items():
        print(f"Specification: {spec_name}")
        print(f"Count: {spec_info['count']}")
        print("Values:")
        for value, count in spec_info['values'].items():
            print(f"  {value}: {count}")
        print()


def print_results_map(results_map):
    for measure, measure_info in results_map.items():
        print(f"Measure: {measure}")
        print(f"Total count: {measure_info['count']}")
        print("Outcomes:")
        for outcome in measure_info['outcomes']:
            print(f"  {outcome}")
        print()


def plot_grouped_bars(data, ax):
    values = [item[1] for item in data]
    groups = [item[0].split('_')[0] for item in data]

    group_colors = {}
    unique_groups = set(groups)
    colors = plt.cm.tab10.colors
    for i, group in enumerate(unique_groups):
        group_colors[group] = colors[i % len(colors)]

    for i, (value, group) in enumerate(zip(values, groups)):
        ax.bar(i, value, color=group_colors[group], width=1.0)

    average = np.mean(values)
    median = np.median(values)

    ax.axhline(y=average, color='red', linestyle='--', label=f'Average: {average:.2f}')
    ax.axhline(y=median, color='green', linestyle='-.', label=f'Median: {median:.2f}')

    ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    ax.legend(loc='lower right')

    return group_colors

def plot_dataset_results(dataset_results, num_cols=5):
    num_plots = len(dataset_results)
    num_cols = max(min(num_plots, num_cols), 2)
    num_rows = (num_plots + num_cols - 1) // num_cols

    fig, axes = plt.subplots(num_rows, num_cols, figsize=(6*num_cols, 4*num_rows))

    all_group_colors = {}

    for idx, (key, result) in enumerate(dataset_results.items()):
        row = idx // num_cols
        col = idx % num_cols
        ax = axes[row, col] if num_rows > 1 else axes[col]
        group_colors = plot_grouped_bars(result, ax)

        ax.text(0.5, 0.05, f'Prompt: {key}', transform=ax.transAxes, fontsize=10,
                horizontalalignment='center', bbox=dict(facecolor='white', alpha=0.8))

        all_group_colors[key] = group_colors

    if num_plots % num_cols != 0:
        for j in range(num_plots % num_cols, num_cols):
            axes[-1, j].axis('off')

    plt.tight_layout()
    plt.show()

    return all_group_colors


def print_colored_bar(color):
    r, g, b = int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
    return f"\033[48;2;{r};{g};{b}m  \033[0m"


def show_key_group_colors(all_group_colors):
    key_group_colors = {}
    for key, group_colors in all_group_colors.items():
        key_group_colors[key] = [(group, color) for group, color in group_colors.items()]

    for key, groups_colors in key_group_colors.items():
        print(f"Dir: {key}")
        for group, color in groups_colors:
            colored_bar = print_colored_bar(color)
            print(f"{group}({colored_bar})", end="\t")
        print()
