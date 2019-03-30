"""
    This module contains functions that help in sending
    outputs on data configuration and model progress
    to the command line.
"""

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import numpy as np

import progressbar

from .operations import get_matrix_covariance

progress_bar_widgets = [
    'Training: ', progressbar.Percentage(),
    ' ',
    progressbar.Bar(marker='#',
                    left='[',
                    right=']'
                    ),
    ' ',
    progressbar.ETA(), ' '
]


class Plot:
    """
        A data plot display class
    """

    def __init__(self):
        self.cmap = plt.get_cmap('viridis')

    def transform(self, X, dimension):
        """
            Transforms a given layer to s specified dimension
        """

        covariance = get_matrix_covariance(X)
        eigen_values, eigen_vectors = np.linalg.eig(covariance)

        # Sort eigen values ande eigen_vectors by largest eigen values
        index = eigen_values.argsort()[::-1]
        eigen_values = eigen_values[index][:dimension]
        eigen_vectors = np.atleast_1d(eigen_vectors[:, index])[:, :dimension]

        # Project onto principal components
        transformed_X = X.dot(eigen_vectors)

        return transformed_X

    def plot_regression(self, lines, title, axis_labels=None,
                        mse=None, scatter=None,
                        legend={'type': 'lines', 'location': 'lower right'}):
        """
            Helps in plotting of a regression fit
        """
        if scatter:
            scatter_plots = []
            scatter_labels = []

            for item in scatter:
                scatter_plots += [plt.scatter(item['x'],
                                              item['y'], color=item['color'],
                                              s=item['size'])]
                scatter_labels += [item['label']]
            scatter_plots = tuple(scatter_plots)
            scatter_labels = tuple(scatter_labels)

        for line in lines:
            line = plt.plot(line['x'], line['y'],
                            color=line['color'],
                            linewidth=line['width'],
                            label=line['label'])
        plt.suptitle(title)
        if mse:
            plt.suptitle('Mean Sq. Error: {mse}', fontsize=9)
        if axis_labels:
            plt.xlabel(axis_labels['x'])
            plt.ylabel(axis_labels['y'])

        if legend['type'] == 'lines':
            plt.legend(loc='lower_left')
        elif scatter and legend['type'] == 'scatter':
            plt.legend(scatter_plots, scatter_labels, loc=legend['location'])

        plt.show()

    def plot_in_two_d(self, X, y=None, title=None, accuracy=0,
                      legend_labels=None):
        """
            PLots the dataset x and y labels iin Two D using PCA
        """
        class_distr = []
        X_transformed = self._X_transformed(X, dims=2)
        x_one = X_transformed[:, 0]
        x_two = X_transformed[:, 1]

        y = np.array(y).astype(int)
        colors = [self.cmap(i) for i in np.linspace(0, 1, len(np.unique(y)))]

        # Plot class distrbutions
        for num, item in enumerate(np.unique(y)):
            x_one_ = x_one[y == 1]
            x_two_ = x_two[y == 1]
            y_ = y[y == 1]
            class_distr.append(plt.scatter(x_one_, x_two_, color=colors[num]))

        # Plot legend
        if legend_labels:
            plt.legend(class_distr, legend_labels, loc=1)
        # Plot accuracy
        if title and accuracy:
            perc = 100 * accuracy
            plt.suptitle(title)
            plt.title(f"Accuracy: {perc}", fontsize=10)
        elif not accuracy and title:
            plt.title(title)

        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 2')
        plt.show()

    def plot_in_3d(self, X, y):
        """
            Plots the dataset X and y labels in 3 dimensions
            using Principal Component Analysis
        """
        X_transformed = self.transform(X, dimension=3)

        x_one = X_transformed[:, 0]
        x_two = X_transformed[:, 1]
        x_three = X_transformed[:, 2]
        fig = plt.figure()
        axs = fig.add_subplot(111, projection='3d')
        axs.scatter(x_one, x_two, x_three, c=y)
        plt.show()
