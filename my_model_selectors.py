import math
import statistics
import warnings

import numpy as np
from hmmlearn.hmm import GaussianHMM
from sklearn.model_selection import KFold
from asl_utils import combine_sequences


class ModelSelector(object):
    '''
    base class for model selection (strategy design pattern)
    '''

    def __init__(self, all_word_sequences: dict, all_word_Xlengths: dict, this_word: str,
                 n_constant=3,
                 min_n_components=2, max_n_components=10,
                 random_state=14, verbose=False):
        self.words = all_word_sequences
        self.hwords = all_word_Xlengths
        self.sequences = all_word_sequences[this_word]
        self.X, self.lengths = all_word_Xlengths[this_word]
        self.this_word = this_word
        self.n_constant = n_constant
        self.min_n_components = min_n_components
        self.max_n_components = max_n_components
        self.random_state = random_state
        self.verbose = verbose

    def select(self):
        raise NotImplementedError

    def base_model(self, num_states):
        # with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        # warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            hmm_model = GaussianHMM(n_components=num_states, covariance_type="diag", n_iter=1000,
                                    random_state=self.random_state, verbose=False).fit(self.X, self.lengths)
            if self.verbose:
                print("model created for {} with {} states".format(self.this_word, num_states))
            return hmm_model
        except:
            if self.verbose:
                print("failure on {} with {} states".format(self.this_word, num_states))
            return None


class SelectorConstant(ModelSelector):
    """ select the model with value self.n_constant

    """

    def select(self):
        """ select based on n_constant value

        :return: GaussianHMM object
        """
        best_num_components = self.n_constant
        return self.base_model(best_num_components)


class SelectorBIC(ModelSelector):
    """ select the model with the lowest Bayesian Information Criterion(BIC) score

    http://www2.imm.dtu.dk/courses/02433/doc/ch6_slides.pdf
    Bayesian information criteria: BIC = -2 * logL + p * logN
    """

    def select(self):
        """ select the best model for self.this_word based on
        BIC score for n between self.min_n_components and self.max_n_components

        :return: GaussianHMM object
        """
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # TODO implement model selection based on BIC scores
        # raise NotImplementedError
        record = float("inf")

        min_seq = min([len(seq) for seq in self.sequences])
        self.max_n_components = min (self.max_n_components, min_seq)

        hmm_model = self.base_model(self.n_constant)
        for num in range(self.min_n_components,self.max_n_components+1,1):
            #print(num)
            try:
                model = GaussianHMM(n_components= num, n_iter=1000).fit(self.X, self.lengths)
                logL = model.score(self.X, self.lengths)
                # p is the number of free parameters, N is the number of data points
                p = num*num + 2* num* len(self.X[0]) -1
                BIC = -2* logL + p * np.log(len(self.X))
                if BIC < record:
                    record = BIC
                    hmm_model = model
            except:
                continue
                # print("failure on {} with {} states".format(self.this_word, num))
        return hmm_model

class SelectorDIC(ModelSelector):
    ''' select best model based on Discriminative Information Criterion

    Biem, Alain. "A model selection criterion for classification: Application to hmm topology optimization."
    Document Analysis and Recognition, 2003. Proceedings. Seventh International Conference on. IEEE, 2003.
    http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.58.6208&rep=rep1&type=pdf
    DIC = log(P(X(i)) - 1/(M-1)SUM(log(P(X(all but i))
    '''

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)

        # TODO implement model selection based on DIC scores
        # raise NotImplementedError
        best_n = self.random_state
        best_DIC = float("-inf")
        best_model = None
        n_components = n

        for n in range(self.min_n_components,self.max_n_components+1):
            #print(num)
            try:
                model = GaussianHMM(n, n_iter=1000).fit(self.X, self.lengths)
                original_prob = model.score(self.X,self.lengths)

                sum_prob_others = 0.0

                for word in self.words:
                    if word == self.this_word:
                        continue

                    other_x, other_lengths = self.hwords[word]
                    logL = model.score(other_x,other_lengths)
                    sum_prob_others += logL

                avg_prob_others = sum_prob_others/len(self.words-1)
                DIC = original_prob - avg_prob_others
                print('num_comp: {} for DIC:'.format(n,DIC))

                if DIC > best_DIC:
                    best_DIC = DIC
                    best_n = n
            except:
                pass

        best_model = GaussianHMM(best_n, n_iter=1000).fir(self.X,self.lengths)
                # print("failure on {} with {} states".format(self.this_word, num))
        return best_model

class SelectorCV(ModelSelector):
    ''' select best model based on average log Likelihood of cross-validation folds

    '''

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # TODO implement model selection using CV
        # raise NotImplementedError
        record = float("-inf")

        min_seq = min([len(seq) for seq in self.sequences])
        self.max_n_components = min (self.max_n_components, min_seq)
        hmm_model = self.base_model(self.n_constant)
        if len(self.sequences) == 1:
            return hmm_model
        elif len(self.sequences) == 2:
            split_method = KFold(n_splits=2)
            #self.max_n_components = 3
        else:
            split_method = KFold(n_splits=3,random_state=self.random_state)


        for num in range(self.min_n_components,self.max_n_components+1,1):
            #print(num)
            logL = 0
            cnt = 0

            for cv_train_idx, cv_test_idx in split_method.split(self.sequences):
                #print("Train fold indices:{} Test fold indices:{}".format(cv_train_idx, cv_test_idx))  # view indices of the folds
                X, lengths = combine_sequences(cv_train_idx,self.sequences)
                try:
                    model = GaussianHMM(n_components= num, n_iter=1000).fit(X, lengths)
                    X, lengths = combine_sequences(cv_test_idx,self.sequences)
                    logL += model.score(X, lengths)
                except:
                    continue
                    #print("failure on {} with {} states".format(self.this_word, num))
            if cnt> 0 and logL/cnt > record:
                record = logL
                hmm_model = model
        return hmm_model
