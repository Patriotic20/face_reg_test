from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from core.logging import logging
from models.role import Role
from core.db_helper import db_helper

logger = logging.getLogger(__name__)

ROLE_LIST = [
    "admin",
    "user",
    "teacher",
    "student",
]


async def create_roles():
    logger.info(f"Starting role creation process for {len(ROLE_LIST)} roles")

    async with db_helper.session_factory() as session:
        try:
            created_count = 0
            existing_count = 0

            for role_name in ROLE_LIST:
                stmt = select(Role).where(Role.name == role_name)
                result = await session.execute(stmt)
                existing_role = result.scalar_one_or_none()

                if existing_role:
                    existing_count += 1
                else:
                    session.add(Role(name=role_name))
                    created_count += 1

            await session.commit()

            logger.info(
                f"Role creation complete: {created_count} created, "
                f"{existing_count} already exist, {len(ROLE_LIST)} total"
            )

        except IntegrityError as e:
            await session.rollback()
            logger.warning(f"Integrity error during role creation: {e}")
            raise

        except Exception as e:
            await session.rollback()
            logger.exception("Failed to create roles")
            raise
