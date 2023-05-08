import os
from flask import Flask
import click
from sqlalchemy import select
import CoexpressionExplorer.CoexClust as CoexClust
from CoexpressionExplorer.models import db, Dataset, DatasetMeta


# create and configure the app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///CoExDB.db" 

db.init_app(app)
with app.app_context():
    db.create_all()


import CoexpressionExplorer.views

@app.cli.command("load_dataset")
@click.option("--name", help="What to call the dataset")
@click.option("--path")
@click.option("--metadata_name")
@click.option("--metadata_path")
def load_dataset(name,path,metadata_name,metadata_path):
    # check to see if the dataset has already been inserted
    select(Dataset).where(Dataset.name == name or Dataset.path == path)
    dataExists = db.session.query(Dataset.id).where(
        Dataset.name == name or Dataset.path == path).scalar() is not None
    metaExists = db.session.query(DatasetMeta.id).where(
        DatasetMeta.name == metadata_name or DatasetMeta.path == metadata_path).scalar() is not None
    if dataExists:
        raise Exception("This dataset has already been uploaded. Either path or name is not unique")
    else:
        df = Dataset(name=name, path=path)
        meta = DatasetMeta(name=metadata_name, path=metadata_path)
        db.session.add(meta)
        db.session.commit()
        df.dataset_metadata = meta
        db.session.add(df)
        db.session.commit()
# flask --app CoexpressionExplorer load_dataset --name "TCGA, GTEx and TARGET - TPM" --path "/home/ewan/Documents/Expression Data/Parq/TcgaTargetGtex_rsem_gene_tpm_GreaterThanOneTPMmedian.parquet" --metadata_name "Combined TCGA, GTEx and Target sample phenotypes" --metadata_path "/home/ewan/Documents/Expression Data/Annotation/TCGA_target_GTEX_KF_phenotype.txt"
        

@app.cli.command("run_coex")
@click.option("--dataset_id")
@click.option("--dataset_name")
def run_coex(dataset_id=None, dataset_name=None):
    if dataset_id is not None:
        dataset = db.session.query(Dataset).where(Dataset.id == dataset_id).first()
    elif dataset_name is not None:
        dataset = db.session.query(Dataset).where(Dataset.name == dataset_name).first()
    else:
        raise Exception("You must supply either a dataset id or name")
    df = CoexClust.load_dataset(dataset)
    return df



        
        




