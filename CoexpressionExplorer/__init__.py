import os
from flask import Flask
import click



# create and configure the app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///CoExDB.db"
    
    
from CoexpressionExplorer.models import db, Dataset, DatasetMeta
db.init_app(app)
import CoexpressionExplorer.views

with app.app_context():
    db.create_all()


@app.cli.command("load_dataset")
@click.option("--name", help="What to call the dataset")
@click.option("--path")
@click.option("--metadata_name")
@click.option("--metadata_path")
def load_dataset(name,path,metadata_name,metadata_path):
    meta = DatasetMeta(name=metadata_name, path=metadata_path)
    df = Dataset(name=name, path=path)
    df.dataset_metadata = meta
    db.session.add(df)
    db.session.commit()

 # flask --app CoexpressionExplorer load_dataset --name "TCGA, GTEx and TARGET - TPM" --path "/home/ewan/Documents/Expression Data/Parq/TcgaTargetGtex_rsem_gene_tpm_GreaterThanOneTPMmedian.parquet" --metadata_name "Combined TCGA, GTEx and Target sample phenotypes" --metadata_path "/home/ewan/Documents/Expression Data/Annotation/TCGA_target_GTEX_KF_phenotype.txt"
        
        
        




