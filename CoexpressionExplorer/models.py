from flask_sqlalchemy import SQLAlchemy
from typing import List, Optional
from sqlalchemy import ForeignKey, Table, String, Column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class Dataset(db.Model):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    path: Mapped[str] = mapped_column(String(40))
    dataset_metadata: Mapped["DatasetMeta"] = relationship(back_populates="dataset")
    subsample_init: Mapped["DatasetSubsample"] = relationship()


class DatasetMeta(db.Model):
    __tablename__ = "dataset_meta"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    path: Mapped[str] = mapped_column(String(40))
    dataset: Mapped["Dataset"] = relationship(back_populates="dataset_metadata")


class SampleAnnotation(db.Model):
    __tablename__ = "sample_annotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    annotation_type: Mapped[str] = mapped_column(String(40))
    annotation: Mapped[str] = mapped_column(String(60))


subsample_association_table = Table(
    "subsample_association",
    db.Model.metadata,
    Column("sample_id", ForeignKey("samples.id"), primary_key=True),
    Column("subsample_id", ForeignKey("dataset_subsamples.id"), primary_key=True)
)

class Sample(db.Model):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(30))
    dataset: Mapped["Dataset"] = relationship()
    subsamples: Mapped[List["DatasetSubsample"]] = relationship(secondary=subsample_association_table,
                                                                back_populates="sample_ids")



class DatasetSubsample(db.Model):
    __tablename__ = "dataset_subsamples"

    id: Mapped[int] = mapped_column(primary_key=True)
    samples: Mapped[List["Sample"]] = relationship(secondary=subsample_association_table,
                                                 back_populates="subsamples")
    dataset: Mapped["Dataset"] = relationship()
    parent_subsample: Mapped[Optional["DatasetSubsample"]] = relationship()


class Gene(db.Model):
    __tablename__ = "genes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    gene_id: Mapped[str] = mapped_column(String(20))
    gene_symbol: Mapped[str] = mapped_column(String(20))
    gene_name: Mapped[str] = mapped_column(String(40))


gene_association_table = Table(
    "gene_subsample_association",
    db.Model.metadata,
    Column("gene_id", ForeignKey("genes.id"), primary_key=True),
    Column("subclust_geneset_id", ForeignKey("subclust_genesets.id"), primary_key=True)
)


class SubclustGenes(db.Model):
    __tablename__ = "subclust_genesets"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_subsample: Mapped["DatasetSubsample"] = relationship(secondary=gene_association_table)


module_association_table = Table(
    "module_subsample_association",
    db.Model.metadata,
    Column("gene_id", ForeignKey("genes.id"), primary_key=True),
    Column("module_id", ForeignKey("modules.id"), primary_key=True)
)


class Modules(db.Model):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(30))
    subsample: Mapped["DatasetSubsample"] = relationship()
    subclust_geneset: Mapped["SubclustGenes"] = relationship()
    genes: Mapped[List["Gene"]] = relationship(secondary=module_association_table)


