from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'qwery321';

DATABASE = 'cardb.db'

selectVehiclesWithOwnerName = """
    select vehicles.id as id
    , COALESCE(vehicles.rsz, '-') as rendszam
    , strftime('%Y-%m-%d %H:%M:%S', vehicles.created, 'unixepoch') AS created
    , owners.name as owner
    , owners.email as email
    from vehicles
    left join owners on vehicles.ownerId = owners.id and owners.deleted = 0 
    where vehicles.deleted = 0 order by vehicles.rsz
    """
selectVehicles = "select id, rsz from vehicles where deleted = 0 order by rsz"
selectOwners = "select id, name, phone, email, strftime('%Y-%m-%d %H:%M:%S', created, 'unixepoch') as created from owners where deleted = 0 order by name"
selectEmployees = "select id, name from employees where deleted = 0 order by name"
selectStatuses = "select id, statusText as name from status where deleted = 0"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    sqlSelect = """
    select 
    jobs.id 
    , vehicles.rsz as rendszam
    , jobs.comment as comment
    , DATETIME(jobs.created, 'unixepoch') as created
    , owners.name as name
    , owners.phone as phone
    , owners.email as email
    , employees.name as employeename
    , status.statusText as status
    from jobs
    left join owners on jobs.ownerId = owners.id and owners.deleted = 0
    left join vehicles on jobs.vehicleId = vehicles.id and vehicles.deleted = 0
    left join status on jobs.statusId = status.id and status.deleted = 0
    left join employees on jobs.employeeId = employees.id and employees.deleted = 0
    where jobs.deleted = 0 and jobs.statusId < 5""";
    conn = get_db()
    cursor = conn.execute(sqlSelect)
    items = cursor.fetchall()
    conn.close()
    return render_template('index.html',items=items)

@app.route('/archive')
def archive():
    sqlSelect = """
    select 
    jobs.id 
    , vehicles.rsz as rendszam
    , jobs.comment as comment
    , DATETIME(jobs.created, 'unixepoch') as created
    , owners.name as name
    , owners.phone as phone
    , owners.email as email
    , employees.name as employeename
    , status.statusText as status
    from jobs
    left join owners on jobs.ownerId = owners.id and owners.deleted = 0
    left join vehicles on jobs.vehicleId = vehicles.id and vehicles.deleted = 0
    left join status on jobs.statusId = status.id and status.deleted = 0
    left join employees on jobs.employeeId = employees.id and employees.deleted = 0
    where jobs.deleted = 0 and jobs.statusId = 5 order by rendszam""";
    conn = get_db()
    cursor = conn.execute(sqlSelect)
    items = cursor.fetchall()
    conn.close()
    return render_template('archive.html',items=items)

@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    conn = get_db()
    cursor = conn.execute(selectOwners)
    owners = cursor.fetchall()
    cursor = conn.execute(selectVehiclesWithOwnerName)
    vehicles = cursor.fetchall()

    if request.method == 'POST':
        rsz = request.form['rsz']
        ownerId = request.form['ownerId']
        created = int(time.time())
        deleted = 0

        if '-' not in rsz:
            flash('A rendszámnak tartalmaznia kell egy kötőjelet!', 'danger')
        else:
            conn.execute('INSERT INTO vehicles (rsz, ownerId, created, deleted) VALUES (?, ?, ?, ?)',
                        (rsz, ownerId, created, deleted))
            conn.commit()
            flash('Jármű sikeresen hozzáadva az adatbázishoz!', 'success')
            cursor = conn.execute(selectVehiclesWithOwnerName)
            vehicles = cursor.fetchall()
    conn.close()

    return render_template('add_vehicle.html', vehicles=vehicles, owners=owners)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    conn = get_db()
    cursor = conn.execute(selectEmployees)
    employees = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        created = int(time.time())
        deleted = 0
        
        conn = get_db()
        conn.execute('INSERT INTO employees (name, created, deleted) VALUES (?, ?, ?)',
                     (name, created, deleted))
        conn.commit()
        flash('Alkalmazott sikeresen hozzáadva az adatbázishoz!', 'success')
        cursor = conn.execute(selectEmployees)
        employees = cursor.fetchall()
        conn.close()
        """ return redirect(url_for('index')) """
    
    return render_template('add_employee.html', employees = employees)

@app.route('/add_owner', methods=['GET', 'POST'])
def add_owner():
    conn = get_db()
    cursor = conn.execute(selectOwners)
    owners = cursor.fetchall()
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        created = int(time.time())
        deleted = 0
        
        conn = get_db()
        conn.execute('INSERT INTO owners (name, phone, created, deleted, email) VALUES (?, ?, ?, ?, ?)',
                     (name, phone, created, deleted, email))
        conn.commit()
        flash('Tulajdonos sikeresen hozzáadva az adatbázishoz!', 'success')
        """ return redirect(url_for('index')) """
        cursor = conn.execute(selectOwners)
        owners = cursor.fetchall()
        conn.close()
    
    return render_template('add_owner.html', owners = owners)

