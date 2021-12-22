import displaying
import load_data
import model_utils
import train_model
import test_model



def run_cw2(train=True, test=True, visualize=True):
    ###############################
    # Load data
    ###############################
    train_path = 'data/train/'
    validation_path = 'data/val/'
    test_path = 'data/test/'
    batch_size = 4
    train_loader, validation_loader, test_loader = load_data.create_data_loaders(train_path=train_path,
                                                                                 validation_path=validation_path,
                                                                                 test_path=test_path,
                                                                                 batch_size=batch_size,
                                                                                 )

    ###############################
    # Train Model
    ###############################
    model_type = 'baseline'  # 'baseline' or 'mlt_hard' or 'mlt_attention' or 'mlt_gscnn'
    model, optimizer, loss_criterion = model_utils.get_model(model_type=model_type)
    if train:
        # Train model
        model = train_model.train_model(model_type=model_type, train_loader=train_loader,
                                        validation_loader=validation_loader,
                                        model=model, optimizer=optimizer, loss_criterion=loss_criterion)
    else:
        # Load model
        model_path = 'model.pth'  # todo: update this as a parameter.
        model = model_utils.load_model(model_path=model_path)

    ###############################
    # Test Model
    ###############################
    if test:
        # Evaluate over testing dataset.
        test_loss, test_metrics = test_model.evaluate_model_on_data(data_loader=test_loader, model=model)

    ###############################
    # Run visualization
    ###############################
    if visualize:
        images, labels, segmentations, bboxes = load_data.take_random_samples(data_loader=test_loader, n_samples=16)
        displaying.visualise_results(model=model, images=images, labels=labels, segmentation=segmentations,
                                     bboxes=bboxes)

    print('CW is done! Well, almost done.')


if __name__ == '__main__':
    run_cw2()