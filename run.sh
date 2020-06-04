# bash run_grid.sh inner_solvers/minim_5w5s_SVM/maml_impregconv_20000.pt
# bash run_grid.sh inner_solvers/minim_5w1s_SVM/maml_impregconv_22000.pt
# bash run_grid.sh inner_solvers/minim_5w5s_LR/maml_impregconv_7000.pt
# bash run_grid.sh inner_solvers/minim_5w1s_LR/maml_impregconv_18000.pt
# bash run_grid.sh inner_solvers/minim_5w5s_protonet/maml_impregconv_8000.pt
# bash run_grid.sh inner_solvers/minim_5w1s_protonet/maml_impregconv_20000.pt

export PYTHONPATH='.'
python scripts/dump_features.py inner_solvers/minim_5w5s_SVM/maml_impregconv_20000.pt inner_solvers_features/minim_5w5s_SVM_features_dict.pkl
python scripts/dump_features.py inner_solvers/minim_5w1s_SVM/maml_impregconv_22000.pt inner_solvers_features/minim_5w1s_SVM_features_dict.pkl
python scripts/dump_features.py inner_solvers/minim_5w5s_LR/maml_impregconv_7000.pt inner_solvers_features/minim_5w5s_LR_features_dict.pkl
python scripts/dump_features.py inner_solvers/minim_5w1s_LR/maml_impregconv_18000.pt inner_solvers_features/minim_5w1s_LR_features_dict.pkl
python scripts/dump_features.py inner_solvers/minim_5w5s_protonet/maml_impregconv_8000.pt inner_solvers_features/minim_5w5s_protonet_features_dict.pkl
python scripts/dump_features.py inner_solvers/minim_5w1s_protonet/maml_impregconv_20000.pt inner_solvers_features/minim_5w1s_protonet_features_dict.pkl