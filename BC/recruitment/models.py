from django.db import models
from member.models import Member
from reservation.models import Reservation

# Community (모집글)
# -----------------------------------------------------
class Community(models.Model):
    community_id = models.AutoField(primary_key=True)
    contents = models.TextField()
    region = models.CharField(max_length=10)
    sport_type = models.CharField(max_length=10)
    facility = models.CharField(max_length=100, default="미정")
    num_member = models.IntegerField()

    reg_date = models.DateTimeField(auto_now_add=True)
    chat_url = models.CharField(max_length=100, null=True, blank=True)
    view_cnt = models.IntegerField(default=0)
    update_date = models.DateTimeField(auto_now=True)
    delete_date = models.DateTimeField(null=True, blank=True)

    member_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    reservation_id = models.ForeignKey(Reservation, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "community"

    def __str__(self):
        return f"모집글 {self.community_id}"
    
# EndStatus (마감 상황)
# -----------------------------------------------------
class EndStatus(models.Model):
    community = models.OneToOneField(Community,primary_key=True,on_delete=models.CASCADE)
    end_date = models.DateField(null=True, blank=True)
    end_set_date = models.DateField()
    end_stat = models.IntegerField(default=0)       # 마감여부(0=마감안됨, 1=마감)

    class Meta:
        db_table = "end_status"

    def __str__(self):
        return f"Community {self.community_id} 마감상태"
# Rating (평점)
# -----------------------------------------------------
class Rating(models.Model):
    facility = models.CharField(max_length=100, primary_key=True)
    user_id = models.CharField(max_length=20)
    rated = models.IntegerField(default=0)
    comments = models.TextField()
    community_id = models.ForeignKey(Community)
    class Meta:
        db_table = "rating"

    def __str__(self):
        return f"{self.facility} - {self.rated}점"
    
# JoinStat (참석 여부) — 복합 PK
# -----------------------------------------------------
class JoinStat(models.Model):
    member_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    community_id = models.ForeignKey(Community, on_delete=models.CASCADE)
    join_status = models.IntegerField(default=0)

    class Meta:
        db_table = "join_stat"
        constraints = [
            models.UniqueConstraint(
                fields=["member", "community"],
                name="pk_join_stat"
            )
        ]
