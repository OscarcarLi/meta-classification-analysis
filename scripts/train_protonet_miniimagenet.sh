python main.py \
--algorithm protonet \
--model-type impregconv \
--original-conv \
--num-channels 64 \
--retain-activation True \
--use-group-norm True \
--add-bias False \
--optimizer adam \
--slow-lr 0.0001 \
--optimizer-update-interval 4 \
--model-grad-clip 0. \
--dataset miniimagenet \
--num-batches-meta-train 80000 \
--num-batches-meta-val 100 \
--meta-batch-size 2 \
--num-classes-per-batch-meta-train 20 \
--num-classes-per-batch-meta-val 5 \
--num-classes-per-batch-meta-test 5 \
--num-train-samples-per-class-meta-train 1 \
--num-train-samples-per-class-meta-val 1 \
--num-train-samples-per-class-meta-test 1 \
--num-val-samples-per-class-meta-train 15 \
--num-val-samples-per-class-meta-val 15 \
--num-val-samples-per-class-meta-test 15 \
--img-side-len 84 \
--output-folder minim_20w1s_protonet_continued \
--device cuda \
--device-number 3 \
--log-interval 50 \
--save-interval 1000 \
--val-interval 1000 \
--checkpoint train_dir/minim_20w1s_protonet/maml_impregconv_79000.pt \
--verbose True

