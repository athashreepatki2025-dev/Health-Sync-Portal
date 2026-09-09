
# main.py
# HealthSync Dashboard Backend
#
# This file is a FastAPI application.
# It connects to the MySQL database and provides API endpoints.
# The Vue.js frontend will call these endpoints to get data.
#
# To run this file:
#     uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from fastapi import FastAPI, HTTPException


# ── Create the FastAPI application ───────────────────────────────────────────

app = FastAPI(title='HealthSync Dashboard API')


# ── CORS Configuration ───────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['GET'],
    allow_headers=['*'],
)


# ── Database connection helper ───────────────────────────────────────────────

def get_db():
    return mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        password='Pro64',
        database='healthcync'
    )


# ── ENDPOINT 1: Summary numbers ──────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/summary

@app.get('/summary')
def get_summary():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Count active patients
    cursor.execute(
        'SELECT COUNT(*) AS total FROM patient WHERE is_deleted = 0'
    )
    patients = cursor.fetchone()['total']

    # Count active doctors
    cursor.execute(
        'SELECT COUNT(*) AS total FROM doctor WHERE is_active = 1'
    )
    doctors = cursor.fetchone()['total']

    # Count all appointments
    cursor.execute(
        'SELECT COUNT(*) AS total FROM appointment'
    )
    appointments = cursor.fetchone()['total']

    # Count all bills
    cursor.execute(
        'SELECT COUNT(*) AS total FROM billing'
    )
    bills = cursor.fetchone()['total']

    # Count rejected bills
    cursor.execute(
        "SELECT COUNT(*) AS total FROM billing WHERE status = 'Rejected'"
    )
    rejected = cursor.fetchone()['total']

    # Calculate rejection percentage
    rejection_rate = round(
        (rejected / bills * 100), 1
    ) if bills > 0 else 0

    # Total revenue collected
    cursor.execute(
        'SELECT ROUND(SUM(amount_paid), 2) AS total FROM billing'
    )
    revenue = cursor.fetchone()['total'] or 0

    # Count medicines
    cursor.execute(
        'SELECT COUNT(*) AS total FROM medicine'
    )
    medicines = cursor.fetchone()['total']

    # Count test reports
    cursor.execute(
        'SELECT COUNT(*) AS total FROM test_report'
    )
    test_reports = cursor.fetchone()['total']

    # Count clinical notes
    cursor.execute(
        'SELECT COUNT(*) AS total FROM clinical_note'
    )
    clinical_notes = cursor.fetchone()['total']

    cursor.close()
    db.close()

    return {
        'total_patients': patients,
        'total_doctors': doctors,
        'total_appointments': appointments,
        'total_bills': bills,
        'rejection_rate': rejection_rate,
        'total_revenue': float(revenue),
        'total_medicines': medicines,
        'total_test_reports': test_reports,
        'total_clinical_notes': clinical_notes
    }


# ── ENDPOINT 2: Patient list ─────────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/patients

@app.get('/patients')
def get_patients():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            patient_id,
            full_name,
            gender,
            blood_group,
            DATE_FORMAT(date_of_birth, '%d %b %Y') AS date_of_birth,
            DATE_FORMAT(created_at, '%d %b %Y') AS registered_on
        FROM patient
        WHERE is_deleted = 0
        ORDER BY created_at DESC
        LIMIT 50
        '''
    )

    patients = cursor.fetchall()

    cursor.close()
    db.close()

    return {'patients': patients}


# ── ENDPOINT 3: Billing summary ──────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/billing

@app.get('/billing')
def get_billing():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            b.bill_id,
            p.full_name AS patient_name,
            b.total_amount,
            b.amount_paid,
            b.status,
            DATE_FORMAT(b.bill_date, '%d %b %Y') AS bill_date
        FROM billing b
        JOIN patient p
            ON p.patient_id = b.patient_id
        ORDER BY b.created_at DESC
        LIMIT 50
        '''
    )

    bills = cursor.fetchall()

    # Convert Decimal values to float
    for bill in bills:
        bill['total_amount'] = float(bill['total_amount'])
        bill['amount_paid'] = float(bill['amount_paid'])

    cursor.close()
    db.close()

    return {'bills': bills}


# ── ENDPOINT 4: Doctor list ──────────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/doctors