@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    conn = get_db()
    cursor = conn.execute(selectOwners)
    owners = cursor.fetchall()
    cursor = conn.execute(selectVehicles)
    vehicles = cursor.fetchall()
    cursor = conn.execute(selectEmployees)
    employees = cursor.fetchall()
    if request.method == 'POST':
        ownerId = int(request.form['ownerId'])
        vehicleId = int(request.form['vehicleId'])
        employeeId = int(request.form['employeeId'])
        comment = request.form['comment']
        created = int(time.time())
        deleted = 0
        statusId = 1

        if ownerId == 0 or vehicleId == 0 or employeeId == 0:
            flash("Minden mező kitöltése kötelező!")
        else:
            conn.execute('INSERT INTO jobs (ownerId, vehicleId, employeeId, comment, created, deleted) VALUES (?, ?, ?, ?, ?, ?)',
                     (ownerId, vehicleId, employeeId, comment, created, deleted))
            conn.commit()
        
        flash('Munka sikeresen hozzáadva az adatbázishoz!', 'success')
        """ return redirect(url_for('index')) """
    conn.close()
    return render_template('add_job.html',owners = owners, vehicles = vehicles, employees = employees)

@app.route('/delete_vehicle/<int:vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id):
    conn = get_db()
    conn.execute("UPDATE vehicles SET deleted = 1 WHERE id = ?", (vehicle_id,))
    conn.commit()
    conn.close()
    flash("A jármű sikeresen törölve lett.", "success")
    return redirect(url_for('add_vehicle'))

@app.route('/delete_employee/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    conn = get_db()
    conn.execute("UPDATE employees SET deleted = 1 WHERE id = ?", (employee_id,))
    conn.commit()
    conn.close()
    flash("Az alkalmazott sikeresen törölve lett az adatbázisból.", "success")
    return redirect(url_for('add_employee'))

@app.route('/delete_owner/<int:owner_id>', methods=['POST'])
def delete_owner(owner_id):
    conn = get_db()
    conn.execute("UPDATE owners SET deleted = 1 WHERE id = ?", (owner_id,))
    conn.commit()
    conn.close()
    flash("A tulajdonos sikeresen törölve lett az adatbázisból.", "success")
    return redirect(url_for('add_owner'))

@app.route('/view_job/<int:job_id>', methods=['GET', 'POST'])
def job_task(job_id):
    conn = get_db()

    if request.method == 'POST':
        new_status_id = int(request.form['status'])
        
        cursor = conn.execute("select statusText from status where id = ?", (new_status_id,))
        row = cursor.fetchone()
        newStatusText = row['statusText'] if row else None
        
        conn.execute("UPDATE jobs SET statusId = ? WHERE id = ?", (new_status_id, job_id))
        conn.commit()
        
        cursor = conn.execute("SELECT owners.email, owners.name FROM jobs LEFT JOIN owners ON jobs.ownerId = owners.id WHERE jobs.id = ?", (job_id,))
        owner = cursor.fetchone()
        
        if owner and owner['email']:
            try:
                smtp_server = 'sandbox.smtp.mailtrap.io'
                smtp_port = 587
                smtp_user = '50d69c549c5494'
                smtp_password = '4e51486fa046ef'
                
                # E-mail létrehozása
                msg = MIMEMultipart()
                msg['From'] = "service@cardb.hu"
                msg['To'] = owner['email']
                msg['Subject'] = 'Értesítés: Munkalap státuszának frissítése'

                body = f"""Kedves {owner['name']},

Értesítjük, hogy munkalapjának státusza frissítve lett az alábbi új státuszra:
- Státusz: {newStatusText}

Köszönjük, hogy minket választott!
                
Üdvözlettel,
CARDB - Szervíz Csapat
"""
                msg.attach(MIMEText(body, 'plain'))

                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
                server.quit()

                flash("A státusz sikeresen frissítve lett, és az ügyfelet értesítettük.", "success")
            except Exception as e:
                flash("A státusz frissítése sikeres volt, de az e-mail küldése sikertelen.", "danger")
        else:
            flash("A státusz sikeresen frissítve lett, de az ügyfél e-mail címe hiányzik.", "warning")

    cursor = conn.execute(selectStatuses)
    statuses = cursor.fetchall()

    sqlSelect = """
    SELECT 
        jobs.id, 
        vehicles.rsz AS rendszam,
        jobs.comment AS comment,
        DATETIME(jobs.created, 'unixepoch') AS created,
        owners.name AS name,
        owners.phone AS phone,
        owners.email AS email,
        employees.name AS employeename,
        status.statusText AS status,
        status.id AS statusId
    FROM jobs
    LEFT JOIN owners ON jobs.ownerId = owners.id AND owners.deleted = 0
    LEFT JOIN vehicles ON jobs.vehicleId = vehicles.id AND vehicles.deleted = 0
    LEFT JOIN status ON jobs.statusId = status.id AND status.deleted = 0
    LEFT JOIN employees ON jobs.employeeId = employees.id AND employees.deleted = 0
    WHERE jobs.deleted = 0 AND jobs.id = ?"""

    cursor = conn.execute(sqlSelect, (job_id,))
    job = cursor.fetchone()
    conn.close()

    return render_template('view_job.html', job=job, statuses=statuses)


if __name__ == '__main__':
    app.run(debug=True)
