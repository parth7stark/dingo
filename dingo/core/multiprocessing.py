from multiprocessing import Pool
from threadpoolctl import threadpool_limits
import numpy as np
import pandas as pd
from tqdm import tqdm

def apply_func_with_multiprocessing(
    func: callable, theta: pd.DataFrame, num_processes: int = 1
) -> np.ndarray:
    """
    Call func(theta.iloc[idx].to_dict()) with multiprocessing.

    Parameters
    ----------
    func: callable

    theta : pd.DataFrame
        Parameters with multiple rows, evaluate func for each row.
    num_processes : int
        Number of parallel processes to use.

    Returns
    -------
    result: np.ndarray
        Output array, where result[idx] = func(theta.iloc[idx].to_dict())
    """
    with threadpool_limits(limits=1, user_api="blas"):

        # Generator object for theta rows. For idx this yields row idx of
        # theta dataframe, converted to dict, ready to be passed to
        # self.log_likelihood.
        theta_generator = (d[1].to_dict() for d in theta.iterrows())

        if num_processes > 1:
            with Pool(processes=num_processes) as pool:
                # result = pool.map(func, theta_generator)
                result = list(tqdm(pool.imap(func, theta_generator), total=len(theta), desc="MultiProcessing"))

        else:
            # For a single process, you can use tqdm directly with map
            # result = list(map(func, theta_generator))
            result =  list(tqdm(map(func, theta_generator), total=len(theta), desc="Processing"))

    return np.array(result)
