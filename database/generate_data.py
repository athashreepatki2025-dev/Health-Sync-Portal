
# HealthSync Sample Data Generator
#
# This script populates the CareSync MySQL database with realistic test data.
# It supports the original tables:
#   doctor, patient, appointment, billing, activity_log
#
# It also populates the added tables:
#   medicine, test_report, clinical_note
#
# Run this script ONCE after creating all database tables.
#
# Required libraries:
#   pip install mysql-connector-python Faker

import mysql.connector
import random
from faker import Faker
from datetime import date, timedelta, datetime
from decimal import Decimal

# Create a Faker instance set to India.
fake = Faker("en_IN")

# ─── DATABASE CONNECTION ────────────────────────────────────────────────────

connection = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Pro64",
    database="healthcync"
)

cursor = connection.cursor()

print("Connected to MySQL successfully.")

# ─── CONSTANTS ──────────────────────────────────────────────────────────────

NUM_DOCTORS = 40
NUM_PATIENTS = 500
NUM_APPOINTMENTS = 3000
NUM_BILLS = 2500

# New tables
MEDICINES_PER_PATIENT_MIN = 1
MEDICINES_PER_PATIENT_MAX = 3
REPORTS_PER_PATIENT_MIN = 0
REPORTS_PER_PATIENT_MAX = 3
NOTES_PER_PATIENT_MIN = 1
NOTES_PER_PATIENT_MAX = 3

BILL_REJECT_LOW = 0.08
BILL_REJECT_HIGH = 0.12

SPECIALISATIONS = [
    "Cardiology",
    "General Medicine",
    "Orthopaedics",
    "Gynaecology",
    "Paediatrics",
    "Neurology",
    "Dermatology",
    "Ophthalmology",
    "ENT",
    "Psychiatry",
    "Oncology",
    "Urology",
    "Endocrinology"
]

BLOOD_GROUPS = [
    "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"
]

DIAGNOSES = [
    "Hypertension",
    "Type 2 Diabetes",
    "Upper Respiratory Infection",
    "Migraine",
    "Lumbar Spondylosis",
    "Anxiety Disorder",
    "Anaemia",
    "Hypothyroidism",
    "Gastritis",
    "Urinary Tract Infection",
    "Dengue Fever",
    "Viral Fever",
    "Asthma",
    "Arthritis",
    "Obesity",
    "Iron Deficiency",
    "Vitamin D Deficiency",
    "Sinusitis",
    "Eczema"
]

MEDICINE_NAMES = [
    ("Paracetamol", "500 mg"),
    ("Amoxicillin", "500 mg"),
    ("Azithromycin", "500 mg"),
    ("Metformin", "500 mg"),
    ("Amlodipine", "5 mg"),
    ("Pantoprazole", "40 mg"),
    ("Cetirizine", "10 mg"),
    ("Ibuprofen", "400 mg"),
    ("Levothyroxine", "50 mcg"),
    ("Atorvastatin", "10 mg"),
    ("Omeprazole", "20 mg"),
    ("Diclofenac", "50 mg"),
    ("Montelukast", "10 mg"),
    ("Vitamin D3", "60,000 IU"),
    ("Iron Supplement", "100 mg")
]

MEDICINE_TIMES = [
    "Morning",
    "Afternoon",
    "Evening",
    "Night",
    "Morning and Night",
    "After Breakfast",
    "After Lunch",
    "After Dinner"
]

TEST_TYPES = [
    "CBC",
    "Blood Sugar",
    "Lipid Profile",
    "Liver Function Test",
    "Kidney Function Test",
    "Thyroid Profile",
    "Urine Test",
    "X-Ray",
    "MRI",
    "CT Scan",
    "ECG",
    "Ultrasound"
]

REJECTION_REASONS = [
    "Insurance claim limit exceeded for this policy year.",
    "Procedure not covered under current insurance plan.",
    "Pre-authorisation was not obtained before treatment.",
    "Patient not eligible under submitted insurance policy number.",
    "Duplicate claim submitted for the same service date.",
    "Medical documents submitted are incomplete.",
    "Claim submitted after the deadline specified by insurer."
]

CLINICAL_NOTE_TEMPLATES = [
    "Patient reports improvement in symptoms. Continue current treatment.",
    "Patient advised to maintain regular medication and follow-up.",
    "Vitals reviewed. No immediate complications observed.",
    "Patient advised to undergo the recommended diagnostic tests.",
    "Symptoms discussed with patient. Treatment plan explained.",
    "Follow-up consultation recommended after completion of tests.",
    "Patient advised regarding diet, rest and medication schedule."
]


