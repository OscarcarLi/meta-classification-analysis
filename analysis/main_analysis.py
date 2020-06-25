
import os
from tqdm import tqdm
import json
import argparse
import pickle
import torch
import torch.nn as nn
import numpy as np
import pprint
from tensorboardX import SummaryWriter
import re
import gc


from algorithm_trainer.models import gated_conv_net_original, resnet
from algorithm_trainer.algorithm_trainer import Generic_adaptation_trainer, Classical_algorithm_trainer
from algorithm_trainer.algorithms.algorithm import SVM, ProtoNet
from data_layer.dataset_managers import MetaDataManager, ClassicalDataManager
from analysis.objectives import var_reduction_disc


""" Always configure aux func before running analysis.
Find entire list in objectives file. Can be None too
"""

aux_func = var_reduction_disc
    


def main(args):

    is_training = False
    writer = None
    
    # load checkpoint
    if args.model_type == 'resnet':
        model = resnet.ResNet18(num_classes=args.num_classes, 
            distance_classifier=args.distance_classifier, add_bias=args.add_bias, no_fc_layer=args.no_fc_layer)
    elif args.model_type == 'conv64':
        model = ImpRegConvModel(
            input_channels=3, num_channels=64, img_side_len=image_size, num_classes=args.num_classes,
            verbose=True, retain_activation=True, use_group_norm=True, add_bias=args.add_bias)
    else:
        raise ValueError(
            'Unrecognized model type {}'.format(args.model_type))
    print("Model\n" + "=="*27)    
    print(model)
    if args.checkpoint != '':
        print(f"loading from {args.checkpoint}")
        model_dict = model.state_dict()
        chkpt_state_dict = torch.load(args.checkpoint)
        if 'model' in chkpt_state_dict:
            chkpt_state_dict = chkpt_state_dict['model']
        chkpt_state_dict_cpy = chkpt_state_dict.copy()
        # remove "module." from key, possibly present as it was dumped by data-parallel
        for key in chkpt_state_dict_cpy.keys():
            if args.cpy_fc_layer is False and 'fc.' in key:
                _  = chkpt_state_dict.pop(key)
            elif 'module.' in key:
                new_key = re.sub('module\.', '',  key)
                chkpt_state_dict[new_key] = chkpt_state_dict.pop(key)
        chkpt_state_dict = {k: v for k, v in chkpt_state_dict.items() if k in model_dict}
        model_dict.update(chkpt_state_dict)
        updated_keys = set(model_dict).intersection(set(chkpt_state_dict))
        print(f"Updated {len(updated_keys)} keys using chkpt")
        print("Following keys updated :", "\n".join(sorted(updated_keys)))
        model.load_state_dict(model_dict)                
    os.environ["CUDA_VISIBLE_DEVICES"] = args.device_number
    print('Using GPUs: ', os.environ["CUDA_VISIBLE_DEVICES"])
    model = torch.nn.DataParallel(model, device_ids=range(torch.cuda.device_count()))
    model.cuda()
        

    # optimizer
    loss_func = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam([
        {'params': model.parameters(), 'lr': args.lr},
    ])
    print("Total n_epochs: ", args.n_epochs)

    
    # data loader
    image_size = args.img_side_len
    val_file = os.path.join(args.dataset_path, 'val.json')
    meta_val_datamgr = MetaDataManager(
        image_size, batch_size=args.batch_size_val, n_episodes=args.n_iterations_val,
        n_way=args.n_way_val, n_shot=args.n_shot_val, n_query=args.n_query_val)
    meta_val_loader = meta_val_datamgr.get_data_loader(val_file, aug=False)
    classical_val_datamgr = ClassicalDataManager(image_size, batch_size=320)
    classical_val_loader = classical_val_datamgr.get_data_loader(val_file, aug=False)

    # algorithm
    if args.algorithm == 'SVM':
        algorithm = SVM(
            model=model,
            inner_loss_func=loss_func,
            n_way=args.n_way_train,
            n_shot=args.n_shot_train,
            n_query=args.n_query_train,
            device=args.device)

    elif args.algorithm == 'Protonet':
        algorithm = ProtoNet(
            model=model,
            inner_loss_func=loss_func,
            n_way=args.n_way_train,
            n_shot=args.n_shot_train,
            n_query=args.n_query_train,
            device=args.device)
    else:
        raise ValueError(
            'Unrecognized algorithm {}'.format(args.algorithm))



    
    # Iteratively optimize some objective and evaluate performance
    if aux_func:
        print("##"*27, f"AUX OBJECTIVE: {aux_func.__name__}", "##"*27)
    adaptation_trainer = Generic_adaptation_trainer(
        algorithm=algorithm,
        aux_objective=None,
        outer_loss_func=loss_func,
        outer_optimizer=optimizer, 
        writer=writer,
        log_interval=args.log_interval, grad_clip=args.grad_clip,
        model_type=args.model_type,
        n_aux_objective_steps=args.n_aux_objective_steps,
        label_offset=args.label_offset)
    classical_trainer = Classical_algorithm_trainer(
        model=model,
        loss_func=aux_func,
        optimizer=optimizer, writer=writer,
        log_interval=args.log_interval, save_folder=None, 
        grad_clip=args.grad_clip,
        label_offset=args.label_offset
    )
    
    
    # print results
    
    for iter_start in range(args.n_epochs):
        _ = classical_trainer.run(classical_val_loader, is_training=True, epoch=iter_start+1)
        # clean up garbage and clear cuda cache as much as possible
        gc.collect()
        results = adaptation_trainer.run(meta_val_loader, meta_val_datamgr)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(results)
            



