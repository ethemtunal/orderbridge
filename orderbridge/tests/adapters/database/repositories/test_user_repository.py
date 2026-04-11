from orderbridge.adapters.database.repositories import DBUserRepo
from orderbridge.common.datagen.user_factory import UserFactory


def test_get_user(orderbridge_db):
    user = UserFactory.create(uuid="my-uuid")
    user_repo = DBUserRepo(orderbridge_db)
    fetched_user = user_repo.get_by_id(user.id)
    assert fetched_user.uuid == user.uuid

    assert user_repo.get_by_uuid("my-uuid").id == user.id
