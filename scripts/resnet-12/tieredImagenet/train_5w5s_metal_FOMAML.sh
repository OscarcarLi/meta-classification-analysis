#! /bin/bash

output='metal_tiered_r12_FOMAMLinnUpd5T20Vp0.01_n5s5q15tb4_Adam0.01det3565'
# method_dataset_model_innerAlg_config_outerOpt 
device='0'
mkdir -p logs
mkdir -p runs

CUDA_VISIBLE_DEVICES="$device" python main.py \
--fix-support 0 \
--model-type resnet_12 \
--avg-pool True \
--projection False \
--num-classes-train 5 \
--classifier-type linear \
--algorithm InitBasedAlgorithm \
--init-meta-algorithm FOMAML \
--inner-update-method sgd \
--alpha 0.01 \
--num-updates-inner-train 5 \
--num-updates-inner-val 20 \
--classifier-metric euclidean \
--dataset-path datasets/filelists/tieredImagenet-base \
--img-side-len 84 \
--n-epochs 70 \
--batch-size-train 4 \
--n-way-train 5 \
--n-shot-train 5 \
--n-query-train 15 \
--n-iters-per-epoch 1000 \
--batch-size-val 2 \
--n-way-val 5 \
--n-shot-val 5 \
--n-query-val 15 \
--n-iterations-val 5000 \
--support-aug True \
--query-aug True \
--randomize-query False \
--preload-train True \
--optimizer-type Adam \
--lr 0.01 \
--weight-decay 0.0005 \
--grad-clip 0. \
--drop-lr-epoch 35,65 \
--drop-factors 0.1,0.01 \
--lr-scheduler-type deterministic \
--eps 0. \
--restart-iter 0 \
--output-folder ${output} \
--device cuda \
--device-number ${device} \
--log-interval 100