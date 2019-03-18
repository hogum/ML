"""
    This module contains the network model
    layers.
"""
import numpy as np
import copy
import math


class Layer:
    """
        Parent class layer model. Only contains methods common
        to impemented layer models and does not suffice
        to create a layer.
    """

    def set_input_shape(self, shape):
        """
            Sets the input shape expected of the layer
            for the forward pass
        """
        self.input_shape = shape

    def get_name(self):
        """
            Returns the name of the layer. Thiss is represented by
            the class instance holding the layer.
        """
        return self.__class__.__name__

    @classmethod
    def reshape_col_to_image(cls,
                             cols, imgs_shape, fltr_shape,
                             stride, output_shape=True):
        """
            Changes shape of the input layer from column to image

        """
        batch_size, channels, height, width = imgs_shape
        pad_h, pad_w = cls.get_padding(fltr_shape, output_shape)

        padded_h = height + np.sum(pad_h)
        padded_w = width + np.sum(pad_w)
        padded_imgs = np.empty((batch_size, channels, padded_h, padded_w))

        # Calculate indices for dot product between weights
        # and images

        ind1, ind2, ind3 = get_img_cols_indices(
            imgs_shape, fltr_shape, (pad_h, pad_w), stride)

        cols_reshaped = cols.reshape(channels * np.product(fltr_shape))
        cols_reshaped = cols_reshaped.transpose(2, 0, 1)

        # Add column content to images at the indeces
        np.add.at(padded_imgs, (slice(None), ind1, ind2, ind3), cols_reshaped)

        # Image without padding
        return padded_imgs[:, :, pad_h[0]:height +
                           pad_h[0], pad_w[0]:width + pad_w[0]]

    @classmethod
    def get_padding(cls, fltr_shape, output_shape):
        """
            Determines the padding of the ouput height and width
        """
        if not output_shape:
            return (0, 0), (0, 0)
        flt_height, flt_width = fltr_shape

        # Ref
        # output_height = (height + padd_h - filter_height) / stride + 1
        # output_height = height # Stride = 1

        padd_ht_a = int(math.floor((flt_height - 1) / 2))
        padd_ht_b = int(math.ceil((flt_height - 1) / 2))
        padd_wt_a = int(math.floor((flt_width - 1) / 2))
        padd_wt_b = int(math.ceil((flt_width - 1) / 2))

        return (padd_ht_a, padd_ht_b), (padd_wt_a, padd_wt_b)

    def reshape_image_to_col(cls, images, fltr_shape, stride,
                             output_shape=True):
        """
            Changes shape of the input layer from image to column
        """
        fltr_height, fltr_width = fltr_shape
        pad_h, pad_w = cls.get_padding(fltr_shape, output_shape)

        padded_imgs = np.pad(
            images, ((0, 0), (0, 0), pad_h, pad_w), mode='constant')

        # Indices to apply dot product between weights and image
        ind_a, ind_b, ind_c = get_img_cols_indices(
            images.shape, fltr_shape, (pad_h, pad_w), stride)

        # Retrieve image content at these images
        cols = padded_imgs[:, ind_a, ind_b, ind_c]
        channels = images.shape[1]

        # Reshape content to column shape
        cols_reshaped = cols.transpose(1, 2, 0).reshape(
            fltr_height * fltr_width * channels, -1)

        return cols_reshaped


class ConvolutionTwoD(Layer):
    """
        A class that models a 2D data layer
        Inherits Layer
        Parameters:
        ______----_______-----_________
        no_of_filters: int
            Number of filters to convolve over the input matrix. Represents
            the number of channels of the output shape.
        filter_shape: tuple
            Holds the filter height and width
                e.g (filter_height, filter_width)
        input_shape: tuple
            The expected shape of the input layer. Requires to be specified
            for the  first layer of the network.
                e.g (batch_size, channels, width, height)
        padding: boolean
            True - output height and width matches input height and width
            False - output without padding
        stride: int
            Step size of the filters during convolution over the input

    """

    def __init__(self, no_of_filters, filter_shape,
                 input_shape, padding=False, stride=1, trainable=True):
        self.no_of_filters = no_of_filters
        self.filter_shape = filter_shape
        self.input_shape = input_shape
        self.padding = padding
        self.stride = stride
        self.trainable = trainable

    def init_weights(self, optimizer):
        """
            Initializes the input weights
        """
        fltr_height, fltr_width = self.filter_shape
        channels = self.input_shape[0]
        limit = 1 / pow(np.prod(
            self.filter_shape),
            .5)
        self.weight_ = np.random.uniform(-limit,
                                         limit,
                                         size=(self.no_of_filters,
                                               channels,
                                               fltr_height,
                                               fltr_width)
                                         )
        self.weight_out = np.zeros((self.no_of_filters, 1))
        self.optimized_w = copy.copy(optimizer)
        self.optimized_w_out = copy.copy(optimizer)

    def forward_pass(self, X, training=True):
        """
            Propagates input data through the network to
            get an output prediction
        """
        self.input_layer = X
        batch_size, channels, heigt, width = X.shape

        # For dot product between input and weights,
        # change image shape to column shape
        self.X_col = reshape_image_to_col(
            X, self.filter_shape,
            stride=self.stride,
            output_shape=self.padding)

        # Reshape weight shape to column
        self.W_col = self.weight_.reshape((self.no_of_filters, -1))
        output = self.W_col.dot(self.X_col) + self.weight_out

        # Reshape output to: no_of_filters, height, width, and batch size
        output = output.reshape(self.output_shape() + (batch_size, ))

        # Redistribute axes to bring batch size first
        return output.transpose(3, 0, 1, 2)

    def backward_pass(self, grad):
        """
            Parameter:
                grad: accumulated gradient
            ____________________________________
            Propagates the accumulated gradient backwards.
            -> It calculates the gradient of a loss function with respect
               to all the weights in the network.

        """
        # Reshape accumulated grad to column shape
        accumulated_grad = grad.transpose(
            1, 2, 3, 0).reshape(self.no_of_filters, -1)

        if self.trainable:
            # Find the dot product of the column-shaped accumulated grad
            # and column shape layer.
            # This will determine the grad at the layer w.r.t layer weights

            grad_weight = accumulated_grad.dot(
                self.X_col.T).reshape(self.weight_.shape)

            # Gradient w.r.t the bias sums
            grad_w_out = np.sum(grad, axis=1, keepdims=True)

            # Update layer weights
            self.weight_ = self.optimized_w.update(self.weight_, grad_weight)
            self.weight_out = self.optimized_w_out.update(
                self.weight_out, grad_w_out)

        # Find gradient to propage back to previous layer
        accumulated_grad = self.W_col.T.dot(accumulated_grad)

        accumulated_grad = reshape_col_to_image(accumulated_grad,
                                                self.input_layer.shape,
                                                self.filter_shape,
                                                stride=self.stride,
                                                output_shape=self.padding)
        return accumulated_grad

    def output_shape(self):
        """
            Gives the shape of the output returned by the forward pass
        """
        channels, height, width = self.input_shape
        padd_ht, padd_wt = get_padding(
            self.filter_shape, output_shape=self.padding)
        output_height = (height + np.sum(padd_ht) -
                         self.filter_shape[0]) / self.stride + 1
        output_width = (width + np.sum(padd_wt) -
                        self.filter_shape[1]) / self.stride + 1
        return self.no_of_filters, int(output_height), int(output_width)

    def paramitize(self):
        """
            Returns the number of trainable parameters used by the layer
        """
        return np.prod(self.weight_.shape)
        + np.prod(self.weight_out.shape)
