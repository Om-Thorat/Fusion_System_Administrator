import json
from pathlib import Path

from django.conf import settings

from .models import ArchiveRecord, AuthUser, GlobalsExtrainfo, Student


VALID_ARCHIVE_TYPES = {"archived", "alumni"}


def _safe_segment(value):
    if value is None:
        return "unknown"
    text = str(value).strip()
    if not text:
        return "unknown"
    return text.replace("/", "-")


def archive_student(student_username, archive_type, archived_by):
    archive_type = (archive_type or "").strip().lower()
    if archive_type not in VALID_ARCHIVE_TYPES:
        raise ValueError("archive_type must be either 'archived' or 'alumni'.")

    normalized_username = (student_username or "").strip()
    if not normalized_username:
        raise ValueError("student_username is required.")

    student = (
        Student.objects.select_related("id__user", "batch_id__discipline")
        .filter(id__user__username__iexact=normalized_username)
        .first()
    )
    if not student:
        raise Student.DoesNotExist(f"Student '{normalized_username}' not found.")

    user = AuthUser.objects.get(pk=student.id.user_id)
    extra_info = GlobalsExtrainfo.objects.get(pk=student.id_id)

    discipline_name = ""
    if student.batch_id and student.batch_id.discipline:
        discipline_name = student.batch_id.discipline.name
    elif extra_info.department:
        discipline_name = extra_info.department.name

    full_name = f"{user.first_name} {user.last_name}".strip()
    archive_payload = {
        "username": user.username,
        "full_name": full_name,
        "email": user.email,
        "programme": student.programme,
        "discipline": discipline_name,
        "batch": student.batch,
        "curr_semester_no": student.curr_semester_no,
        "category": student.category,
        "father_name": student.father_name,
        "mother_name": student.mother_name,
        "hall_no": student.hall_no,
        "room_no": student.room_no,
        "cpi": student.cpi,
        "date_of_birth": extra_info.date_of_birth.isoformat()
        if extra_info.date_of_birth
        else None,
        "phone_no": extra_info.phone_no,
        "address": extra_info.address,
        "sex": extra_info.sex,
        "title": extra_info.title,
    }

    base_media = Path(settings.BASE_DIR) / "media"
    archive_dir = (
        base_media
        / "archives"
        / f"Batch_{student.batch}"
        / _safe_segment(student.programme)
        / _safe_segment(discipline_name)
    )
    archive_dir.mkdir(parents=True, exist_ok=True)

    file_path = archive_dir / f"{user.username}.json"
    with file_path.open("w", encoding="utf-8") as archive_file:
        json.dump(archive_payload, archive_file, indent=2)

    ArchiveRecord.objects.create(
        student_username=user.username,
        full_name=full_name,
        programme=student.programme,
        discipline=discipline_name,
        batch=student.batch,
        archive_type=archive_type,
        json_file_path=str(file_path),
        archived_by=(archived_by or "system").strip() or "system",
    )

    return str(file_path)
