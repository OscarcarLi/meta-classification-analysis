python main_classical.py \
--model-type resnet \
--classifier-type distance-classifier \
--loss-names cross_ent var_disc \
--lambdas 1.0  0.2 \
--lr 0.001 \
--grad-clip 0. \
--dataset-path data/filelists/miniImagenet \
--num-classes 64 \
--n-epochs 400 \
--train-batch-size 64 \
--val-batch-size 50 \
--img-side-len 84 \
--output-folder classical_miniimagenet_dc_with_var_disc \
--device cuda \
--device-number 0,1,2,3 \
--log-interval 25 \
--train-aug