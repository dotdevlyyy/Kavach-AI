"""
Kavach AI — NetworkLog Model
Represents a snapshot of a network connection for air-gap audit.
"""

from tortoise import fields, models


class NetworkLog(models.Model):
    """A log entry recording a network connection snapshot for sovereignty audit."""

    id = fields.IntField(pk=True)  # Auto-increment
    timestamp = fields.DatetimeField(auto_now_add=True)
    local_addr = fields.CharField(max_length=100)
    remote_addr = fields.CharField(max_length=100)
    protocol = fields.CharField(max_length=10)
    status = fields.CharField(max_length=50)
    process_name = fields.CharField(max_length=200, null=True)
    is_local = fields.BooleanField(default=True)

    class Meta:
        table = "network_logs"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"NetworkLog({self.id}, {self.local_addr} -> {self.remote_addr})"
