import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import scipy.stats as stats
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage, ward, cut_tree
from multiprocess import set_start_method, Pool
from dataclasses import dataclass
from typing import List
from sqlalchemy import select, insert, update
from sqlalchemy.orm import joinedload, selectinload

from CoexpressionExplorer.models import db, Dataset, DatasetMeta, SubclustGenes, Gene, DatasetSubsample


class CoExDataset():
    """Takes a db Dataset object and returns an pbject containing the pandas expression dataframe and pandas metadata dataframe."""
    def __init__(self, dataset_inst) -> None:
        self.df = load_dataset(dataset_inst.id)
        self.dataset = dataset_inst
        self.metadata = load_dataset_metadata(dataset_inst.id)


# Function to import a dataset from disk referenced in the db.
def load_dataset(dataset_id=None, sample_names=None):
    if dataset_id is not None:
        dataset = db.session.query(Dataset).where(Dataset.id == dataset_id).first()
    else:
        raise Exception("You must supply a dataset id")
    df = pd.read_parquet(dataset.path)
    if sample_names is not None:
        df = df[sample_names]
    return df


def load_dataset_metadata(dataset_id=None):
    if dataset_id is not None:
        metaQ = (db.session.query(Dataset, DatasetMeta)
                 .join(Dataset.dataset_metadata)
                 .where(Dataset.id == dataset_id)
                 .order_by(Dataset.id, DatasetMeta.path)
                 .first())
    else:
        raise Exception("You must supply a dataset id")
    metadata = pd.read_parquet(metaQ.DatasetMeta.path)
    return metadata


def filterByVar(df,gene_number):
        corGeneNumber = min([gene_number,df.shape[0]-1])
        df_var = df.var(axis=1)
        cutValue = df_var.sort_values(ascending=False)[corGeneNumber]
        crop_index = df.index.values[df_var > cutValue]
        return crop_index


def makeCorrDist(df):
    correlationDist = pdist(df, metric = "correlation")
    print("Calculated correlation distance matrix")
    return correlationDist
        
    
def clusterByGenes(corDist,linkageMethod="average", dist=0.2):
    ''' Make coexpression modules/features '''
    model = linkage(corDist, method=linkageMethod)
    moduleLabels = pd.Series(fcluster(model, t = dist, criterion = "distance"))
    return moduleLabels

def trimModules(moduleLabels, gene_names ,moduleGeneNumFilter):
    # count and sort the number of genes in each module
    modCount = moduleLabels.value_counts()
    labelSet = modCount[modCount>=moduleGeneNumFilter].index
    moduleGeneNames = [pd.Series(gene_names)[moduleLabels==labelSet[i]].tolist() for i in range(labelSet.size)]
    print("Created ", labelSet.size," modules")
    return moduleGeneNames


def run_coex_subsample(datasetSubsample, gene_number, linkageMethod, dist, moduleGeneNumFilter):
    samples = [samp.sample_name for samp in datasetSubsample.samples]
    exp_data = load_dataset(datasetSubsample.dataset_id, sample_names=samples)
    # Filter the matrix to the most highly variable genes
    gene_list = filterByVar(exp_data, gene_number)
    print(f"Gene number is = {gene_number}")
    db_genes = db.session.scalars(select(Gene).filter(Gene.gene_id.in_(gene_list))).all()
    # check if existing Subclust gene object exists
    subClGenes = db.session.execute(select(SubclustGenes).options(joinedload(SubclustGenes.genes))
          .where(SubclustGenes.dataset_subsample == datasetSubsample)).scalar()
    ScGExists = subClGenes is not None
    print(f"ScGExists = {ScGExists}")
    if ScGExists is False:
        
        subClGenes = SubclustGenes(dataset_subsample=datasetSubsample, genes=db_genes)
        db.session.add(subClGenes)
        db.session.commit()
    
    # Create correlation distance matrix
    gene_names = [gene.gene_id for gene in subClGenes.genes]
    print(f"Number of genes = {len(gene_names)}")
    corDist = makeCorrDist(exp_data.loc[gene_names])
    # Create modules
    moduleLabels = clusterByGenes(corDist, linkageMethod=linkageMethod, dist=dist)
    modules = trimModules(moduleLabels, gene_names, moduleGeneNumFilter)
    return modules


