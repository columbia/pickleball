import argparse
import json

def compare_json_objects(json_obj1, json_obj2):
    def compare_lists(list1, list2):
        set1 = set(list1)
        set2 = set(list2)

        in_first_not_second = set1 - set2
        in_second_not_first = set2 - set1
        in_both = set1 & set2

        return len(in_first_not_second), len(in_second_not_first), len(in_both)

    global_diff_1, global_diff_2, global_in_both = compare_lists(json_obj1.get('globals_expected', []), json_obj2.get('globals', []))
    reduce_diff_1, reduce_diff_2, reduce_in_both = compare_lists(json_obj1.get('reduces_expected', []), json_obj2.get('reduces', []))

    result = {
        "global_lines": {
            "in_first_not_second": global_diff_1,
            "in_second_not_first": global_diff_2,
            "in_both": global_in_both
        },
        "reduce_lines": {
            "in_first_not_second": reduce_diff_1,
            "in_second_not_first": reduce_diff_2,
            "in_both": reduce_in_both
        }
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Compare two JSON files for discrepancies in 'global_lines' and 'reduce_lines' fields.")
    parser.add_argument('file1', type=str, help='The filename of the first JSON file (ground truth).')
    parser.add_argument('file2', type=str, help='The filename of the second JSON file to compare against the first.')

    args = parser.parse_args()

    try:
        with open(args.file1, 'r', encoding='utf-8') as f1, open(args.file2, 'r', encoding='utf-8') as f2:
            json_obj1 = json.load(f1)
            json_obj2 = json.load(f2)

        comparison_result = compare_json_objects(json_obj1, json_obj2)
        print(json.dumps(comparison_result, indent=4))

    except FileNotFoundError as e:
        print(f"Error: {e.filename} was not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON in file. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
