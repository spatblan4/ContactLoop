from sqlalchemy.dialects import postgresql

from app.models import ContactEvent


def test_contact_event_discussed_topics_uses_existing_postgres_text_array():
    column = ContactEvent.__table__.c.discussed_topics
    postgres_type = column.type.dialect_impl(postgresql.dialect())

    assert isinstance(postgres_type, postgresql.ARRAY)
