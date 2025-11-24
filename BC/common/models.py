from django.db import models
from member.models import Member
from recruitment.models import Community
from board.models import Article

# Create your models here.
# -----------------------------------------------------
# Comment (댓글)
# -----------------------------------------------------
class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    comment = models.TextField()
    reg_date = models.DateTimeField(auto_now_add=True)
    delete_date = models.DateTimeField(null=True, blank=True, unique=True)

    member_id = models.ForeignKey(Member)
    community_id = models.ForeignKey(Community, null=True, blank=True)
    article_id = models.ForeignKey(Article, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        db_table = "comment"

    def __str__(self):
        return f"댓글 {self.comment_id}"


# -----------------------------------------------------
# AddInfo (첨부파일)
# -----------------------------------------------------
class AddInfo(models.Model):
    add_info_id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=20)
    file_name = models.CharField(max_length=100)
    encoded_name = models.CharField(max_length=200)
    reg_date = models.DateTimeField(auto_now_add=True)

    article_id = models.ForeignKey(Article, null=True, blank=True, on_delete=models.SET_NULL)
    community_id = models.ForeignKey(Community, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "add_info"

    def __str__(self):
        return self.file_name