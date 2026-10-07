"""Streaming CSV exports shared by students, rosters, and the audit log."""
import csv
from datetime import date

from django.http import StreamingHttpResponse


def safe_cell(value):
    """Prefix spreadsheet-trigger characters so Excel/Sheets never evaluates
    a cell as a formula."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


class _Echo:
    """csv.writer writes each row here; returning the string turns the row
    into a generator item."""

    def write(self, value):
        return value


def csv_response(filename_prefix, header, rows):
    """A streaming CSV response with a UTF-8 BOM and formula-safe cells."""
    writer = csv.writer(_Echo())

    def generate():
        # A leading BOM makes Excel open the file as UTF-8.
        yield "\ufeff"
        yield writer.writerow(header)
        for row in rows:
            yield writer.writerow([safe_cell(cell) for cell in row])

    filename = f"{filename_prefix}-{date.today().isoformat()}.csv"
    response = StreamingHttpResponse(generate(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
