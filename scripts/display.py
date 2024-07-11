from scripts.constants import Constants
import numpy as np
import matplotlib.pyplot as plt


def print_claim(claim):
    yellow = '\033[93m'
    green = '\033[92m'
    orange = '\033[38;5;208m'
    reset = '\033[0m'

    for key, value in claim.items():
        if isinstance(value, list):
            print(f"\t\t\t{yellow}{key}:{reset}")
            for item in value:
                print(f"\t\t\t\t{orange}{item[Constants.Attributes.NAME]}: {green}{item[Constants.Attributes.VALUE]},{reset}")
        else:
            print(f"\t\t\t{yellow}{key}:{reset} {green}{value}{reset}")
    print("\n")


def print_table_claims(table_idx, claims, print_extracted=True, print_wrong=True):
    print(f"\tTable Index: {table_idx}")
    if print_extracted:
        print("\t\tExtracted Claims:")
        extracted_claims = claims[Constants.Attributes.EXTRACTED_CLAIMS]
        for claim in extracted_claims:
            print_claim(claim)

    if print_wrong:
        print("\t\tWrong Claims:")
        for wrong_claim in claims[Constants.Attributes.WRONG_CLAIMS]:
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
        print(f"Count: {spec_info[Constants.Attributes.COUNT]}")
        print("Values:")
        for value, count in spec_info[Constants.Attributes.VALUES].items():
            print(f"  {value}: {count}")
        print()


def print_results_map(results_map):
    for measure, measure_info in results_map.items():
        print(f"Measure: {measure}")
        print(f"Total count: {measure_info[Constants.Attributes.COUNT]}")
        print("Outcomes:")
        for outcome in measure_info[Constants.Attributes.OUTCOMES]:
            print(f"  {outcome}")
        print()


def plot_grouped_bars(data, ax=None):
    values = [item[1] for item in data]
    groups = [item[0].split('_')[0] for item in data]

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        show_plot = True
    else:
        show_plot = False 

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

    if show_plot:
        plt.show()

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
    for key, group_colors in all_group_colors:
        key_group_colors[key] = [(group, color) for group, color in group_colors.items()]

    for key, groups_colors in key_group_colors.items():
        print(f"Dir: {key}")
        for group, color in groups_colors:
            colored_bar = print_colored_bar(color)
            print(f"{group}({colored_bar})", end="\t")
        print()


def show_single_key_group_color(group_colors):
    for key, color in group_colors.items():
        colored_bar = print_colored_bar(color)
        print(f"Article ID: {key}\t {colored_bar}")



def plot_value_distribution(data, color="orange"):
    values = [value for _, value in data]
    
    bins = np.arange(0, 1.05, 0.05)
    
    weights = np.ones_like(values) / len(values)
    
    plt.figure(figsize=(12, 6))
    plt.hist(
        values, 
        bins=bins, 
        weights=weights * 100,
        edgecolor='black', 
        alpha=0.7, 
        color=color, 
        histtype='bar', 
        rwidth=0.95
    )

    mean_value = np.mean(values)
    median_value = np.median(values)

    plt.axvline(mean_value, color='blue', linestyle='dashed', linewidth=1)
    plt.axvline(median_value, color='green', linestyle='dashed', linewidth=1)
    plt.text(mean_value + 0.005, 42, f'Mean: {mean_value:.2f}', color='blue')
    plt.text(median_value + 0.005, 38, f'Median: {median_value:.2f}', color='green')
    
    plt.title('Distribution of Coverage values')
    plt.xlabel('Value')
    plt.ylabel('Percentage')

    plt.xticks(np.arange(0, 1.05, 0.05))
    plt.ylim(0, 45)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.show()