# ─── STEP 1: INSERT DOCTORS ─────────────────────────────────────────────────

print(f"Inserting {NUM_DOCTORS} doctors...")

doctor_ids = []

for i in range(NUM_DOCTORS):
    name = "Dr. " + fake.name()
    spec = random.choice(SPECIALISATIONS)
    phone = "9" + str(random.randint(100000000, 999999999))
    email = f"doctor{i + 1}@caresync.in"
    licence = f"MCI-{2000 + i:04d}"

    cursor.execute(
        """
        INSERT INTO doctor
            (full_name, specialisation, phone, email, licence_number)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (name, spec, phone, email, licence)
    )

    doctor_ids.append(cursor.lastrowid)

connection.commit()
print(f"Done. Inserted {len(doctor_ids)} doctors.")


# ─── STEP 2: INSERT PATIENTS ────────────────────────────────────────────────

print(f"Inserting {NUM_PATIENTS} patients...")

patient_ids = []

for i in range(NUM_PATIENTS):
    name = fake.name()
    dob = fake.date_of_birth(minimum_age=5, maximum_age=85)
    gender = random.choice(["Male", "Female"])
    phone = "9" + str(random.randint(100000000, 999999999))
    email = f"patient{i + 1}@example.com"
    address = fake.address().replace("\n", ", ")
    blood = random.choice(BLOOD_GROUPS)
    ec_name = fake.name()
    ec_phone = "9" + str(random.randint(100000000, 999999999))

    cursor.execute(
        """
        INSERT INTO patient
            (full_name, date_of_birth, gender, phone, email, address,
             blood_group, emergency_contact_name, emergency_contact_phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            name,
            dob,
            gender,
            phone,
            email,
            address,
            blood,
            ec_name,
            ec_phone
        )
    )

    patient_ids.append(cursor.lastrowid)

connection.commit()
print(f"Done. Inserted {len(patient_ids)} patients.")


# ─── STEP 3: INSERT APPOINTMENTS ────────────────────────────────────────────

print(f"Inserting {NUM_APPOINTMENTS} appointments...")

appointment_ids = []

# Generate appointments over the past 2 years.
start_date = date.today() - timedelta(days=730)
end_date = date.today()

hour_options = list(range(9, 17))
minute_options = [0, 15, 30, 45]

for _ in range(NUM_APPOINTMENTS):
    p_id = random.choice(patient_ids)
    d_id = random.choice(doctor_ids)

    appt_dt = start_date + timedelta(
        days=random.randint(0, (end_date - start_date).days)
    )

    appt_tm = (
        f"{random.choice(hour_options):02d}:"
        f"{random.choice(minute_options):02d}:00"
    )

    reason = "Patient complaints of " + random.choice(DIAGNOSES).lower()
    diag = random.choice(DIAGNOSES)

    # 80% Completed, 10% Scheduled, 10% Cancelled.
    status = random.choices(
        ["Completed", "Scheduled", "Cancelled"],
        weights=[80, 10, 10]
    )[0]

    cursor.execute(
        """
        INSERT INTO appointment
            (patient_id, doctor_id, appointment_date, appointment_time,
             reason, diagnosis, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (p_id, d_id, appt_dt, appt_tm, reason, diag, status)
    )

    appointment_ids.append(cursor.lastrowid)

connection.commit()
print(f"Done. Inserted {len(appointment_ids)} appointments.")


# ─── STEP 4: INSERT BILLS ───────────────────────────────────────────────────

print(f"Inserting up to {NUM_BILLS} bills...")

cursor.execute(
    """
    SELECT appointment_id, patient_id
    FROM appointment
    WHERE status = %s
    """,
    ("Completed",)
)

completed_appointments = cursor.fetchall()

if len(completed_appointments) < NUM_BILLS:
    print(
        f"Note: Only {len(completed_appointments)} completed "
        f"appointments available."
    )
    bills_to_create = completed_appointments
else:
    bills_to_create = random.sample(
        completed_appointments,
        NUM_BILLS
    )

reject_rate = random.uniform(
    BILL_REJECT_LOW,
    BILL_REJECT_HIGH
)

print(
    f"Bill rejection rate for this run: "
    f"{reject_rate * 100:.1f}%"
)

bills_inserted = 0

for appt_id, p_id in bills_to_create:
    total = round(random.uniform(300, 3000), 2)

    rand_val = random.random()

    if rand_val < reject_rate:
        status = "Rejected"
        amount_paid = 0.00
        discount = 0.00
        reject_reason = random.choice(REJECTION_REASONS)

    elif rand_val < reject_rate + 0.10:
        status = "Partially Paid"
        paid_pct = random.uniform(0.30, 0.70)
        amount_paid = round(total * paid_pct, 2)
        discount = 0.00
        reject_reason = None

    elif rand_val < reject_rate + 0.15:
        status = "Pending"
        amount_paid = 0.00
        discount = 0.00
        reject_reason = None

    else:
        status = "Paid"
        discount = round(
            total * random.uniform(0, 0.05),
            2
        )
        amount_paid = round(
            total - discount,
            2
        )
        reject_reason = None

    cursor.execute(
        """
        SELECT appointment_date
        FROM appointment
        WHERE appointment_id = %s
        """,
        (appt_id,)
    )

    row = cursor.fetchone()
    appt_date = row[0]

    bill_date = appt_date + timedelta(
        days=random.randint(0, 2)
    )
    due_date = bill_date + timedelta(days=30)

    cursor.execute(
        """
        INSERT INTO billing
            (appointment_id, patient_id, total_amount, amount_paid,
             discount, status, rejection_reason, bill_date, due_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            appt_id,
            p_id,
            total,
            amount_paid,
            discount,
            status,
            reject_reason,
            bill_date,
            due_date
        )
    )

    bills_inserted += 1

