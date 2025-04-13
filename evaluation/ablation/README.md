# Ablation Experiment

We measure the effectiveness of policy generation and lazy loading features in
isolation.

## Ablation Experiment 0:

What is the effectiveness of lazy loading with empty policies?

Set up as with Ablation Experiment 2, but use empty policy (`empty.json`).

## Ablation Experiment 1:

What is the effectiveness of policy generation without lazy loading?

```
docker compose run strict-all
```

- Create version of Unpickler without lazy loading
- run enforce-all
- Expect: fewer successfully loaded

Visualize results and generate table:

```
python3 scripts/generatetable.py evaluation/ablation/strict-manifest.toml evaluation/enforcement/results -strict > evaluation/tables/ablation-1.tex

pdflatex evaluation/tables/ablation-1.pdf
```

## Ablation Experiment 2:

What is the effectiveness of lazy loading without generating customized
policies?

```
docker compose run lazy-wou-all
```

Overview: we replace all generated policies with the default Weights-Only
Unpickler policy and run the PickleBall loader. Any model that successfully
loads is

- Expect: fewer successfully loaded

