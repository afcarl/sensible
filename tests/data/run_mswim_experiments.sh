#!/bin/bash

bias=(0.0 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5)

for i in "${bias[@]}"
do
    python ground_truth_eval.py --use-bias-estimation True --bias-constant $i --run-name bias-$i
done
