# read_data.py
# HealthSync Database Reader
#
# This script demonstrates how to connect Python to MySQL
# and run queries against the original CareSync tables plus
# the newly added medicine, test_report and clinical_note tables.
#
# Tables used:
#   doctor
#   patient
#   appointment
#   billing
#   activity_log
#   medicine
#   test_report
#   clinical_note

import mysql.connector


# ─── DATABASE CONNECTION ────────────────────────────────────────────────────

# Best practice: in a real application, read the password from an
# environment variable or configuration file.
connection = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Pro64",
    database="healthcync"
)

cursor = connection.cursor(dictionary=True)

print("Connected to CareSync database.")
print("=" * 70)


# ─── QUERY 1: How many doctors in each specialisation? ──────────────────────

print()
print("QUERY 1: Doctor Count by Specialisation")
print("-" * 55)

cursor.execute(
    """
    SELECT
        specialisation,
        COUNT(*) AS total_doctors
    FROM doctor
    WHERE is_active = 1
    GROUP BY specialisation
    ORDER BY total_doctors DESC
    """
)

rows = cursor.fetchall()

for row in rows:
    print(
        f"  {row['specialisation']:<25} "
        f"{row['total_doctors']} doctors"
    )


# ─── QUERY 2: Revenue by billing status ─────────────────────────────────────

print()
print("QUERY 2: Revenue Summary by Bill Status")
print("-" * 55)

cursor.execute(
    """
    SELECT
        status,
        COUNT(*) AS total_bills,
        ROUND(SUM(total_amount), 2) AS total_billed,
        ROUND(SUM(amount_paid), 2) AS total_collected,
        ROUND(AVG(total_amount), 2) AS avg_bill_amount
    FROM billing
    GROUP BY status
    ORDER BY total_billed DESC
    """
)

rows = cursor.fetchall()

for row in rows:
    print(
        f"  {row['status']:<15} "
        f"Bills: {row['total_bills']:>5}  "
        f"Billed: Rs {row['total_billed']:>10}  "
        f"Collected: Rs {row['total_collected']:>10}"
    )


# ─── QUERY 3: Bill rejection rate ──────────────────────────────────────────

print()
print("QUERY 3: Bill Rejection Rate")
print("-" * 55)

cursor.execute(
    "SELECT COUNT(*) AS total FROM billing"
)

total_bills = cursor.fetchone()["total"]

cursor.execute(
    """
    SELECT COUNT(*) AS rejected
    FROM billing
    WHERE status = 'Rejected'
    """
)

rejected_bills = cursor.fetchone()["rejected"]

rejection_rate = (
    rejected_bills / total_bills * 100
    if total_bills > 0
    else 0
)

print(f"  Total Bills    : {total_bills}")
print(f"  Rejected Bills : {rejected_bills}")
print(f"  Rejection Rate : {rejection_rate:.2f}%")


# ─── QUERY 4: Top 5 busiest doctors ─────────────────────────────────────────

print()
print("QUERY 4: Top 5 Busiest Doctors by Appointments")
print("-" * 60)

cursor.execute(
    """
    SELECT
        d.full_name,
        d.specialisation,
        COUNT(a.appointment_id) AS total_appointments
    FROM doctor d
    JOIN appointment a
        ON a.doctor_id = d.doctor_id
    WHERE a.status = 'Completed'
    GROUP BY
        d.doctor_id,
        d.full_name,
        d.specialisation
    ORDER BY total_appointments DESC
    LIMIT 5
    """
)

rows = cursor.fetchall()

for i, row in enumerate(rows, start=1):
    print(
        f"  {i}. {row['full_name']:<30} "
        f"({row['specialisation']:<20}) "
        f"{row['total_appointments']} completed appointments"
    )


# ─── QUERY 5: Patients with more than 5 visits ─────────────────────────────

print()
print("QUERY 5: Patients With More Than 5 Completed Visits")
print("-" * 60)

cursor.execute(
    """
    SELECT
        p.full_name,
        p.blood_group,
        COUNT(a.appointment_id) AS visit_count
    FROM patient p
    JOIN appointment a
        ON a.patient_id = p.patient_id
    WHERE a.status = 'Completed'
      AND p.is_deleted = 0
    GROUP BY
        p.patient_id,
        p.full_name,
        p.blood_group
    HAVING visit_count > 5
    ORDER BY visit_count DESC
    LIMIT 10
    """
)

rows = cursor.fetchall()

if not rows:
    print("  No patients with more than 5 visits found.")
else:
    for row in rows:
        print(
            f"  {row['full_name']:<30} "
            f"Blood: {row['blood_group']:<4} "
            f"Visits: {row['visit_count']}"
        )


# ─── QUERY 6: Monthly appointment trend ─────────────────────────────────────

