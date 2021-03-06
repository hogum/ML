"""
    Deep Convolutional Generative Adversarial Network
"""

from ..helpers.deep_learning.network import Neural_Network
from ..helpers.deep_learning.loss import CrossEntropyLoss
from ..helpers.deep_learning.layers import (
    ConvolutionTwoD, Activation, DropOut, BatchNormalization, Dense, Flatten,
    ZeroPadding2D, Reshape, UpSampling2D)
from ..deep_learning.grad_optimizers import Adam

from ..helpers.utils.display import progress_bar_widgets

import numpy as np
from matplotlib import pyplot as plt

import progressbar


class DCGAN:
    """
            Models a Deep Convolutional Generative Adversarial Network

    """

    def __init__(self, optimizer=Adam, loss_function=CrossEntropyLoss):
        self.image_rows = 28
        self.image_cols = 28
        self.channels = 1
        self.latent_dims = 100
        self.img_shape = (self.channels, self.image_rows, self.image_cols)

        self.pgrbar = progressbar.ProgressBar(widgets=progress_bar_widgets)

        optimizer = optimizer(learning_rate=0.0002, beta1=.5)

        self.discriminator = self.build_discriminator(
            optimizer, loss_function)
        self.gen = self.build_gen(optimizer, loss_function)
        self.combined = Neural_Network(optimizer, loss_function)

        self.extend_layers()
        self.summarize()

    def build_discriminator(self, optimizer, loss_function
                            ):
        """
            Creates the network discriminator
        """
        model = Neural_Network(optimizer=optimizer, loss=loss_function)

        model.add_layer(ConvolutionTwoD(no_of_filters=32,
                                        filter_shape=(3, 3),
                                        stride=2, input_shape=self.img_shape))
        model.add_layer(Activation('leaky_relu'))
        model.add_layer(DropOut(p=.25))
        model.add_layer(ConvolutionTwoD(64, filter_shape=(3, 3), stride=2))
        model.add_layer(ZeroPadding2D(padding=((0, 1), (0, 1))))
        model.add_layer(Activation('leaky_relu'))
        model.add_layer(DropOut(.25))

        model.add_layer(BatchNormalization(momentum=.8))
        model.add_layer(ConvolutionTwoD(128,
                                        filter_shape=(3, 3), stride=2))
        model.add_layer(Activation('leaky_relu'))
        model.add_layer(DropOut(0.25))

        model.add_layer(BatchNormalization(momentum=.8))
        model.add_layer(ConvolutionTwoD(256, filter_shape=(3, 3),
                                        stride=1))
        model.add_layer(Activation('leaky_relu'))
        model.add_layer(DropOut(0.25))
        model.add_layer(Flatten())
        model.add_layer(Dense(units=2))
        model.add_layer(Activation('softmax'))

        return model

    def extend_layers(self):
        """
            Combines the model generator and discriminator layers
        """

        layers = self.gen.input_layers + self.discriminator.input_layers
        self.combined.input_layers += layers

    def summarize(self):
        """
            Displays model details
        """
        self.gen.show_model_details('Generator')
        self.discriminator.show_model_details('Discriminator')

    def build_gen(self, optimizer, loss_function):
        """
            Builds the model discriminator
        """

        model = Neural_Network(optimizer=optimizer, loss=loss_function)

        model.add_layer(Dense(units=128 * 7 * 7, input_shape=(100,)))
        model.add_layer(Activation('leaky_relu'))
        model.add_layer(Reshape((128, 7, 7)))
        model.add_layer(BatchNormalization(momentum=0.8))
        model.add_layer(UpSampling2D())

        model.add_layer(ConvolutionTwoD(
            no_of_filters=128, filter_shape=(3, 3)))
        model.add_layer(Activation('leaky_relu'))
        model.add_layer(BatchNormalization(momentum=0.8))
        model.add_layer(UpSampling2D())

        model.add_layer(ConvolutionTwoD(64, filter_shape=(3, 3)))
        model.add_layer(Activation('leaky_relu'))
        model.add_layer(BatchNormalization(momentum=0.8))
        model.add_layer(ConvolutionTwoD(no_of_filters=1,
                                        filter_shape=(3, 3)))
        model.add_layer(Activation('tanh'))

        return model

    def train(self, X, y, epochs, batch_size=128, save_interval=50):
        """
            Trains the model
        """

        X = X.reshape((-1, ) + self.img_shape)
        self.X = (X.astype(np.float32) - 127.5) / 127.5
        self.y = y

        for epoch in range(epochs):
            self.train_discriminator(batch_size // 2)
            self.train_gen(batch_size)
            disp = f'{epoch}  [Discriminator: loss -' + \
                f' {self.d_loss:.4f}] acc - {self.d_acc * 100:.2f}]' + \
                f' [Generator: loss - {self.g_loss:.4f},' + \
                f'  acc - {self.g_acc * 100:.2f}'
            print(disp)

            if not epoch % save_interval:
                self.save(epoch)

    def train_discriminator(self, half_batch):
        """
            Trains the discriminator
        """
        self.discriminator.set_trainable(True)

        # Random half batch of images
        idx = np.random.randint(0, self.X.shape[0], half_batch)
        images = self.X[idx]

        # Sample noise for use as generator input
        noise = np.random.normal(size=(half_batch, 100))

        # Generate a half batch of images
        gen_images = self.gen.make_prediction(noise)

        valid = np.concatenate(
            (np.ones((half_batch, 1)), np.zeros((half_batch, 1))), axis=1)
        fake = np.concatenate(
            (np.zeros((half_batch, 1)), np.ones((half_batch, 1))), axis=1)

        loss_real, acc_real = self.discriminator.train_on_batch(images, valid)
        loss_fake, acc_fake = self.discriminator.train_on_batch(
            gen_images, fake)

        self.d_loss = (loss_real + loss_fake) / 2
        self.d_acc = (acc_fake + acc_real) / 2

    def train_gen(self, batch_size):
        """
            Finds the loss and accuracy of the combined model
        """

        self.discriminator.set_trainable(False)
        noise = np.random.normal(size=(batch_size, self.latent_dims))
        valid = np.concatenate(
            (np.ones((batch_size, 1)),
             np.zeros((batch_size, 1))),
            axis=1)

        self.g_loss, self.g_acc = self.combined.train_on_batch(noise, valid)

    def save(self, epoch):
        """
            Saves the generated images
        """
        row, col = 5, 5
        noise = np.random.uniform(0, 1, (row * col, 100))

        gen_images = self.gen.make_prediction(noise)

        # Rescale images [0 - 1] from [-1 - 1]
        gen_images = 0.5 * (gen_images + 1)
        fig, axis = plt.subplots(row, col)
        plt.suptitle('Deep Convolutional Generative Adversarial Network')

        count = 0
        for i in range(row):
            for j in range(col):
                axis[i, j].imshow(gen_images[count, 0, :, :], cmap='gray')
                axis[i, j].axis('off')
                count += 1
        fig.savefig(f'mnist_{epoch}.png')
        plt.close()
