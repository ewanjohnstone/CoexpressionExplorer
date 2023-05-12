import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List
import click
from flask.cli import with_appcontext
from sqlalchemy import select, insert, update
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
import mygene


from CoexpressionExplorer.models import db, Dataset, DatasetMeta, Gene, Sample, SampleAnnotation, DatasetSubsample
import CoexpressionExplorer.CoexClust as CoexClust
import CoexpressionExplorer.setup_db as setup_db
from . import app


@click.command("insert_dataset")
@with_appcontext
@click.option("--name", help="What to call the dataset")
@click.option("--path")
@click.option("--metadata_name")
@click.option("--metadata_path")
def insert_dataset(name,path,metadata_name,metadata_path):
    # check to see if the dataset has already been inserted
    df = Dataset(name=name, path=path)
    meta = DatasetMeta(name=metadata_name, path=metadata_path)

    dataset_id = db.session.query(Dataset.id).where(
        Dataset.name == name or Dataset.path == path).scalar()
    metadata_id = db.session.query(DatasetMeta.id).where(
        DatasetMeta.name == metadata_name or DatasetMeta.path == metadata_path).scalar()
    if (dataset_id is not None) or (metadata_id is not None):
        print("""
        This dataset has already been uploaded. Either path or name is not unique. 
        Moving forward to insert gene IDs""")
        df = db.session.query(Dataset).where(Dataset.id == dataset_id).first()
    else:
        db.session.add(meta)
        db.session.commit()
        df.dataset_metadata = meta
        db.session.add(df)
        db.session.commit()

    
    exp_data = CoexClust.load_dataset(df.id)
    gene_ids = exp_data.index.values
    sample_names = exp_data.columns
    del exp_data


    # Insert Genes
    db_genes = db.session.query(Gene.gene_id).all()
    db_genes = [a[0] for a in db_genes]

    new_genes = list(set(gene_ids) - set(db_genes))
    print(f"Found {len(new_genes)} new genes.")
    
    # gather other gene metadata
    if len(new_genes) > 0:
        mg = mygene.MyGeneInfo()
        geneMetadata = mg.getgenes(new_genes, 
                           fields='ensembl.gene,name,symbol',
                           as_dataframe=True)
        geneMetadata.reset_index(inplace=True)
        geneMetadata = geneMetadata[["query","symbol","name"]]
        geneMetadata.columns = ["gene_id","gene_symbol","gene_name"]
        geneMetadata = geneMetadata.to_dict("records")
        db.session.execute(insert(Gene),geneMetadata,)
        db.session.commit()
    
    # insert sample metadata
    anno = CoexClust.load_dataset_metadata(df.id)
    anno = pd.DataFrame(anno.stack())
    anno.reset_index(inplace=True)
    anno.columns = ["sample_name", "annotation_type", "annotation"]
    anno_dicts = anno[["annotation_type","annotation"]].to_dict("records")
    #anno_dicts = list(set(anno_dicts)) inteded to de-dup the annotations
    anno_stmt = sqlite_upsert(SampleAnnotation).values(anno_dicts)
    anno_stmt = anno_stmt.on_conflict_do_nothing(
        index_elements = ["annotation_type","annotation"])
    db.session.execute(anno_stmt)
    db.session.commit()

    # Insert Samples
    db_samples = db.session.query(Sample.dataset_id).all()
    db_samples = [a[0] for a in db_samples]
    anno_obs = db.session.query(SampleAnnotation).all()

    new_samples = list(set(sample_names) - set(db_samples))
    
    # insert the samples and annotation links - This part is very slow as it is doing a select query per sample. Should be improved later. 
    if len(new_samples) > 0:
        for i in range(len(new_samples)):
            sample = Sample(sample_name = new_samples[i], dataset_id = df.id)

            annoSlice = anno.loc[anno["sample_name"] == new_samples[i]]

            annoItems = []
            for index, row in annoSlice.iterrows():
                annoItems.append(
                    db.session.execute(
                    select(SampleAnnotation).filter_by(annotation = row["annotation"]).filter_by(annotation_type = row["annotation_type"])).scalar_one())
            sample.annotations = annoItems
            db.session.add(sample)
            db.session.commit()
            


        


        

@click.command("run_coex")
@with_appcontext
@click.option("--dataset_id", required=True, type=int)
@click.option("--gene_number", type=int, default=5000,
              help="The number of high variance genes to cluster for this dataset")
def run_coex(dataset_id, gene_number):
    # Create an initial parent DatasetSubsample object for the dataset.
    parentDataset = db.session.execute(select(Dataset).where(Dataset.id == dataset_id)).first()[0]
    dSamples = db.session.execute(select(Sample).where(Sample.dataset_id == parentDataset.id)).all()
    samples = [d[0] for d in dSamples]
    print(f"Gene number is = {gene_number}")
    dss = db.session.execute(select(DatasetSubsample)
          .where(DatasetSubsample.dataset==parentDataset)).scalar()
    dsExists = dss is not None
    print(f"dsExists = {dsExists}")
    if dsExists is False:
        dss = DatasetSubsample(dataset=parentDataset, samples=samples)
        db.session.add(dss)
        db.session.commit()
    else:
        print(f"Root Subsample already exists for dataset id ={dataset_id}")
    # Open the dataset and import the expression matrix
    coex_modules = CoexClust.run_coex_subsample(dss, gene_number = gene_number, linkageMethod="average", 
                                                dist=0.2, moduleGeneNumFilter=6)
    return print(coex_modules)

app.cli.add_command(insert_dataset)
app.cli.add_command(run_coex)