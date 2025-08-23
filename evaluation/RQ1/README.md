# RQ1: Block Malicious Models

## Instructions
After building the enforce docker images, e.g., ` pickleball-superimage:latest`, run

```bash
sh eval-pickleball.sh malicious-model-on-host.txt pickleball-superimage:latest 80
```
This uses the policy generated with superimage library.

The expected output:
```
=== SUMMARY ===
Total model tested: 84
Loaded: 0
Blocked: 84

PERCENTAGES:
Blocked: 100% (84/84 models)
Loaded: 0% (0/84 models)
```

Running against a policy takes around 5 mins.