@app.get('/doctors')
def get_doctors():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            d.doctor_id,
            d.full_name,
            d.specialisation,
            COUNT(a.appointment_id) AS total_appointments
        FROM doctor d
        LEFT JOIN appointment a
            ON a.doctor_id = d.doctor_id
            AND a.status = 'Completed'
        WHERE d.is_active = 1
        GROUP BY
            d.doctor_id,
            d.full_name,
            d.specialisation
        ORDER BY total_appointments DESC
        '''
    )

    doctors = cursor.fetchall()

    cursor.close()
    db.close()

    return {'doctors': doctors}


# ── ENDPOINT 5: Appointment list ─────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/appointments

@app.get('/appointments')
def get_appointments():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            a.appointment_id,
            p.full_name AS patient_name,
            d.full_name AS doctor_name,
            d.specialisation,
            DATE_FORMAT(
                a.appointment_date,
                '%d %b %Y'
            ) AS appointment_date,
            TIME_FORMAT(
                a.appointment_time,
                '%H:%i'
            ) AS appointment_time,
            a.reason,
            a.diagnosis,
            a.notes,
            a.status
        FROM appointment a
        JOIN patient p
            ON p.patient_id = a.patient_id
        JOIN doctor d
            ON d.doctor_id = a.doctor_id
        ORDER BY
            a.appointment_date DESC,
            a.appointment_time DESC
        LIMIT 50
        '''
    )

    appointments = cursor.fetchall()

    cursor.close()
    db.close()

    return {'appointments': appointments}


# ── ENDPOINT 6: Medicine list ────────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/medicines

@app.get('/medicines')
def get_medicines():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            m.medicine_id,
            m.medicine_name,
            m.dose,
            m.time,
            p.patient_id,
            p.full_name AS patient_name,
            DATE_FORMAT(
                m.created_at,
                '%d %b %Y'
            ) AS created_on
        FROM medicine m
        JOIN patient p
            ON p.patient_id = m.patient_id
        WHERE p.is_deleted = 0
        ORDER BY m.created_at DESC
        LIMIT 100
        '''
    )

    medicines = cursor.fetchall()

    cursor.close()
    db.close()

    return {'medicines': medicines}


# ── ENDPOINT 7: Test report list ─────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/test-reports

@app.get('/test-reports')
def get_test_reports():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            t.report_id,
            t.report_type,
            DATE_FORMAT(
                t.report_date,
                '%d %b %Y'
            ) AS report_date,
            t.file_path,
            p.patient_id,
            p.full_name AS patient_name
        FROM test_report t
        JOIN patient p
            ON p.patient_id = t.patient_id
        WHERE p.is_deleted = 0
        ORDER BY t.report_date DESC
        LIMIT 100
        '''
    )

    reports = cursor.fetchall()

    cursor.close()
    db.close()

    return {'test_reports': reports}


# ── ENDPOINT 8: Clinical note list ───────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/clinical-notes

@app.get('/clinical-notes')
def get_clinical_notes():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            c.note_id,
            d.doctor_id,
            d.full_name AS doctor_name,
            d.specialisation,
            p.patient_id,
            p.full_name AS patient_name,
            c.note,
            DATE_FORMAT(
                c.created_at,
                '%d %b %Y %H:%i'
            ) AS created_at,
            DATE_FORMAT(
                c.updated_at,
                '%d %b %Y %H:%i'
            ) AS updated_at
        FROM clinical_note c
        JOIN doctor d
            ON d.doctor_id = c.doctor_id
        JOIN patient p
            ON p.patient_id = c.patient_id
        WHERE p.is_deleted = 0
        ORDER BY c.created_at DESC
        LIMIT 100
        '''
    )

    notes = cursor.fetchall()

    cursor.close()
    db.close()

    return {'clinical_notes': notes}


# ── ENDPOINT 9: Activity log ─────────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/activity-logs

@app.get('/activity-logs')
def get_activity_logs():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            log_id,
            user_type,
            user_id,
            action,
            target_table,
            target_id,
            old_value,
            new_value,
            ip_address,
            DATE_FORMAT(
                logged_at,
                '%d %b %Y %H:%i:%s'
            ) AS logged_at
        FROM activity_log
        ORDER BY logged_at DESC
        LIMIT 100
        '''
    )

    logs = cursor.fetchall()

    cursor.close()
    db.close()

    return {'activity_logs': logs}


# ── ENDPOINT 10: Patient complete clinical summary ───────────────────────────
#
# URL:
# http://127.0.0.1:8000/patient-summary

