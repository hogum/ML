"""
    This module contains the restricted Boltzmann Machine model
"""

import numpy as np

import progressbar

from ..helpers.utils.display import progress_bar_widgets
from ..helpers.utils.data_utils import data_helper
from ..helpers.deep_learning.activation_functions import Sigmoid


class RBM:
    """
        Bernoulli Restricted Boltzmann Machine

        Parameters:
        ------------
        hidden: int
            No of processing nodes in the hidden layer
        l_rate: float
            Step length used in updating weights
        batch_size: int
            Size of the mini-batch used to calculate each weight update
        iter: int
            Number of training iterations to tune the weight for

    """

    def __init__(self, hidden=128, l_rate=0.1, batch_size=10, iters=100):
        self.no_of_iters = iters
        self.batch_size = batch_size
        self.learning_rate = l_rate
        self.hidden = hidden
        self.training_errs = []
        self.training_reconstructions = []
        self.progressbar = progressbar.ProgressBar(
            widgets=progress_bar_widgets)

    def init_weights(self, X):
        """
            Initializes the weight inputs
        """
        n_visible = X.shape[1]
        self.weights = np.random.normal(
            scale=0.1, size=(n_visible, self.hidden))
        self.v_ = np.zeros(n_visible)
        self.h_ = np.zeros(self.hidden)

    def fit(self, X, y=None):
        """
            Trains the model through Contrastive Divergence
        """
        self.init_weights(X)

        for _ in self.progressbar(range(self.no_of_iters)):
            batch_errs = []
            for batch in data_helper.iterate_over_batch(
                    X, batch_size=self.batch_size):
                # + Phase
                positive_hidden = sigmoid(batch.dot(self.weights) + self.h_)
                hidden_states = self.sample(positive_hidden)
                positive_associations = batch.T.dot(positive_hidden)

                # - Phase
                neg_visible = sigmoid(
                    hidden_states.dot(self.weights.T) + self.v_)
                neg_visible = self.sample(neg_visible)
                neg_hidden = sigmoid(neg_visible.dot(self.weights) + self.h_)
                neg_associations = neg_visible.T.dot(neg_hidden)

                self.weights += self.learning_rate * \
                    (positive_associations - neg_associations)
                self.h_ += self.learning_rate * \
                    (positive_hidden.sum(axis=0) - neg_hidden.sum(axis=0))
                self.v_ += self.learning_rate * \
                    (batch.sum(axis=0) - neg_visible.sum(axis=0))

                batch_errs.append(np.mean((batch - neg_visible)**2))
            self.training_errs.append(np.mean(batch_errs))

            # Reconstruct a batch of images from training set
            idx = np.random.choice(range(X.shape[0]), self.batch_size)
            self.training_reconstructions.append(self.reconstruct(X[idx]))

    def sample(self, X):
        """
            Selected input to feed back into the network
        """
        return X > np.random.random_sample(X.shape)

    def reconstruct(self, X):
        """
           Reconstructs images and updates based on the difference
           between the calculated and the actual image projections
        """
        pos_hidden = sigmoid(X.dot(self.weights) + self.h_)
        hidden_states = self.sample(pos_hidden)
        neg_visible = sigmoid(hidden_states.dot(self.weights.T) + self.v_)

        return neg_visible


sigmoid = Sigmoid()
