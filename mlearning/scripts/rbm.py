"""
    Restricted Boltzman's Machine [Energy based model]
"""

from sklearn.datasets import fetch_mldata
import numpy as np
import matplotlib.pyplot as plt

from ..unsupervised.restricted_boltzmann_machine import RBM


def start_restricted_bolz_machine():
    """
        Drives the restricted boltzmann machine network
    """

    mnist = fetch_mldata('MNIST original')
    X = mnist.data / 255
    y = mnist.target

    # Select samples of digit 2
    X = X[y == 2]

    # Limit dataset to 500 samples
    idx = np.random.choice(range(X.shape[0]), size=500, replace=False)
    X = X[idx]

    rbm = RBM(hidden=50, iters=200, batch_size=25, l_rate=0.001)
    rbm.fit(X)

    training, = plt.plot(range(len(rbm.training_errs)),
                         rbm.training_errs, label='Training Error')
    plt.legend(handles=[training])
    plt.title('Error Plot')
    plt.ylabel('Error')
    plt.xlabel('Iterations')
    plt.show()
    save_images(rbm, iter_='First')
    save_images(rbm, iter_='Last')


def save_images(rbm, iter_=''):
    """
        Saves the generated output images
    """
    fig, axis = plt.subplots(5, 5)
    plt.suptitle(f'Restricted Boltzmann Machine - {iter_} Iteration')
    idx = 0 if iter_ == 'First' else -1

    cnt = 0
    for i in range(5):
        for j in range(5):
            axis[i, j].imshow(rbm.training_reconstructions[idx][
                              cnt].reshape((28, 28)), cmap='gray')
            axis[i, j].axis('off')
            cnt += 1
    fig.savefig(f'{iter_.lower()}_iter.png')
    plt.close()
