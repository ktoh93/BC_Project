from django.db import models

# -----------------------------------------------------
# Member (사용자)
# -----------------------------------------------------
class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=100)
    nickname = models.CharField(max_length=20, unique=True)
    birthday = models.IntegerField()
    gender = models.IntegerField()
    addr = models.CharField(max_length=200)
    phone_num = models.CharField(max_length=100, unique=True)
    delete_yn = models.IntegerField(default=0)                  # 탈퇴여부(0=지금회원, 1=탈퇴)
    reg_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    delete_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "member"

    def __str__(self):
        return self.user_id
    
# -----------------------------------------------------
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

