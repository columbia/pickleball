import json
from datetime import datetime

# Initialize dictionaries for storing examples
st_first_not_same_day = {}  # `safetensor` commits before `bin`, but not on the same day
st_first_not_same_hour = {}  # `safetensor` commits before `bin`, but not within the same hour
bin_first_not_same_day = {}  # `bin` commits before `safetensor`, but not on the same day
bin_first_not_same_hour = {}  # `bin` commits before `safetensor`, but not within the same hour

with open("model_commit_times.json", "r") as f:
    commit_times = json.load(f)

for key, times in commit_times.items():
    # Check if both time entries exist and convert string times to datetime objects
    if times["safetensor"] and times["bin"]:
        st_time = datetime.fromisoformat(times["safetensor"])
        bin_time = datetime.fromisoformat(times["bin"])

        # Determine the comparison results for day and hour
        same_day = st_time.date() == bin_time.date()
        same_hour = same_day and st_time.hour == bin_time.hour

        # Prepare the data entry, including custom_code presence
        data_entry = {
            'safetensor': times['safetensor'],
            'bin': times['bin'],
            'custom_code': times.get('custom_code', False)  # Default to False if not present
        }

        if st_time < bin_time:
            if not same_day:
                st_first_not_same_day[key] = data_entry
            elif not same_hour:
                st_first_not_same_hour[key] = data_entry
        elif st_time > bin_time:
            if not same_day:
                bin_first_not_same_day[key] = data_entry
            elif not same_hour:
                bin_first_not_same_hour[key] = data_entry

# Save the results into separate files
with open("st_first_not_same_day.json", "w") as f:
    json.dump(st_first_not_same_day, f, indent=4)

with open("st_first_not_same_hour.json", "w") as f:
    json.dump(st_first_not_same_hour, f, indent=4)

with open("bin_first_not_same_day.json", "w") as f:
    json.dump(bin_first_not_same_day, f, indent=4)

with open("bin_first_not_same_hour.json", "w") as f:
    json.dump(bin_first_not_same_hour, f, indent=4)
