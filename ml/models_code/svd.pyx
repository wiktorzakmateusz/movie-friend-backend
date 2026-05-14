import numpy as np
cimport numpy as cnp
import cython
from numpy import random
from sklearn.model_selection import KFold
from libc.math cimport sqrt, fabs

cdef class SVD():
    cdef public int n_factors, n_epochs, n_users, n_items
    cdef public double global_mean, lr_all, reg_all
    
    cdef public double init_mean, init_std_dev
    cdef public double lr_bu, lr_bi, lr_pu, lr_qi
    cdef public double reg_bu, reg_bi, reg_pu, reg_qi
    
    cdef public object trainset

    cdef double[::1] bu, bi
    cdef double[:, ::1] pu, qi

    def __init__(self, int n_factors=100, int n_epochs=20, double lr_all=.005, double reg_all=.02):
        """
        Args:
            n_factors: int, number of latent factors
            n_epochs: int, number of sgd iterations
            lr_all: double, learning rate for all parameters
            reg_all: double, regularization factor for all parameters
        """
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr_all = lr_all
        self.reg_all = reg_all

        # predefined initialization parameters
        self.init_mean = 0
        self.init_std_dev = 0.1
        self.lr_bu = self.lr_bi = self.lr_pu = self.lr_qi = lr_all
        self.reg_bu = self.reg_bi = self.reg_pu = self.reg_qi = reg_all

    def fit(self, trainset):
        """
        Trains the model
        
        Args:
            trainset: a numpy ndarray with cols: userId, movieId, rating
        """

        self.trainset = trainset

        # extract dimensions and global mean
        self.n_users = int(np.max(trainset[:, 0])) + 1
        self.n_items = int(np.max(trainset[:, 1])) + 1
        self.global_mean = np.mean(trainset[:,2])

        # create a contiguous memory view for cython
        cdef double[:, ::1] train_view = np.ascontiguousarray(trainset, dtype=np.float64)

        # run stochastic gradient descent
        self.sgd(train_view)

        return self

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def sgd(self, double[:, ::1] trainset):
        """
        Performs stochastic gradient descent to optimize factors and biases
        
        Args:
            trainset: double[:, ::1], contiguous memory view of the dataset
        """

        # user biases
        cdef double [::1] bu = np.zeros(self.n_users, dtype=np.double)
        # item biases
        cdef double [::1] bi = np.zeros(self.n_items, dtype=np.double)
        # user factors
        cdef double [:, ::1] pu = random.normal(self.init_mean, self.init_std_dev, size=(self.n_users, self.n_factors))
        # item factors
        cdef double [:, ::1] qi = random.normal(self.init_mean, self.init_std_dev, size=(self.n_items, self.n_factors))

        # initialising temp variables
        cdef int u, i, f
        cdef int n_factors = self.n_factors
        cdef double r, err, dot, puf, qif
        cdef double global_mean = self.global_mean

        cdef double lr_bu = self.lr_bu
        cdef double lr_bi = self.lr_bi
        cdef double lr_pu = self.lr_pu
        cdef double lr_qi = self.lr_qi

        cdef double reg_bu = self.reg_bu
        cdef double reg_bi = self.reg_bi
        cdef double reg_pu = self.reg_pu
        cdef double reg_qi = self.reg_qi

        cdef int num_ratings = trainset.shape[0]
        cdef int current_epoch, j

        # main loop
        for current_epoch in range(self.n_epochs):

            # iterating over all ratings:
            for j in range(num_ratings):
                u = <int>trainset[j, 0]
                i = <int>trainset[j, 1]
                r = trainset[j, 2]
            
                # compute current error
                dot = 0  # <q_i, p_u>
                for f in range(n_factors):
                    dot += qi[i, f] * pu[u, f]
                err = r - (global_mean + bu[u] + bi[i] + dot)

                # update biases
                bu[u] += lr_bu * (err - reg_bu * bu[u])
                bi[i] += lr_bi * (err - reg_bi * bi[i])

                # update factors
                for f in range(n_factors):
                    puf = pu[u, f]
                    qif = qi[i, f]
                    pu[u, f] += lr_pu * (err * qif - reg_pu * puf)
                    qi[i, f] += lr_qi * (err * puf - reg_qi * qif)

        self.bu = bu
        self.bi = bi
        self.pu = pu
        self.qi = qi

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef double estimate(self, int u, int i):
        """
        Predicts the rating for a specific user and item
        
        Args:
            u: int, user id
            i: int, item id
            
        Returns:
            est: double, predicted rating score
        """
        cdef bint known_user = (0 <= u < self.n_users)
        cdef bint known_item = (0 <= i < self.n_items)
        cdef double est = self.global_mean
        cdef int f
        
        # add biases if known
        if known_user: est += self.bu[u]
        if known_item: est += self.bi[i]

        # add dot product of factors if both are known
        if known_user and known_item:
            for f in range(self.n_factors):
                est += self.qi[i, f] * self.pu[u, f]

        return est
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def cross_validation(self, dataset, int n_splits=3):
        """
        Evaluates the model using k-fold cross validation
        
        Args:
            dataset: a numpy ndarray with cols: userId, movieId, rating
            n_splits: int, number of folds for cross validation
            
        Returns:
            rmse: double, root mean squared error
            mae: double, mean absolute error
        """

        cdef double rmse = 0.0, mae = 0.0
        cdef int u, i, sample
        cdef double r, r_hat, error
        cdef double[:, ::1] test_view 

        # initialize k-fold
        kf = KFold(n_splits=n_splits, shuffle=True)

        for train_index, test_index in kf.split(dataset):

            # create splits
            trainset, testset = dataset[train_index], dataset[test_index]

            # train on trainset
            self.fit(trainset)

            # test on testset
            test_view = np.ascontiguousarray(testset, dtype=np.float64)

            for sample in range(test_view.shape[0]):
                u = <int>test_view[sample, 0]
                i = <int>test_view[sample, 1]
                r = test_view[sample, 2]

                # predict rating
                r_hat = self.estimate(u, i)

                # calculate error
                error = (r - r_hat)
                rmse += error*error
                mae += fabs(error)

        # average across dataset size
        rmse = sqrt(rmse / dataset.shape[0])
        mae /= dataset.shape[0]

        return rmse, mae
                
    def save(self, str filepath):
        """
        Saves the model arrays and attributes to a compressed .npz file
        
        Args:
            filepath: str, destination path
        """
        
        # callback if not fitted
        if self.pu is None or self.qi is None:
            raise ValueError("Model is not fitted yet.")

        # saving arrays and scalars
        np.savez_compressed(
            filepath,
            n_factors=self.n_factors,
            n_epochs=self.n_epochs,
            lr_all=self.lr_all,
            reg_all=self.reg_all,
            n_users=self.n_users,
            n_items=self.n_items,
            global_mean=self.global_mean,
            bu=np.asarray(self.bu),
            bi=np.asarray(self.bi),
            pu=np.asarray(self.pu),
            qi=np.asarray(self.qi)
        )

    
    @staticmethod
    def load(str filepath):
        """
        Loads the model from a compressed .npz file
        
        Args:
            filepath: str, source path
            
        Returns:
            model: SVD, the loaded model instance
        """
        
        # load arrays from file
        data = np.load(filepath)
        
        # initialize empty model
        cdef SVD model = SVD(
            n_factors=int(data['n_factors']),
            n_epochs=int(data['n_epochs']),
            lr_all=float(data['lr_all']),
            reg_all=float(data['reg_all'])
        )
        
        # restore scalars
        model.n_users = int(data['n_users'])
        model.n_items = int(data['n_items'])
        model.global_mean = float(data['global_mean'])
        
        # restore arrays
        model.bu = data['bu'].astype(np.double)
        model.bi = data['bi'].astype(np.double)
        model.pu = data['pu'].astype(np.double)
        model.qi = data['qi'].astype(np.double)
        
        return model
