from django.db import models
from member.models import Member

# Board (게시판)
# -----------------------------------------------------
class Board(models.Model):
    board_id = models.AutoField(primary_key=True)
    board_name = models.CharField(max_length=200)

    class Meta:
        db_table = "board"

    def __str__(self):
        return self.board_name


# Article (게시글)
# -----------------------------------------------------
class Article(models.Model):
    article_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    contents = models.TextField()
    view_cnt = models.IntegerField(default=0)
    update_date = models.DateTimeField(auto_now=True)
    delete_date = models.DateTimeField(null=True, blank=True)
    reg_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    always_on = models.IntegerField(default=1)              # 상시표시 (0=상시표시, 1=상시표시x)

    member_id = models.ForeignKey(Member)
    board_id = models.ForeignKey(Board, on_delete=models.CASCADE)

    etc_int1 = models.IntegerField(null=True, blank=True)
    etc_int2 = models.IntegerField(null=True, blank=True)
    etc_int3 = models.IntegerField(null=True, blank=True)

    etc_text1 = models.CharField(max_length=100, null=True, blank=True)
    etc_text2 = models.CharField(max_length=100, null=True, blank=True)
    etc_text3 = models.CharField(max_length=100, null=True, blank=True)

    etc_date1 = models.DateTimeField(null=True, blank=True)
    etc_date2 = models.DateTimeField(null=True, blank=True)
    etc_date3 = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "article"

    def __str__(self):
        return self.title