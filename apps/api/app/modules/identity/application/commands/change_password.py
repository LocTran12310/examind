from dataclasses import dataclass

from app.modules.identity.application.common import load_user
from app.modules.identity.domain.ports import PasswordHasher, UserRepository
from app.modules.identity.domain.services.accounts import check_new_password
from app.shared.application.actor import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import Invalid


@dataclass(frozen=True)
class ChangePassword:
    current_password: str
    new_password: str


class ChangePasswordHandler:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, uow: UnitOfWork):
        self.users, self.hasher, self.uow = users, hasher, uow

    def __call__(self, actor: Actor, cmd: ChangePassword) -> None:
        user = load_user(self.users, actor.user_id)
        if not self.hasher.verify(cmd.current_password or "", user.password_hash):
            raise Invalid("Mật khẩu hiện tại không đúng", "current_password")
        check_new_password(cmd.new_password)
        if cmd.current_password == cmd.new_password:
            raise Invalid("Mật khẩu mới phải khác mật khẩu cũ", "new_password")
        user.password_hash = self.hasher.hash(cmd.new_password)
        user.must_change_password = False
        self.uow.commit()
