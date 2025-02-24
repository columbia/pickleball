# Ablation Experiment

We measure the effectiveness of policy generation and lazy loading features in
isolation.

## Ablation Experiment 1:

What is the effectiveness of policy generation without lazy loading?

- Create version of Unpickler without lazy loading
- Rebuild all containers with this version
- run enforce-all
- Expect: fewer successfully loaded

In `docker-compose.yml` identify the `pickleball-enforce` and
`pickleball-enforce-deb11` services.
* In each, change `context: enforce` to `context: evaluation/ablation`

Rebuild all containers:

```
docker compose build --no-cache
```

Ensure that there are generated policies in `evaluation/policies`.

Then run all enforcement loading experiments:

```
docker compose run enforce-all
```

Visualize results and generate table:

```
python3 scripts/generatetable.py evaluation/manifest --enforcement-results evaluation/enforcement/results > evaluation/tables/ablation-1.tex

pdflatex evaluation/tables/ablation-1.pdf
```

## Ablation Experiment 2:

What is the effectiveness of lazy loading without generating customized
policies?

Overview: we replace all generated policies with the default Weights-Only
Unpickler policy and run the PickleBall loader. Any model that successfully
loads is

- Set all policies to WOP then run enforce-all
- Purpose:
- Expect: fewer successfully loaded

Set all policies to the default WOP:

```
python3 TODO
```
