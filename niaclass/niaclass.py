from pandas.api.types import is_numeric_dtype
from niaclass.feature_info import _FeatureInfo
from niaclass.rule import _Rule
from NiaPy.task import StoppingTask
from NiaPy.benchmarks import Benchmark
from NiaPy.algorithms.utility import AlgorithmUtility
import numpy as np

__all__ = [
    'NiaClass'
]

class NiaClass:
    r"""Implementation of NiaClass classifier.
    
    Date:
        2021

    Author:
        Luka Pečnik

    Reference:
        The implementation is based on the following article:
        Iztok Fister Jr., Iztok Fister, Dušan Fister, Grega Vrbančič, Vili Podgorelec. On the potential of the nature-inspired algorithms for pure binary classification. In. Computational science - ICCS 2020 : 20th International Conference, Proceedings. Part V. Cham: Springer, pp. 18-28. Lecture notes in computer science, 12141, 2020

    License:
        MIT

    Attributes:
        TODO
    """

    def __init__(self, pop_size=90, num_evals=5000, algo='FireflyAlgorithm', **kwargs):
        r"""Initialize instance of NiaClass.

        Arguments:
            TODO
        """
        self.__pop_size = pop_size
        self.__num_evals = num_evals
        self.__algo = algo

    def __split_train_test(self, x, y):
        indices = np.arange(x.shape[0])
        num_training_instances = int(0.8 * x.shape[0])
        np.random.shuffle(indices)
        train_indices = indices[:num_training_instances]
        test_indices = indices[num_training_instances:]

        x_train, x_test = x.iloc[train_indices], x.iloc[test_indices]
        y_train, y_test = y.iloc[train_indices], y.iloc[test_indices]

        return x_train, y_train, x_test, y_test
    
    def fit(self, x, y):
        r"""Fit NiaClass.

        Arguments:
            x (pandas.core.frame.DataFrame): n samples to classify.
            y (pandas.core.series.Series): n classes of the samples in the x array.

        Returns:
            None
        """
        num_of_classes = y.nunique()
        feats = []

        for col in x:
            if is_numeric_dtype(x[col]):
                feats.append(_FeatureInfo(1, None, x[col].min(), x[col].max()))
            else:
                feats.append(_FeatureInfo(0, x[col].unique(), None, None))
        
        D = 1 # 1 for control value that threshold is compared to.
        for f in feats:
            if f.dtype == 1:
                """
                * 1 for threshold that determines if the definite feature belongs to the rule or not.
                * 2 for min and max mapping for each class (num_of_classes).
                """
                D += 1 + 2 * num_of_classes
            else:
                """
                * 1 for threshold that determines if the definite feature belongs to the rule or not
                """
                D += 1 + num_of_classes
        
        algo = AlgorithmUtility().get_algorithm(self.__algo)
        algo.NP = self.__pop_size

        benchmark = _NiaClassBenchmark(feats, num_of_classes, *self.__split_train_test(x, y))
        task = StoppingTask(
            D=D,
            nFES=self.__num_evals,
            benchmark=benchmark
        )
        algo.run(task)

    def predict(self, x, **kwargs):
        r"""Predict class for each sample (row) in x.

        Arguments:
            x (pandas.core.frame.DataFrame): n samples to classify.

        Returns:
            pandas.core.series.Series: n predicted classes.
        """
        return None

class _NiaClassBenchmark(Benchmark):
    def __init__(self, features, num_of_classes, x_train, y_train, x_test, y_test):
        Benchmark.__init__(self, 0.0, 1.0)
        self.__features = features
        self.__num_of_classes = num_of_classes
        self.__x_train = x_train
        self.__y_train = y_train
        self.__x_test = x_test
        self.__y_test = y_test

    def __get_bin_index(self, value, number_of_bins):
        """Gets index of value's bin. Value must be between 0.0 and 1.0.

        Arguments:
            value (float): Value to put into bin.
            number_of_bins (uint): Number of bins on the interval [0.0, 1.0].
        
        Returns:
            uint: Calculated index.
        """
        bin_index = np.int(np.floor(value / (1.0 / number_of_bins)))
        if bin_index >= number_of_bins:
            bin_index -= 1
        return bin_index
    
    def __build_rules(self, sol):
        classes_rules = [[] for i in range(self.__num_of_classes)]
        
        sol_ind = 0
        for f in self.__features:
            current_feature_threshold = sol[sol_ind]
            sol_ind += 1
            for i in range(self.__num_of_classes):
                if current_feature_threshold >= sol[-1]:
                    if f.dtype == 1:
                        val1 = sol[sol_ind] * f.max + f.min
                        val2 = sol[sol_ind + 1] * f.max + f.min
                        (val1, val2) = (val2, val1) if val2 < val1 else (val1, val2)

                        classes_rules[i].append(_Rule(None, val1, val2))
                        sol_ind += 2
                    else:
                        classes_rules[i].append(_Rule(f.values[self.__get_bin_index(sol[sol_ind + 1], len(f.values))], None, None))
                        sol_ind += 1
                else:
                    if f.dtype == 1:
                        sol_ind += 2
                    else:
                        sol_ind += 1
                    classes_rules[i].append(None)
        
        return classes_rules

    def function(self):
        def evaluate(D, sol):
            val = 0.0

            classes_rules = self.__build_rules(sol)

            return val
        return evaluate
