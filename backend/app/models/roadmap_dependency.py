from sqlalchemy import BigInteger, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RoadmapDependency(Base):
    __tablename__ = 'roadmap_dependencies'
    __table_args__ = (
        ForeignKeyConstraint(['from_id','project_id'],['project_roadmap_milestones.id','project_roadmap_milestones.project_id'],ondelete='RESTRICT'),
        ForeignKeyConstraint(['to_id','project_id'],['project_roadmap_milestones.id','project_roadmap_milestones.project_id'],ondelete='RESTRICT'),
        UniqueConstraint('project_id','from_id','to_id'),
        CheckConstraint('from_id <> to_id',name='ck_roadmap_dependency_not_self'),
    )
    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    project_id: Mapped[int] = mapped_column(BigInteger,index=True)
    from_id: Mapped[int] = mapped_column(BigInteger)
    to_id: Mapped[int] = mapped_column(BigInteger)