print()
print("QUERY 6: Monthly Appointment Count (Last 6 Months)")
print("-" * 60)

cursor.execute(
    """
    SELECT
        DATE_FORMAT(appointment_date, '%Y-%m') AS month,
        COUNT(*) AS total_appointments
    FROM appointment
    WHERE appointment_date >=
          DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
    GROUP BY month
    ORDER BY month ASC
    """
)

rows = cursor.fetchall()

for row in rows:
    print(
        f"  {row['month']}   "
        f"{row['total_appointments']} appointments"
    )


# ─── QUERY 7: Medicine records by patient ───────────────────────────────────

print()
print("QUERY 7: Patient Medicines")
print("-" * 55)

cursor.execute(
    """
    SELECT
        p.patient_id,
        p.full_name AS patient_name,
        m.medicine_name,
        m.dose,
        m.time
    FROM medicine m
    JOIN patient p
        ON p.patient_id = m.patient_id
    WHERE p.is_deleted = 0
    ORDER BY p.full_name, m.medicine_name
    LIMIT 20
    """
)

rows = cursor.fetchall()

if not rows:
    print("  No medicine records found.")
else:
    for row in rows:
        print(
            f"  Patient: {row['patient_name']:<25} "
            f"Medicine: {row['medicine_name']:<20} "
            f"Dose: {row['dose'] or '-':<10} "
            f"Time: {row['time'] or '-'}"
        )


# ─── QUERY 8: Medicine count by patient ─────────────────────────────────────

print()
print("QUERY 8: Patients With Most Medicine Records")
print("-" * 55)

cursor.execute(
    """
    SELECT
        p.patient_id,
        p.full_name AS patient_name,
        COUNT(m.medicine_id) AS medicine_count
    FROM patient p
    JOIN medicine m
        ON m.patient_id = p.patient_id
    WHERE p.is_deleted = 0
    GROUP BY
        p.patient_id,
        p.full_name
    ORDER BY medicine_count DESC
    LIMIT 10
    """
)

rows = cursor.fetchall()

for row in rows:
    print(
        f"  {row['patient_name']:<30} "
        f"Medicines: {row['medicine_count']}"
    )


# ─── QUERY 9: Test reports for patients ─────────────────────────────────────

print()
print("QUERY 9: Recent Test Reports")
print("-" * 55)

cursor.execute(
    """
    SELECT
        tr.report_id,
        p.full_name AS patient_name,
        tr.report_type,
        tr.report_date,
        tr.file_path
    FROM test_report tr
    JOIN patient p
        ON p.patient_id = tr.patient_id
    WHERE p.is_deleted = 0
    ORDER BY tr.report_date DESC
    LIMIT 20
    """
)

rows = cursor.fetchall()

if not rows:
    print("  No test reports found.")
else:
    for row in rows:
        print(
            f"  Report ID: {row['report_id']:<5} "
            f"Patient: {row['patient_name']:<25} "
            f"Type: {row['report_type']:<25} "
            f"Date: {row['report_date']} "
            f"File: {row['file_path'] or '-'}"
        )


# ─── QUERY 10: Test report count by type ────────────────────────────────────

print()
print("QUERY 10: Test Report Count by Type")
print("-" * 55)

cursor.execute(
    """
    SELECT
        report_type,
        COUNT(*) AS total_reports
    FROM test_report
    GROUP BY report_type
    ORDER BY total_reports DESC
    """
)

rows = cursor.fetchall()

for row in rows:
    print(
        f"  {row['report_type']:<30} "
        f"{row['total_reports']} reports"
    )


# ─── QUERY 11: Clinical notes with doctor and patient ───────────────────────

print()
print("QUERY 11: Recent Clinical Notes")
print("-" * 60)

cursor.execute(
    """
    SELECT
        cn.note_id,
        d.full_name AS doctor_name,
        p.full_name AS patient_name,
        cn.note,
        cn.created_at
    FROM clinical_note cn
    JOIN doctor d
        ON d.doctor_id = cn.doctor_id
    JOIN patient p
        ON p.patient_id = cn.patient_id
    WHERE p.is_deleted = 0
    ORDER BY cn.created_at DESC
    LIMIT 20
    """
)

rows = cursor.fetchall()

if not rows:
    print("  No clinical notes found.")
else:
    for row in rows:
        print()
        print(f"  Note ID : {row['note_id']}")
        print(f"  Doctor  : {row['doctor_name']}")
        print(f"  Patient : {row['patient_name']}")
        print(f"  Note    : {row['note']}")
        print(f"  Created : {row['created_at']}")


# ─── QUERY 12: Number of clinical notes written by each doctor ─────────────

print()
print("QUERY 12: Clinical Notes by Doctor")
print("-" * 55)

