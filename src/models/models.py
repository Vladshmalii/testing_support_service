from tortoise.models import Model
from tortoise import fields
from ..enums import UserRole, RequestStatus
from .mixins import ModelPrefixMixin


class User(Model, ModelPrefixMixin):
    PREFIX = "USR"

    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    role = fields.CharEnumField(UserRole)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    inn = fields.CharField(max_length=12, null=True)
    phone = fields.CharField(max_length=20, null=True)
    first_name = fields.CharField(max_length=100, null=True)
    last_name = fields.CharField(max_length=100, null=True)
    birth_date = fields.DateField(null=True)
    father_name = fields.CharField(max_length=100, null=True)

    class Meta:
        table = "users"


class Request(Model, ModelPrefixMixin):
    PREFIX = "REQ"

    id = fields.IntField(pk=True)
    owner = fields.ForeignKeyField("models.User", related_name="requests", on_delete=fields.CASCADE)
    text = fields.TextField()
    status = fields.CharEnumField(RequestStatus, default=RequestStatus.NEW)
    staff_member = fields.ForeignKeyField("models.User", related_name="assigned_requests", null=True,
                                          on_delete=fields.SET_NULL)
    staff_comment = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "requests"