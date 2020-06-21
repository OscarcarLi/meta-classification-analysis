import os
from tqdm import tqdm
import json
import argparse
import pickle
import torch
import numpy as np
from tensorboardX import SummaryWriter
import pprint





def main(args):
    is_training = not args.eval
    run_name = 'train' if is_training else 'eval'

    if is_training:
        writer = SummaryWriter('./train_dir/{0}/{1}'.format(
            args.output_folder, run_name))
        with open('./train_dir/{}/config.txt'.format(
            args.output_folder), 'w') as config_txt:
            for k, v in sorted(vars(args).items()):
                config_txt.write('{}: {}\n'.format(k, v))
    else:
        writer = None

    save_folder = './train_dir/{0}'.format(args.output_folder)
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)



    ####################################################
    #         DATASET AND DATALOADER CREATION          #
    ####################################################

    # There are 3 tyoes of files: base, val, novel
    # Here we train on base and validate on val
    image_size = args.img_side_len
    train_file = os.path.join(args.dataset_path, 'base.json')
    val_file = os.path.join(args.dataset_path, 'base.json')
    train_datamgr = ClassicalDataManager(image_size, batch_size=args.train_batch_size)
    train_loader = train_datamgr.get_data_loader(train_file, aug=args.train_aug)
    val_datamgr = ClassicalDataManager(image_size, batch_size=args.val_batch_size)
    val_loader = val_datamgr.get_data_loader(val_file, aug=False)
    


    ####################################################
    #             MODEL/BACKBONE CREATION              #
    ####################################################

    if args.model_type == 'resnet':
        model = resnet.ResNet18(num_classes=args.num_classes, 
            distance_classifier=args.distance_classifier)
    elif args.model_type == 'conv64':
        model = ImpRegConvModel(
            input_channels=3, num_channels=64, img_side_len=image_size,
            verbose=True, retain_activation=True, use_group_norm=True, add_bias=False)
    else:
        raise ValueError(
            'Unrecognized model type {}'.format(args.model_type))
    print("Model\n" + "=="*27)    
    print(model)


    # load from checkpoint
    if args.checkpoint != '':
        print(f"loading from {args.checkpoint}")
        state_dict = torch.load(args.checkpoint)
        model.load_state_dict(state_dict['model'])
        
    # Multi-gpu support and device setup
    os.environ["CUDA_VISIBLE_DEVICES"] = args.device_number
    print('Using GPUs: ', os.environ["CUDA_VISIBLE_DEVICES"])
    model = torch.nn.DataParallel(model, device_ids=range(torch.cuda.device_count()))
    model.cuda()




    ####################################################
    #                OPTIMIZER CREATION                #
    ####################################################


    loss_func = nn.CrossEntropyLoss()
    if args.optimizer == 'adam':
        optimizer = torch.optim.Adam(
            model.parameters(), lr=args.lr, weight_decay=5e-4)
    else:
        optimizer = torch.optim.SGD(
            model.parameters(), lr=args.lr, 
            momentum=0.9, nesterov=True, weight_decay=5e-4)
    print("Total n_epochs: ", args.n_epochs)
        


    ####################################################
    #         ALGORITHM & ALGORITHM TRAINER            #
    ####################################################

  
    if args.algorithm == 'LR':
        algorithm = ImpRMAML_inner_algorithm(
            model=model,
            embedding_model=embedding_model,
            inner_loss_func=loss_func,
            l2_lambda=args.l2_inner_loop,
            device=args.device,
            is_classification=True)

    elif args.algorithm == 'SVM':
        algorithm = MetaOptnet(
            model=model,
            inner_loss_func=loss_func,
            n_way=args.num_classes_per_batch_meta_train,
            n_shot_train=args.num_train_samples_per_class_meta_train,
            n_shot_val=args.num_train_samples_per_class_meta_val,
            device=args.device)

    elif args.algorithm == 'Protonet':
        algorithm = ProtoNet(
            model=model,
            inner_loss_func=loss_func,
            n_way=args.num_classes_per_batch_meta_train,
            n_shot_train=args.num_train_samples_per_class_meta_train,
            n_shot_val=args.num_train_samples_per_class_meta_val,
            device=args.device)

    elif args.algorithm == 'ProtoSVM':
        algorithm = ProtoSVM(
            model=model,
            inner_loss_func=loss_func,
            n_way=args.num_classes_per_batch_meta_train,
            n_shot_train=args.num_train_samples_per_class_meta_train,
            n_shot_val=args.num_train_samples_per_class_meta_val,
            device=args.device)


    if args.algorithm in ['LR']:
        trainer = LR_algorithm_trainer(
            algorithm=algorithm,
            outer_loss_func=loss_func,
            outer_optimizer=optimizer, 
            writer=writer,
            log_interval=args.log_interval, save_interval=args.save_interval,
            model_type=args.model_type, save_folder=save_folder, 
            outer_loop_grad_norm=args.model_grad_clip,
            hessian_inverse=args.hessian_inverse)
        
    elif args.algorithm in ['SVM', 'Protonet', 'ProtoSVM']:
        trainer = Generic_algorithm_trainer(
            algorithm=algorithm,
            outer_loss_func=loss_func,
            outer_optimizer=optimizers, 
            writer=writer,
            log_interval=args.log_interval, save_interval=args.save_interval,
            save_folder=save_folder, outer_loop_grad_norm=args.model_grad_clip,
            model_type=args.model_type,
            optimizer_update_interval=args.optimizer_update_interval)

    
    
    if is_training:
        # create train iterators
        train_iterator = iter(dataset['train']) 
        if args.optimizer == 'sgd':
            lambda_epoch = lambda e: 1.0 if e < 20 * args.optimizer_update_interval else (0.06 if e < 40 * args.optimizer_update_interval else 0.012 if e < 50 * args.optimizer_update_interval else (0.0024))
        else:
            lambda_epoch = lambda e: 1.0 if e < 20 * args.optimizer_update_interval else (0.1 if e < 40 * args.optimizer_update_interval else 0.01 * args.optimizer_update_interval if e < 50 * args.optimizer_update_interval else (0.002))
        lr_scheduler = torch.optim.lr_scheduler.LambdaLR(optimizers, lr_lambda=lambda_epoch, last_epoch=-1)
        for iter_start in range(1, num_batches['train'], args.val_interval):
            lr_scheduler.step()
            if hasattr(trainer._algorithm, '_n_way'):
                trainer._algorithm._n_way = args.num_classes_per_batch_meta_train
            for param_group in optimizers.param_groups:
                print('optimizer:', args.optimizer, 'lr:', param_group['lr'])
            try:
                train_result = trainer.run(train_iterator, is_training=True, 
                    start=iter_start, stop=iter_start+args.val_interval)
            except StopIteration:
                print("Finished training iterations.")
                print(train_result)
                print("Starting final validation.")
    
            # validation
            if hasattr(trainer._algorithm, '_n_way'):
                trainer._algorithm._n_way = args.num_classes_per_batch_meta_val
            tqdm.write("=="*27+"\nStarting validation")
            val_result = trainer.run(iter(dataset['val']), is_training=False, meta_val=True, start=iter_start+args.val_interval - 1)
            tqdm.write(str(val_result))
            tqdm.write("Finished validation\n" + "=="*27)
            
    else:
        if hasattr(trainer._algorithm, '_n_way'):
            trainer._algorithm._n_way = args.num_classes_per_batch_meta_test
        results = trainer.run(iter(dataset['test']), is_training=False, start=0)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(results)
        name = args.checkpoint[0:args.checkpoint.rfind('.')]
        