cursor.execute(
    """
    SELECT
        d.full_name AS doctor_name,
        d.specialisation,
        COUNT(cn.note_id) AS total_notes
    FROM doctor d
    JOIN clinical_note cn
        ON cn.doctor_id = d.doctor_id
    GROUP BY
        d.doctor_id,
        d.full_name,
        d.specialisation
    ORDER BY total_notes DESC
    LIMIT 10
    """
)

rows = cursor.fetchall()

for row in rows:
    print(
        f"  {row['doctor_name']:<30} "
        f"{row['specialisation']:<20} "
        f"Notes: {row['total_notes']}"
    )


# ─── QUERY 13: Complete patient clinical summary ───────────────────────────

print()
print("QUERY 13: Patient Clinical Summary")
print("-" * 65)

cursor.execute(
    """
    SELECT
        p.patient_id,
        p.full_name AS patient_name,
        COUNT(DISTINCT a.appointment_id) AS appointments,
        COUNT(DISTINCT m.medicine_id) AS medicines,
        COUNT(DISTINCT tr.report_id) AS test_reports,
        COUNT(DISTINCT cn.note_id) AS clinical_notes
    FROM patient p
    LEFT JOIN appointment a
        ON a.patient_id = p.patient_id
    LEFT JOIN medicine m
        ON m.patient_id = p.patient_id
    LEFT JOIN test_report tr
        ON tr.patient_id = p.patient_id
    LEFT JOIN clinical_note cn
        ON cn.patient_id = p.patient_id
    WHERE p.is_deleted = 0
    GROUP BY
        p.patient_id,
        p.full_name
    ORDER BY appointments DESC
    LIMIT 10
    """
)

rows = cursor.fetchall()

for row in rows:
    print(
        f"  {row['patient_name']:<30} "
        f"Appointments: {row['appointments']:<4} "
        f"Medicines: {row['medicines']:<3} "
        f"Reports: {row['test_reports']:<3} "
        f"Notes: {row['clinical_notes']:<3}"
    )


# ─── QUERY 14: Overall database summary ─────────────────────────────────────

print()
print("QUERY 14: CareSync Database Summary")
print("-" * 55)

summary_queries = {
    "Doctors": "SELECT COUNT(*) AS total FROM doctor",
    "Patients": "SELECT COUNT(*) AS total FROM patient WHERE is_deleted = 0",
    "Appointments": "SELECT COUNT(*) AS total FROM appointment",
    "Bills": "SELECT COUNT(*) AS total FROM billing",
    "Medicines": "SELECT COUNT(*) AS total FROM medicine",
    "Test Reports": "SELECT COUNT(*) AS total FROM test_report",
    "Clinical Notes": "SELECT COUNT(*) AS total FROM clinical_note",
    "Activity Logs": "SELECT COUNT(*) AS total FROM activity_log"
}

for label, query in summary_queries.items():
    cursor.execute(query)
    total = cursor.fetchone()["total"]
    print(f"  {label:<20}: {total}")


# ─── QUERY 15: Patient dashboard details ────────────────────────────────────

print()
print("QUERY 15: Patient Dashboard Details")
print("-" * 65)

cursor.execute(
    """
    SELECT
        p.patient_id,
        p.full_name,
        p.gender,
        p.blood_group,
        COUNT(DISTINCT a.appointment_id) AS appointments,
        COUNT(DISTINCT m.medicine_id) AS medicines,
        COUNT(DISTINCT tr.report_id) AS reports,
        COUNT(DISTINCT cn.note_id) AS notes
    FROM patient p
    LEFT JOIN appointment a
        ON a.patient_id = p.patient_id
    LEFT JOIN medicine m
        ON m.patient_id = p.patient_id
    LEFT JOIN test_report tr
        ON tr.patient_id = p.patient_id
    LEFT JOIN clinical_note cn
        ON cn.patient_id = p.patient_id
    WHERE p.is_deleted = 0
    GROUP BY
        p.patient_id,
        p.full_name,
        p.gender,
        p.blood_group
    ORDER BY p.created_at DESC
    LIMIT 20
    """
)

rows = cursor.fetchall()

for row in rows:
    print(
        f"  ID: {row['patient_id']:<4} "
        f"{row['full_name']:<28} "
        f"{row['gender']:<8} "
        f"Blood: {row['blood_group']:<4} "
        f"Appointments: {row['appointments']:<3} "
        f"Medicines: {row['medicines']:<3} "
        f"Reports: {row['reports']:<3} "
        f"Notes: {row['notes']:<3}"
    )


# ─── FINAL MESSAGE ─────────────────────────────────────────────────────────

print()
print("=" * 70)
print("All healthcync queries completed successfully.")
print("=" * 70)


# ─── CLEANUP ────────────────────────────────────────────────────────────────

cursor.close()
connection.close()

print("Database connection closed.")
