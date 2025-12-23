from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from uuid import uuid4

from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberAdd


class ProjectCRUD:

    @staticmethod
    def get_by_id(db: Session, project_id: str) -> Project | None:
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_by_key(db: Session, project_key: str) -> Project | None:
        return db.query(Project).filter(Project.project_key == project_key).first()

    @staticmethod
    def get_user_projects(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        return (
            db.query(Project)
            .join(ProjectMember)
            .filter(
                ProjectMember.user_id == user_id,
                Project.is_archived == False
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_project_count(db: Session, user_id: str) -> int:
        return (
            db.query(Project)
            .join(ProjectMember)
            .filter(
                ProjectMember.user_id == user_id,
                Project.is_archived == False
            )
            .count()
        )

    @staticmethod
    def create(
        db: Session,
        data: ProjectCreate,
        owner_id: str
    ) -> Project:
        project = Project(
            id=str(uuid4()),
            name=data.name,
            project_key=data.project_key,
            description=data.description,
            project_type=data.project_type,
            owner_id=owner_id
        )
        db.add(project)
        db.flush()

        member = ProjectMember(
            id=str(uuid4()),
            project_id=project.id,
            user_id=owner_id,
            role="ADMIN"
        )
        db.add(member)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def update(
        db: Session,
        project_id: str,
        data: ProjectUpdate
    ) -> Project | None:
        project = ProjectCRUD.get_by_id(db, project_id)
        if not project:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(project, key, value)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete(db: Session, project_id: str) -> bool:
        project = ProjectCRUD.get_by_id(db, project_id)
        if not project:
            return False

        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def archive(db: Session, project_id: str) -> Project | None:
        project = ProjectCRUD.get_by_id(db, project_id)
        if not project:
            return None

        project.is_archived = True
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def add_member(
        db: Session,
        project_id: str,
        data: ProjectMemberAdd
    ) -> ProjectMember:
        member = ProjectMember(
            id=str(uuid4()),
            project_id=project_id,
            user_id=data.user_id,
            role=data.role
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_member(
        db: Session,
        project_id: str,
        user_id: str
    ) -> bool:
        deleted = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
            .delete()
        )
        db.commit()
        return deleted > 0

    @staticmethod
    def get_members(
        db: Session,
        project_id: str
    ) -> list[ProjectMember]:
        return (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id)
            .all()
        )

    @staticmethod
    def get_member(
        db: Session,
        project_id: str,
        user_id: str
    ) -> ProjectMember | None:
        return (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
            .first()
        )

    @staticmethod
    def get_stats(db: Session, project_id: str) -> dict:
        task_count = (
            db.query(func.count(Task.id))
            .filter(Task.project_id == project_id)
            .scalar()
        )
        member_count = (
            db.query(func.count(ProjectMember.id))
            .filter(ProjectMember.project_id == project_id)
            .scalar()
        )
        return {
            "task_count": task_count or 0,
            "member_count": member_count or 0
        }

    @staticmethod
    def search(
        db: Session,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> list[Project]:
        return (
            db.query(Project)
            .join(ProjectMember)
            .filter(
                ProjectMember.user_id == user_id,
                Project.is_archived == False,
                or_(
                    Project.name.ilike(f"%{query}%"),
                    Project.project_key.ilike(f"%{query}%")
                )
            )
            .limit(limit)
            .all()
        )
