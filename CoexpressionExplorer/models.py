from flask_sqlalchemy import SQLAlchemy
from typing import List, Optional
from sqlalchemy import ForeignKey, Table, String, Column, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class Dataset(db.Model):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    path: Mapped[str] = mapped_column(String(400), unique=True)
    metadata_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dataset_meta.id"))
    dataset_metadata: Mapped[Optional["DatasetMeta"]] = relationship(foreign_keys=metadata_id)
 

class DatasetMeta(db.Model):
    __tablename__ = "dataset_meta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    path: Mapped[str] = mapped_column(String(400), unique=True)
    


class SampleAnnotation(db.Model):
    __tablename__ = "sample_annotations"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    annotation_type: Mapped[str] = mapped_column(String(40))
    annotation: Mapped[str] = mapped_column(String(60))
    
    __table_args__ = (
        UniqueConstraint("annotation_type","annotation", name="anno"),
    )


sample_annotation_association_table = Table(
    "sample_annotation_association",
    db.Model.metadata,
    Column("sample_id", ForeignKey("samples.id"), primary_key=True),
    Column("sample_annotation_id", ForeignKey("sample_annotations.id"), primary_key=True)
)

class Sample(db.Model):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sample_name: Mapped[str] = mapped_column(String(50))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    dataset: Mapped["Dataset"] = relationship()
    annotations: Mapped[List[SampleAnnotation]] = relationship(secondary=sample_annotation_association_table)


subsample_association_table = Table(
    "subsample_association",
    db.Model.metadata,
    Column("sample_id", ForeignKey("samples.id"), primary_key=True),
    Column("subsample_id", ForeignKey("dataset_subsamples.id"), primary_key=True)
)

class DatasetSubsample(db.Model):
    __tablename__ = "dataset_subsamples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #sample_ids: Mapped[List[int]] = mapped_column(ForeignKey("samples.id"))
    samples: Mapped[List[Sample]] = relationship(secondary=subsample_association_table)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    dataset: Mapped["Dataset"] = relationship(foreign_keys=dataset_id)
    parent_subsample_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dataset_subsamples.id"),nullable=True)
    parent_subsample: Mapped[Optional["DatasetSubsample"]] = relationship("DatasetSubsample")


class Gene(db.Model):
    __tablename__ = "genes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gene_id: Mapped[str] = mapped_column(String(20))
    gene_symbol: Mapped[Optional[str]] = mapped_column(String(20),nullable=True)
    gene_name: Mapped[str] = mapped_column(String(40),nullable=True)


gene_association_table = Table(
    "gene_subsample_association",
    db.Model.metadata,
    Column("gene_id", ForeignKey("genes.id"), primary_key=True),
    Column("subclust_geneset_id", ForeignKey("subclust_genesets.id"), primary_key=True)
)


class SubclustGenes(db.Model):
    __tablename__ = "subclust_genesets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gene_number: Mapped[int] = mapped_column()
    dataset_subsample_id: Mapped[int] = mapped_column(ForeignKey("dataset_subsamples.id"))
    dataset_subsample: Mapped["DatasetSubsample"] = relationship()
    genes: Mapped[List["Gene"]] = relationship(secondary=gene_association_table)


module_association_table = Table(
    "module_subsample_association",
    db.Model.metadata,
    Column("gene_id", ForeignKey("genes.id"), primary_key=True),
    Column("module_id", ForeignKey("modules.id"), primary_key=True)
)


class Modules(db.Model):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(30))
    subsample_id: Mapped[int] = mapped_column(ForeignKey("dataset_subsamples.id"))
    subsample: Mapped["DatasetSubsample"] = relationship()
    subclust_geneset_id: Mapped[int] = mapped_column(ForeignKey("subclust_genesets.id"))
    subclust_geneset: Mapped["SubclustGenes"] = relationship()
    genes: Mapped[List["Gene"]] = relationship(secondary=module_association_table)