if __name__ == '__main__':

    def str2bool(arg):
        return arg.lower() == 'true'

    parser = argparse.ArgumentParser(
        description='Analysis of Inner Solver methods for Meta Learning')

    # Algorithm
    parser.add_argument('--algorithm', type=str, help='type of algorithm')

    # Model
    parser.add_argument('--model-type', type=str, default='resnet',
        help='type of the model')
    parser.add_argument('--distance-classifier', action='store_true', default=False,
        help='use a distance classifer (cosine based)')
    parser.add_argument('--num-classes', type=int, default=200,
        help='no of classes -- used during fine tuning')
    parser.add_argument('--label-offset', type=int, default=0,
        help='offset for label values during fine tuning stage')
    parser.add_argument('--no-fc-layer', type=str2bool, default=True,
        help='will not add fc layer to model')
    parser.add_argument('--cpy-fc-layer', type=str2bool, default=False,
        help='copy fc layer from saved checkpoint model')

    # Optimization
    parser.add_argument('--optimizer', type=str, default='adam',
        help='optimizer')
    parser.add_argument('--lr', type=float, default=0.001,
        help='learning rate for the global update')
    parser.add_argument('--grad-clip', type=float, default=0.0,
        help='gradient clipping')
    parser.add_argument('--n-epochs', type=int, default=60000,
        help='number of model training epochs')
    parser.add_argument('--n-aux-objective-steps', type=int, default=5,
        help='number of gradient updates on the auxiliary objective for each task')
    parser.add_argument('--add-bias', type=str2bool, default=False,
        help='add bias term inner loop')

    # Dataset
    parser.add_argument('--dataset-path', type=str,
        help='which dataset to use')
    parser.add_argument('--batch-size-train', type=int, default=10,
        help='batch size for training')
    parser.add_argument('--batch-size-val', type=int, default=10,
        help='batch size for validation')
    parser.add_argument('--n-query-train', type=int, default=15,
        help='how many samples per class for validation (meta train)')
    parser.add_argument('--n-query-val', type=int, default=15,
        help='how many samples per class for validation (meta val)')
    parser.add_argument('--n-shot-train', type=int, default=5,
        help='how many samples per class for train (meta train)')
    parser.add_argument('--n-shot-val', type=int, default=5,
        help='how many samples per class for train (meta val)')
    parser.add_argument('--n-way-train', type=int, default=5,
        help='how classes per task for train (meta train)')
    parser.add_argument('--n-way-val', type=int, default=5,
        help='how classes per task for train (meta val)')
    parser.add_argument('--img-side-len', type=int, default=28,
        help='width and height of the input images')
    

    # Miscellaneous
    parser.add_argument('--device', type=str, default='cuda',
        help='set the device (cpu or cuda)')
    parser.add_argument('--device-number', type=str, default='0',
        help='gpu device number')
    parser.add_argument('--log-interval', type=int, default=100,
        help='number of batches between tensorboard writes')
    parser.add_argument('--checkpoint', type=str, default='',
        help='path to saved parameters.')
    parser.add_argument('--train-aug', action='store_true', default=True,
        help='perform data augmentation during training')
    parser.add_argument('--n-iterations-train', type=int, default=60000,
        help='no. of iterations train.') 
    parser.add_argument('--n-iterations-val', type=int, default=100,
        help='no. of iterations validation.') 
    
    
    args = parser.parse_args()

    # Create logs and saves folder if they don't exist
    if not os.path.exists('./train_dir'):
        os.makedirs('./train_dir')

    # main function call
    main(args)
