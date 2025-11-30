from django.db import models


# FacilityInfo (시설)
# -----------------------------------------------------
class FacilityInfo(models.Model):
    facility_id = models.AutoField(primary_key=True)
    photo = models.CharField(max_length=500) # 사진 필요할까요?
    facility_name = models.CharField(max_length=100)
    sport_type = models.CharField(max_length=100) # 종목인데, 그냥 sport 테이블에서 fk로 가져오는게 나을지/삭제하는게 나을지
    addr1 = models.CharField(max_length=200)  # 시
    addr2 = models.CharField(max_length=200)  # 구
    addr3 = models.CharField(max_length=200)  # 나머지 주소
    homepage = models.CharField(max_length=200, null=True, blank=True)
    tel = models.CharField(max_length=200, null=True, blank=True)
    time_date = models.JSONField(null=True, blank=True)
    etc = models.CharField(max_length=200, null=True, blank=True)
    sports_id = models.ForeignKey("reservation.Sports", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "facility_info"

    def __str__(self):
        return self.facility_name


class Facility(models.Model):
    faci_cd = models.CharField(max_length=50, unique=True)

    faci_nm = models.CharField(max_length=200, null=True, blank=True)
    faci2_nm = models.CharField(max_length=200, null=True, blank=True)
    cp_nm = models.CharField(max_length=50, null=True, blank=True)
    cpb_nm = models.CharField(max_length=50, null=True, blank=True)
    fcob_nm = models.CharField(max_length=100, null=True, blank=True)
    ftype_nm = models.CharField(max_length=100, null=True, blank=True)

    faci_addr = models.CharField(max_length=300, null=True, blank=True)
    faci_road_addr = models.CharField(max_length=300, null=True, blank=True)
    faci_daddr = models.CharField(max_length=300, null=True, blank=True)
    faci_road_daddr = models.CharField(max_length=300, null=True, blank=True)
    faci_zip = models.CharField(max_length=20, null=True, blank=True)

    faci_lat = models.FloatField(null=True, blank=True)
    faci_lot = models.FloatField(null=True, blank=True)

    faci_stat_nm = models.CharField(max_length=50, null=True, blank=True)
    schk_tot_grd_nm = models.CharField(max_length=50, null=True, blank=True)
    schk_tot_grd_cd = models.CharField(max_length=5, null=True, blank=True)

    faci_mng_type_cd = models.CharField(max_length=20, null=True, blank=True)
    inout_gbn_nm = models.CharField(max_length=10, null=True, blank=True)
    atnm_chk_yn = models.CharField(max_length=1, null=True, blank=True)
    faci_tel_no = models.CharField(max_length=50, null=True, blank=True)
    faci_homepage = models.CharField(max_length=200, null=True, blank=True)

    faci_gfa = models.CharField(max_length=50, null=True, blank=True)

    base_ymd = models.CharField(max_length=20, null=True, blank=True)
    reg_dt = models.CharField(max_length=20, null=True, blank=True)
    faci_reg_ymd = models.CharField(max_length=20, null=True, blank=True)
    faci_upd_ymd = models.CharField(max_length=20, null=True, blank=True)
    schk_visit_ymd = models.CharField(max_length=20, null=True, blank=True)
    schk_open_ymd = models.CharField(max_length=20, null=True, blank=True)
    sdwn_ymd = models.CharField(max_length=20, null=True, blank=True)
    th_ymd = models.CharField(max_length=20, null=True, blank=True)

    row_num = models.IntegerField(null=True, blank=True)

    reg_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "facility"
        
    def __str__(self):
        return f"{self.faci_nm} ({self.faci_cd})"