#! /bin/bash

output='metal_tiered_r12_PN_n20s5q15tb1_SGD0.1Drop204050_base_correct'
# method_dataset_model_innerAlg_config_outerOpt_misc
device='0,1'
mkdir -p logs
mkdir -p runs

CUDA_VISIBLE_DEVICES="$device" python main.py \
--fix-support 0 \
--model-type resnet_12 \
--avg-pool True \
--projection False \
--num-classes-train 0 \
--algorithm ProtoNet \
--scale-factor 10. \
--classifier-metric euclidean \
--dataset-path datasets/filelists/tieredImagenet-base \
--img-side-len 84 \
--n-epochs 60 \
--batch-size-train 1 \
--n-way-train 20 \
--n-shot-train 5 \
--n-query-train 15 \
--n-iters-per-epoch 1000 \
--batch-size-val 2 \
--n-way-val 5 \
--n-shot-val 5 \
--do-one-shot-eval-too False \
--n-query-val 15 \
--n-iterations-val 1000 \
--support-aug False \
--query-aug True \
--randomize-query True \
--preload-train True \
--optimizer-type SGDM \
--lr 0.1 \
--weight-decay 0.0005 \
--grad-clip 0. \
--drop-lr-epoch 20,40,50 \
--lr-scheduler-type deterministic \
--eps 0. \
--restart-iter 0 \
--output-folder ${output} \
--device-number ${device} \
--log-interval 100
