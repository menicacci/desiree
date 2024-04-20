import os
import matplotlib.pyplot as plt
import numpy as np


def check_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


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


def plot_dataset_results(dataset_results):
    n = len(dataset_results)
    rows = n // 3 if n % 3 == 0 else n // 3 + 1

    fig, axs = plt.subplots(rows, 3, figsize=(16, 12))

    for i, result in enumerate(dataset_results):
        row = i // 3
        col = i % 3
        plot_grouped_bars(result, axs[row, col])

    plt.tight_layout()
    plt.show()
