# moved to the taxonomy and academic modules (architecture-refactor ADR-01); re-exported for the old layout
from app.modules.academic.domain.entities import Grade, SchoolLevel  # noqa: F401
from app.modules.academic.infrastructure import orm as _academic_orm  # noqa: F401
from app.modules.taxonomy.domain.entities import TAG_GROUPS, Semester, Subject, Tag  # noqa: F401
from app.modules.taxonomy.domain.topics import LEVEL_KINDS, MAX_TOPIC_DEPTH, Topic, topic_label  # noqa: F401
from app.modules.taxonomy.infrastructure import orm as _taxonomy_orm  # noqa: F401
from app.shared.infrastructure.schema.taxonomy import LtreeType  # noqa: F401