if __name__ == '__main__':

    def str2bool(arg):
        return arg.lower() == 'true'

    parser = argparse.ArgumentParser(
        description='Meta-Learning Inner Solvers')

    # Algorithm
    parser.add_argument('--algorithm', type=str, help='type of algorithm')

    # Model
    parser.add_argument('--model-type', type=str, default='gatedconv',
        help='type of the model')
    parser.add_argument('--retain-activation', type=str2bool, default=False,
        help='if True, use activation function in the last layer;\
             otherwise dont use activation in the last layer')
    parser.add_argument('--add-bias', type=str2bool, default=False,
        help='add bias term inner loop')
    parser.add_argument('--use-group-norm', type=str2bool, default=False,
        help='use group norm instead of batch norm')
    
    
    # Optimization
    parser.add_argument('--lr', type=float, default=0.001,
        help='learning rate for the global update')
    parser.add_argument('--grad-clip', type=float, default=0.0,
        help='gradient clipping')
    parser.add_argument('--optimizer-update-interval', type=int, default=1,
        help='number of mini batches after which the optimizer is updated')


    parser.add_argument('--hessian-inverse', type=str2bool, default=False,
        help='for implicit last layer optimization, whether to use \
            hessian to solve linear equation or to use woodbury identity\
            on the hessian inverse')
    
    
    # Dataset
    parser.add_argument('--dataset-path', type=str,
        help='which dataset to use')
    parser.add_argument('--train-batch-size', type=int, default=20,
        help='batch size for training')
    parser.add_argument('--val-batch-size', type=int, default=4,
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
    parser.add_argument('--output-folder', type=str, default='maml',
        help='name of the output folder')
    parser.add_argument('--device', type=str, default='cuda',
        help='set the device (cpu or cuda)')
    parser.add_argument('--optimizer', type=str, default='adam',
        help='optimizer')
    parser.add_argument('--device-number', type=str, default='0',
                        help='gpu device number')
    parser.add_argument('--log-interval', type=int, default=100,
        help='number of batches between tensorboard writes')
    parser.add_argument('--save-interval', type=int, default=1000,
        help='number of batches between model saves')
    parser.add_argument('--eval', action='store_true', default=False,
        help='evaluate model')
    parser.add_argument('--checkpoint', type=str, default='',
        help='path to saved parameters.')
    parser.add_argument('--val-interval', type=int, default=2000,
        help='no. of iterations after which to perform meta-validation.')
    parser.add_argument('--verbose', type=str2bool, default=False,
        help='debugging purposes')

    args = parser.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = args.device_number
    print('GPU number', os.environ["CUDA_VISIBLE_DEVICES"])

    # Create logs and saves folder if they don't exist
    if not os.path.exists('./train_dir'):
        os.makedirs('./train_dir')
    
    # print args
    if args.verbose:
        print('='*10 + ' ARGS ' + '='*10)
        for k, v in sorted(vars(args).items()):
            print('{}: {}'.format(k, v))
        print('='*26)

    main(args)