@app.get('/patient-summary')
def get_patient_summary():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            p.patient_id,
            p.full_name,
            p.gender,
            p.blood_group,
            p.phone,
            p.email,

            (
                SELECT COUNT(*)
                FROM appointment a
                WHERE a.patient_id = p.patient_id
            ) AS total_appointments,

            (
                SELECT COUNT(*)
                FROM medicine m
                WHERE m.patient_id = p.patient_id
            ) AS total_medicines,

            (
                SELECT COUNT(*)
                FROM test_report t
                WHERE t.patient_id = p.patient_id
            ) AS total_test_reports,

            (
                SELECT COUNT(*)
                FROM clinical_note c
                WHERE c.patient_id = p.patient_id
            ) AS total_clinical_notes,

            (
                SELECT COUNT(*)
                FROM billing b
                WHERE b.patient_id = p.patient_id
            ) AS total_bills

        FROM patient p
        WHERE p.is_deleted = 0
        ORDER BY p.created_at DESC
        LIMIT 50
        '''
    )

    patients = cursor.fetchall()

    cursor.close()
    db.close()

    return {'patient_summary': patients}


# ── ENDPOINT 11: Medicine summary ────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/medicine-summary

@app.get('/medicine-summary')
def get_medicine_summary():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            m.medicine_name,
            COUNT(*) AS total_records,
            COUNT(DISTINCT m.patient_id) AS total_patients
        FROM medicine m
        JOIN patient p
            ON p.patient_id = m.patient_id
        WHERE p.is_deleted = 0
        GROUP BY m.medicine_name
        ORDER BY total_records DESC
        '''
    )

    medicines = cursor.fetchall()

    cursor.close()
    db.close()

    return {'medicine_summary': medicines}


# ── ENDPOINT 12: Test report summary ─────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/test-report-summary

@app.get('/test-report-summary')
def get_test_report_summary():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            report_type,
            COUNT(*) AS total_reports,
            COUNT(DISTINCT patient_id) AS total_patients
        FROM test_report
        GROUP BY report_type
        ORDER BY total_reports DESC
        '''
    )

    reports = cursor.fetchall()

    cursor.close()
    db.close()

    return {'test_report_summary': reports}


# ── ENDPOINT 13: Clinical note summary ───────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/clinical-note-summary

@app.get('/clinical-note-summary')
def get_clinical_note_summary():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT
            d.doctor_id,
            d.full_name AS doctor_name,
            d.specialisation,
            COUNT(c.note_id) AS total_notes
        FROM doctor d
        LEFT JOIN clinical_note c
            ON c.doctor_id = d.doctor_id
        WHERE d.is_active = 1
        GROUP BY
            d.doctor_id,
            d.full_name,
            d.specialisation
        ORDER BY total_notes DESC
        '''
    )

    notes = cursor.fetchall()

    cursor.close()
    db.close()

    return {'clinical_note_summary': notes}


# ── ENDPOINT 14: Database table counts ───────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/database-summary

@app.get('/database-summary')
def get_database_summary():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    tables = [
        'doctor',
        'patient',
        'appointment',
        'billing',
        'activity_log',
        'medicine',
        'test_report',
        'clinical_note'
    ]

    result = {}

    for table in tables:
        cursor.execute(
            f'SELECT COUNT(*) AS total FROM `{table}`'
        )
        result[table] = cursor.fetchone()['total']

    cursor.close()
    db.close()

    return {'database_summary': result}


# ── ROOT ENDPOINT ────────────────────────────────────────────────────────────
#
# URL:
# http://127.0.0.1:8000/

@app.get('/')
def root():

    return {
        'message': 'CareSync Dashboard API is running',
        'endpoints': [
            '/summary',
            '/patients',
            '/billing',
            '/doctors',
            '/appointments',
            '/medicines',
            '/test-reports',
            '/clinical-notes',
            '/activity-logs',
            '/patient-summary',
            '/medicine-summary',
            '/test-report-summary',
            '/clinical-note-summary',
            '/database-summary'
        ]
    }
@app.get('/patients/{patient_id}')
def get_patient_by_id(patient_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute('''
        SELECT
            patient_id,
            full_name,
            date_of_birth,
            gender,
            phone,
            email,
            address,
            blood_group,
            emergency_contact_name,
            emergency_contact_phone,
            is_deleted,
            created_at,
            updated_at
        FROM patient
        WHERE patient_id = %s
          AND is_deleted = 0
    ''', (patient_id,))

    patient = cursor.fetchone()

    cursor.close()
    db.close()

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail='Patient not found'
        )

    return patient
{
  "detail": "Patient not found"
}

@app.get('/patients/{patient_id}/appointments')
def get_patient_appointments(patient_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute('''
        SELECT
            a.appointment_id,
            a.patient_id,
            p.full_name AS patient_name,
            a.doctor_id,
            d.full_name AS doctor_name,
            d.specialisation,
            a.appointment_date,
            a.appointment_time,
            a.reason,
            a.diagnosis,
            a.notes,
            a.status
        FROM appointment a
        JOIN patient p
            ON a.patient_id = p.patient_id
        JOIN doctor d
            ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (patient_id,))

    appointments = cursor.fetchall()

    cursor.close()
    db.close()

    return {
        'appointments': appointments
    }