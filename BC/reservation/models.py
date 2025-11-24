from django.db import models
from member.models import Member


# Reservation (예약)
# -----------------------------------------------------
class Reservation(models.Model):
    reservation_id = models.AutoField(primary_key=True)
    reservation_date = models.DateTimeField()
    hour = models.JSONField()
    facility = models.CharField(max_length=100)
    delete_yn = models.IntegerField(default=0)          # 예약상태 (0=예약중, 1=취소)
    reg_date = models.DateTimeField(auto_now_add=True)
    delete_date = models.DateTimeField(null=True, blank=True)

    member = models.ForeignKey(Member)
    class Meta:
        db_table = "reservation"

    def __str__(self):
        return f"예약 {self.reservation_id}"
