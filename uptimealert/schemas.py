from marshmallow import Schema, fields


class MonitorSchema(Schema):
    id = fields.Integer()
    user_id = fields.Integer()
    name = fields.String()
    last_checked_at = fields.DateTime()
    status = fields.Boolean()
