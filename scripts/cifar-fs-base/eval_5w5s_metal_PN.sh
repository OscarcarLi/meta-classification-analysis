#! /bin/bash

output='metal_cifar-fs-base_r12_PN_n20s5q15tb1_SGD0.1Drop204050'
# method_dataset_model_innerAlg_config_outerOpt_misc
device='2'
mkdir -p logs
mkdir -p runs

CUDA_VISIBLE_DEVICES="$device" nohup python eval.py \
--fix-support 0 \
--model-type resnet_12 \
--avg-pool True \
--projection False \
--num-classes-train 0 \
--algorithm ProtoNet \
--scale-factor 10. \
--classifier-metric euclidean \
--dataset-path datasets/filelists/cifar-fs-base \
--img-side-len 32 \
--batch-size-val 2 \
--n-way-val 5 \
--n-shot-val 5 \
--do-one-shot-eval-too False \
--n-query-val 15 \
--n-iterations-val 1000 \
--eps 0. \
--output-folder ${output} \
--device cuda \
--device-number ${device} \
--checkpoint runs/metal_cifar-fs-base_r12_PN_n20s5q15tb1_SGD0.1Drop204050/chkpt_021.pt \
--log-interval 100 > logs/${output}_eval.log &
tail -f logs/${output}_eval.log