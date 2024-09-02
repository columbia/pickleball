"""
Given a JSON file containing a ground truth PickleBall policy and a JSON file
containing an inferred PickleBall policy,
"""
import argparse
import json

def compare_json_objects(json_obj1, json_obj2):
    def compare_lists(list1, list2):
        set1 = set(list1)
        set2 = set(list2)

        in_first_not_second = set1 - set2
        in_second_not_first = set2 - set1
        in_both = set1 & set2

        return in_first_not_second, in_second_not_first, in_both

    def compute_f1(true_positives, false_positives, false_negatives):

        precision = 1.0 if true_positives + false_positives == 0 else true_positives / (true_positives + false_positives)
        recall = 1.0 if true_positives + false_negatives == 0 else true_positives / (true_positives + false_negatives)
        f1 = 1.0 if true_positives + false_positives + false_negatives == 0 else (2 * true_positives) / (2 * true_positives + false_positives + false_negatives)

        return precision, recall, f1

    global_diff_1, global_diff_2, global_in_both = compare_lists(
        json_obj1.get('globals', []),
        json_obj2.get('globals', []))
    reduce_diff_1, reduce_diff_2, reduce_in_both = compare_lists(
        json_obj1.get('reduces', []),
        json_obj2.get('reduces', []))

    global_precision, global_recall, global_f1 = compute_f1(
        true_positives=len(global_in_both),
        false_positives=len(global_diff_2),
        false_negatives=len(global_diff_1)
    )

    reduce_precision, reduce_recall, reduce_f1 = compute_f1(
        true_positives=len(reduce_in_both),
        false_positives=len(reduce_diff_2),
        false_negatives=len(reduce_diff_1)
    )

    result = {
        "global_lines": {
            "in_baseline_not_inferred": len(global_diff_1),
            "in_inferred_not_baseline": len(global_diff_2),
            "in_both": len(global_in_both),
            "precision": global_precision,
            "recall": global_recall,
            "f1": global_f1
        },
        "reduce_lines": {
            "in_baseline_not_inferred": len(reduce_diff_1),
            "in_inferred_not_baseline": len(reduce_diff_2),
            "in_both": len(reduce_in_both),
            "precision": reduce_precision,
            "recall": reduce_recall,
            "f1": reduce_f1
        }
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare two JSON files for representing PickleBall"
            "policies"))
    parser.add_argument(
        "file1",
        type=str,
        help="The filename of the first JSON file (baseline)")
    parser.add_argument(
        "file2",
        type=str,
        help="The filename of the second JSON file (inferred)")
    args = parser.parse_args()

    try:
        with open(args.file1, 'r', encoding='utf-8') as file1, open(args.file2, 'r', encoding='utf-8') as file2:
            json_obj1 = json.load(file1)
            json_obj2 = json.load(file2)
    except FileNotFoundError as e:
        print(f"Error: {e.filename} was not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON in file. {e}")
        return

    comparison_result = compare_json_objects(json_obj1, json_obj2)
    print(json.dumps(comparison_result, indent=2))


if __name__ == "__main__":
    main()
