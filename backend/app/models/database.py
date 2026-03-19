"""
数据库模型 - 使用 SQLAlchemy
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Report(db.Model):
    """报告模型"""

    __tablename__ = "reports"

    id = db.Column(db.String(50), primary_key=True)
    simulation_id = db.Column(db.String(100), nullable=True, index=True)
    title = db.Column(db.String(500), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    outline = db.Column(db.JSON, nullable=True)
    markdown_content = db.Column(db.Text, nullable=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 报告文件路径（相对于 UPLOAD_FOLDER）
    markdown_file_path = db.Column(db.String(500), nullable=True)
    pdf_file_path = db.Column(db.String(500), nullable=True)
    word_file_path = db.Column(db.String(500), nullable=True)

    sections = db.relationship(
        "ReportSection", backref="report", lazy="dynamic", cascade="all, delete-orphan"
    )
    progress = db.relationship(
        "ReportProgress", backref="report", uselist=False, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "report_id": self.id,
            "simulation_id": self.simulation_id,
            "title": self.title,
            "summary": self.summary,
            "status": self.status,
            "outline": self.outline,
            "markdown_content": self.markdown_content,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "files": {
                "markdown": self.markdown_file_path,
                "pdf": self.pdf_file_path,
                "word": self.word_file_path,
            },
        }


class ReportSection(db.Model):
    """报告章节模型"""

    __tablename__ = "report_sections"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(50), db.ForeignKey("reports.id"), nullable=False)
    section_index = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("report_id", "section_index", name="uq_report_section"),
        db.Index("idx_report_section", "report_id", "section_index"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "section_index": self.section_index,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReportProgress(db.Model):
    """报告进度模型"""

    __tablename__ = "report_progress"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(
        db.String(50), db.ForeignKey("reports.id"), nullable=False, unique=True
    )
    status = db.Column(db.String(20), nullable=False, default="pending")
    progress = db.Column(db.Integer, default=0)
    message = db.Column(db.Text, nullable=True)
    current_section = db.Column(db.String(200), nullable=True)
    completed_sections = db.Column(db.JSON, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "current_section": self.current_section,
            "completed_sections": self.completed_sections or [],
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