connection.commit()
print(f"Done. Inserted {bills_inserted} bills.")


# ─── STEP 5: INSERT MEDICINES ───────────────────────────────────────────────

print("Inserting medicines...")

medicine_rows = 0

for p_id in patient_ids:
    number_of_medicines = random.randint(
        MEDICINES_PER_PATIENT_MIN,
        MEDICINES_PER_PATIENT_MAX
    )

    selected_medicines = random.sample(
        MEDICINE_NAMES,
        number_of_medicines
    )

    for medicine_name, dose in selected_medicines:
        medicine_time = random.choice(MEDICINE_TIMES)

        cursor.execute(
            """
            INSERT INTO medicine
                (medicine_name, dose, time, patient_id)
            VALUES (%s, %s, %s, %s)
            """,
            (
                medicine_name,
                dose,
                medicine_time,
                p_id
            )
        )

        medicine_rows += 1

connection.commit()
print(f"Done. Inserted {medicine_rows} medicine records.")


# ─── STEP 6: INSERT TEST REPORTS ────────────────────────────────────────────

print("Inserting test reports...")

test_report_rows = 0

for p_id in patient_ids:
    number_of_reports = random.randint(
        REPORTS_PER_PATIENT_MIN,
        REPORTS_PER_PATIENT_MAX
    )

    for _ in range(number_of_reports):
        report_type = random.choice(TEST_TYPES)
        report_date = date.today() - timedelta(
            days=random.randint(0, 730)
        )

        # Sample file path. Replace with your real file-storage path
        # when connecting the FastAPI file-upload feature.
        file_path = (
            f"/uploads/test_reports/"
            f"patient_{p_id}_{report_type.replace(' ', '_').lower()}.pdf"
        )

        cursor.execute(
            """
            INSERT INTO test_report
                (patient_id, report_type, report_date, file_path)
            VALUES (%s, %s, %s, %s)
            """,
            (
                p_id,
                report_type,
                report_date,
                file_path
            )
        )

        test_report_rows += 1

connection.commit()
print(f"Done. Inserted {test_report_rows} test reports.")


# ─── STEP 7: INSERT CLINICAL NOTES ──────────────────────────────────────────

print("Inserting clinical notes...")

clinical_note_rows = 0

for p_id in patient_ids:
    number_of_notes = random.randint(
        NOTES_PER_PATIENT_MIN,
        NOTES_PER_PATIENT_MAX
    )

    for _ in range(number_of_notes):
        d_id = random.choice(doctor_ids)

        note_text = random.choice(CLINICAL_NOTE_TEMPLATES)

        cursor.execute(
            """
            INSERT INTO clinical_note
                (doctor_id, patient_id, note)
            VALUES (%s, %s, %s)
            """,
            (
                d_id,
                p_id,
                note_text
            )
        )

        clinical_note_rows += 1

connection.commit()
print(f"Done. Inserted {clinical_note_rows} clinical notes.")


# ─── STEP 8: VERIFY ROW COUNTS ──────────────────────────────────────────────

print()
print("=== FINAL ROW COUNTS ===")

tables = [
    "doctor",
    "patient",
    "appointment",
    "billing",
    "medicine",
    "test_report",
    "clinical_note",
    "activity_log"
]

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table:20s}: {count} rows")


# ─── CLEANUP ────────────────────────────────────────────────────────────────

cursor.close()
connection.close()

print()
print("Done. HealthSync database is ready for use.")
