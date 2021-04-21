#! /bin/bash

output='metal_tiered_r12_SVM_n5s15q6tb8_SGD0.1Drop204050'
# method_dataset_model_innerAlg_config_outerOpt_misc
device='0'
mkdir -p logs
mkdir -p runs

CUDA_VISIBLE_DEVICES="$device" nohup python eval.py \
--eot-model True \
--fix-support 0 \
--model-type resnet_12 \
--avg-pool False \
--projection False \
--num-classes-train 0 \
--algorithm SVM \
--learnable-scale True \
--classifier-metric euclidean \
--dataset-path datasets/filelists/tieredImagenet-base \
--img-side-len 84 \
--batch-size-val 2 \
--n-way-val 5 \
--n-shot-val 5 \
--do-one-shot-eval-too False \
--n-query-val 15 \
--n-iterations-val 1000 \
--preload-train True \
--eps 0. \
--output-folder ${output} \
--device cuda \
--device-number ${device} \
--checkpoint runs/metal_tiered_r12_SVM_n5s15q6tb8_SGD0.1Drop204050/chkpt_060.pt \
--log-interval 100 > logs/${output}_evaleot.log &
tail -f logs/${output}_evaleot.log