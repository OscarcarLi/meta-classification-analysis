python main.py \
--algorithm protonet \
--model-type impregconv \
--original-conv \
--slow-lr 0.001 \
--model-grad-clip 0. \
--dataset miniimagenet \
--num-batches-meta-train 60000 \
--num-batches-meta-val 100 \
--meta-batch-size 6 \
--num-classes-per-batch-meta-train 20 \
--num-classes-per-batch-meta-val 5 \
--num-classes-per-batch-meta-test 5 \
--num-train-samples-per-class-meta-train 1 \
--num-train-samples-per-class-meta-val 1 \
--num-train-samples-per-class-meta-test 1 \
--num-val-samples-per-class-meta-train 10 \
--num-val-samples-per-class-meta-val 10 \
--num-val-samples-per-class-meta-test 10 \
--img-side-len 84 \
--output-folder impregmaml_minim_20w1s_protonet \
--device cuda \
--device-number 3 \
--log-interval 50 \
--save-interval 1000 \
--val-interval 1000 \
--num-channels 64 \
--verbose True \
--retain-activation True \
--use-group-norm True \
--optimizer adam
# --checkpoint train_dir/impregmaml_minim_5w5s_metaoptnet_fixed/maml_impregconv_20000.pt


# --momentum \
# --gamma-momentum 0.2 \
# --modulation-mat-rank 8 \


# Nameing convention 
# dataset_type_main_model_rank_training_paradigm_embedding_model   