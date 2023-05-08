import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import scipy.stats as stats
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage, ward, cut_tree
from multiprocess import set_start_method, Pool
from dataclasses import dataclass
from typing import List

from CoexpressionExplorer.models import db, Dataset, DatasetMeta

# Function to import a dataset from disk refrenced in the db.

def load_dataset(Dataset):
    df = pd.read_parquet(Dataset.path)
    print(f"Dataset of shape {df.shape} imported")
    return df
