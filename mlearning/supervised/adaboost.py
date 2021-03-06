"""
    Adaboost Classifier
    Boosting that makes a strong classifier from a number
    of weak classiffiers in ensemble.
"""
import numpy as np

from dataclasses import dataclass
from typing import Any

from ..helpers.utils.operations import op


class AdaBoost:
    """
        Decision stump [One-level tree] classifier

        Parameters:
        ----------
        n_classifiers: int
            Number of weak classifiers to used
    """

    def __init__(self, n_classifiers):
        self.n_classifiers = n_classifiers
        self.classifiers = []

    def fit(self, X, y):
        """
           Finds best threshold for prediction
        """

        self.n_samples, self.n_feat = X.shape
        self.X, self.y = X, y

        # Init weights to 1/n
        weights = np.full(self.n_samples, 1 / self.n_samples)

        for i in range(self.n_classifiers):
            clf = DecisionStump()
            min_error = float('inf')

            # Find best threshold for y prediction
            for feat_idx in range(self.n_feat):
                feature_val = np.expand_dims(X[:, feat_idx], axis=1)
                uniques = np.unique(feature_val)

                for threshold in uniques:
                    self.p = 1

                    prediction = np.ones(y.shape)
                    # Sample values below index. Label -1
                    prediction[X[:, feat_idx] < threshold] = -1

                    self.error = np.sum(weights[y != prediction])

                    new_min_err = self._reclassify_on_error(
                        min_error)
                    if new_min_err:
                        min_error = self.error
                        clf.polarity = self.p
                        clf.threshold = threshold
                        clf.feature_idx = feat_idx
            clf.aplha = self.approximate_proficiency(min_error)
            self._calculate_weights(clf, weights)
            self.classifiers.append(clf)

    def approximate_proficiency(self, min_error):
        """
            Calculates the value of alpha, used in updating the
            sample weights
        """
        return 0.5 * np.log(
            (1 - min_error) / (min_error + 1e-8))

    def _calculate_weights(self, clf, weights):
        """
            Calculates new weights.
            Lower for misclassified samples, and higher for samples
            correctly classified.
        """
        preds = np.ones(self.y.shape)
        # Index for sample values below threshold
        negtv_idx = self._get_negative_index(clf, self.X)
        preds[negtv_idx] = -1
        weights *= np.exp(-clf.alpha * self.y * preds)

        # Normalize to one
        weights /= np.sum(weights)

    def _reclassify_on_error(self, min_err):
        """
            Flips polarity of samples based on error value
        """
        it_happens = self.error > .5

        if it_happens:
            self.error = 1 - self.error
            self.p = -1

        return False if not self.error < min_err else True

    def predict(self, X, **kwargs):
        """
            Gives the sign of the weighted prefiction
        """
        n_samples = X.shape[0]
        y_pred = np.zeros((n_samples, 1))

        # Label samples in classifiers
        for clf in self.classifiers:
            preds = np.ones(y_pred.shape)  # Initialize predictions as 1
            negative_idx = self._get_negative_index(clf, X)
            preds[negative_idx] = -1
            y_pred += clf.alpha * preds

        y_test = kwargs.get('y_test')
        y_pred = np.sign(y_pred).flatten()

        if np.any(y_test):
            acc = op.rate_accuracy(y_pred, y_test)
            return y_pred, acc
        return y_pred

    def _get_negative_index(self, clf, X):
        """
            Givse indexes of sample values below threshold
        """
        neg_idx = (clf.polarity *
                   X[:, clf.feature_idx] < clf.polarity * clf.threshold)
        return neg_idx


@dataclass
class DecisionStump:
    """
        Weak classifier for Adaboost

        Parameters
        ----------
        polarity: int
            Determines classification of sample as -1 or 1
            from threshold
        aplha: float
            Indicates classifiers accuracy
        feature_idx: int
            Index of feature used in making the classification
        threshold: int
            Threshold value against which feature is measured against
    """
    polarity: int = 1
    alpha: float = .02
    feature_idx: Any = None
    threshold: Any = None
