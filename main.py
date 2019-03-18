#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
import hashlib
import pymysql
import datetime
import pymysql.cursors


app = Flask(__name__, static_url_path="")
# Connect to the database
connection = pymysql.connect(host='academic-mysql.cc.gatech.edu',
                             user='cs4400_group26',
                             password='YufqGmbw',
                             db='cs4400_group26',
                             cursorclass=pymysql.cursors.DictCursor)

cursor = connection.cursor()
user_logged_in = []


def load_user(username):
    user_logged_in.append(username)


def get_logged_user():
    return user_logged_in[0]


# Vishnu's part Login, Registration, Staff Functionality
@app.route('/', methods=['GET'])
def home_page():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        query = "SELECT Password, UserType, Username FROM User WHERE Email = '" + str(request.form['email']) + "';"
        cursor.execute(query)
        connection.commit()
        data = cursor.fetchone()
        # Might need to run the hashing function here
        input_password = request.form['password']
        hash = hashlib.md5(input_password.encode())
        hashed_input_password = hash.hexdigest()
        if hashed_input_password == data['Password']:
            load_user(data['Username'])
            if data['UserType'] == 'admin':
                return render_template('admin_home.html')
            elif data['UserType'] == 'staff':
                return render_template('staff_home.html')
            elif data['UserType'] == 'visitor':
                return render_template('visitor_home.html')
        else:
            return render_template('login.html', loginerror=True, registrationcomplete=False)
    else:
        return render_template('login.html', loginerror=False, registrationcomplete=False)


@app.route('/user_home/<usertype>', methods=['GET'])
def user_home(usertype):
    if usertype == 'admin':
        return render_template('admin_home.html')
    elif usertype == 'staff':
        return render_template('staff_home.html')
    elif usertype == 'visitor':
        return render_template('visitor_home.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        user_type = str(request.form['register'])
        username = str(request.form['username'])
        email = str(request.form['email'])
        password = str(request.form['password'])
        confirm_password = str(request.form['confirm_password'])

        username_query = "SELECT Username FROM User;"
        cursor.execute(username_query)
        connection.commit()
        usernames = cursor.fetchall()
        list_usernames = []
        for u in usernames:
            list_usernames.append(u['Username'])

        if password == confirm_password and password is not '' and len(password) >= 8 and username not in list_usernames:
            if user_type == 'staff':
                user_query = "INSERT INTO Staff Values('" + username + "');"
            else:
                user_query = "INSERT INTO Visitor Values('" + username + "');"
            hash = hashlib.md5(password.encode())
            hashed_password = hash.hexdigest()
            general_query = "INSERT INTO User Values('" + username + "', '" + hashed_password + "', '" + email + "', '" + user_type + "');"
            cursor.execute(general_query)
            connection.commit()
            cursor.execute(user_query)
            connection.commit()
            return render_template('login.html', loginerror=False, registrationcomplete=True)
        elif len(password) < 8:
            return render_template('registration.html', passwordnotlength=True)
        elif username in list_usernames:
            return render_template('registration.html', usernamenotunique=True)
        else:
            return render_template('registration.html', passwordnotmatch=True)
    else:
        return render_template('registration.html', passwordnotmatch=False)


# Staff Functionality
@app.route('/staff_search_animals', methods=['GET', 'POST'])
def staff_search_animals():
    if request.method == 'POST':
        Name = request.form["Name"]
        Species = request.form["Species"]
        Exhibit = request.form["Exhibit"]
        Type = request.form["Type"]
        AgeMin = request.form["AgeMin"]
        AgeMax = request.form["AgeMax"]
        dict = {"AgeMin": AgeMin, "AgeMax": AgeMax, "Type": Type, "Name": Name, "Species": Species, "Location": Exhibit}

        cond = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "AgeMin":
                    cond = cond + "Age >= " + str(dict[key]) + " AND "
                elif key is "AgeMax":
                    cond = cond + "Age <= " + str(dict[key]) + " AND "
                elif key is "Type":
                    cond = cond + "Type = '" + dict[key] + "' AND "
                elif key is "Name":
                    cond = cond + "Name = '" + dict[key] + "' AND "
                elif key is "Species":
                    cond = cond + "Species = '" + dict[key] + "' AND "
                elif key is "Location":
                    cond = cond + "Location = '" + dict[key] + "' AND "
        if len(cond) > 0:
            cond = "WHERE " + cond[:-5]
        query = "SELECT * FROM Animal " + cond
        cursor.execute(query)
        connection.commit()
        animals = cursor.fetchall()
        print query
    else:
        query = "SELECT * FROM Animal"
        cursor.execute(query)
        connection.commit()
        animals = cursor.fetchall()
        print query
    return render_template('staff_search_animals.html', animals=animals, sqlQ=query)


@app.route('/staff_animal_care/<name>/<species>/<location>/<type>/<age>', methods=['GET', 'POST'])
def staff_animal_care(name,species,location,type,age):
    animal = {}
    animal['Name'] = name
    animal['Species'] = species
    animal['Location'] = location
    animal['Type'] = type
    animal['Age'] = age
    username = get_logged_user()
    if request.method == 'GET':
        query = "SELECT StaffName, Content, DateAndTime FROM Note WHERE AnimalName = '" + animal['Name'] + "'"
        cursor.execute(query)
        connection.commit()
        note = cursor.fetchall()
        return render_template('staff_animal_care.html', animal=animal, notes=note, sqlQ=query)
    else:
        note_data = request.form['note']
        insertSQL = "INSERT INTO Note(DateAndTime, Content, AnimalName, Species, StaffName) VALUES (%s, %s, %s, %s, %s) "
        dt = datetime.datetime.now().strftime(
            "%Y-%m-%d-%H-%M-%S")
        Date = dt.split("-")
        year = Date[0]
        month = Date[1]
        day = Date[2]
        hour = Date[3]
        minute = Date[4]
        second = Date[5]
        date = datetime.datetime(int(
            year), int(month), int(day), int(hour), int(minute),
            int(second))
        cursor.execute(insertSQL, (date, note_data, animal['Name'], animal['Species'], username))
        connection.commit()
        return redirect('/staff_search_animals')


@app.route('/staff_view_shows', methods=['GET'])
def staff_view_shows():
    if request.method == 'GET':
        user = get_logged_user()
        query = "SELECT Name, DateAndTime, Location FROM Shows WHERE Host = '" + user + "'"
        cursor.execute(query)
        connection.commit()
        data = cursor.fetchall()
        print query
        return render_template('staff_view_shows.html', shows=data, sqlQ=query)
    else:
        user = get_logged_user()
        query = "SELECT Name, DateAndTime, Location FROM Shows WHERE Host = '" + user + "'"
        cursor.execute(query)
        connection.commit()
        data = cursor.fetchall()
        print query
        return render_template('staff_view_shows.html', shows=data, sqlQ=query)


@app.route('/staff_log_out', methods=['GET', 'POST'])
def staff_log_out():
    user_logged_in.pop(0)
    return render_template('index.html')


@app.route('/visitor_log_out', methods=['GET', 'POST'])
def visitor_log_out():
    user_logged_in.pop(0)
    return render_template('index.html')


@app.route('/admin_log_out', methods=['GET', 'POST'])
def admin_log_out():
    user_logged_in.pop(0)
    return render_template('index.html')
# End of Vishnu's part


# Safwan's parts
########Visitor
@app.route('/admin_view_visitor', methods=['GET','POST'])
def AdminViewVisitor_page():
    query = []
    if request.method == 'POST':
        print("home")
        Username = request.form["Username"]
        Email = request.form["Email"]

        dict = {"Username":Username,"Email":Email}
        cond = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "Username":
                    cond = cond + "Username = '" + dict[key] + "' AND "
                elif key is "Email":
                    cond = cond + "Email = '" + dict[key] + "' AND "
        if (len(cond) > 0):
            cond = "WHERE " + cond[:-5]
            cond = "SELECT * FROM User " + cond
            sql = cond
            queryStatement = cond
            cursor.execute(sql)
            connection.commit()
            query = cursor.fetchall()
            for row in query:
                row["Deletion"] = "Delete"
            ##connection.close()
        else:
            sql = "SELECT *  FROM User Where UserType = 'visitor'"
            queryStatement = sql
            cond = sql
            cursor.execute(sql)
            connection.commit()
            query = cursor.fetchall()
            for row in query:
                row["Deletion"] = "Delete"
            ##connection.close()
    else:
        sql = "SELECT *  FROM User Where UserType = 'visitor'"
        queryStatement = sql
        cond = sql
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
    return render_template('viewVisitor.html', visitors = query, sqlQ = cond)


@app.route('/AdminVisitorDelete/<sqlQ>', methods=['GET','POST'])
def AdminDeletevisitor(sqlQ):
    words = sqlQ.split("Delete")
    sqlQ = words[0]
    username = words[1]
    #email = words[2]
    sql = "DELETE FROM User WHERE Username = %s"
    cursor.execute(sql, (username))
    connection.commit()
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    ##connection.close()
    return render_template('viewVisitor.html', visitors = query, sqlQ = sqlQ)


########Staff
@app.route('/admin_view_staff', methods=['GET','POST'])
def AdminViewStaff():
    query = []
    if request.method == 'POST':
        print("home")
        Username = request.form["Username"]
        Email = request.form["Email"]

        dict = {"Username":Username,"Email":Email}
        cond = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "Username":
                    cond = cond + "Username = '" + dict[key] + "' AND "
                elif key is "Email":
                    cond = cond + "Email = '" + dict[key] + "' AND "
        if (len(cond) > 0):
            cond = "WHERE " + cond[:-5]
            cond = "SELECT * FROM User " + cond
            sql = cond
            queryStatement = cond
            cursor.execute(sql)
            connection.commit()
            query = cursor.fetchall()
            for row in query:
                row["Deletion"] = "Delete"
            #connection.close()
        else:
            sql = "SELECT *  FROM User Where UserType = 'staff'"
            queryStatement = sql
            cond = sql
            cursor.execute(sql)
            connection.commit()
            query = cursor.fetchall()
            for row in query:
                row["Deletion"] = "Delete"
            #connection.close()
    else:
        sql = "SELECT *  FROM User Where UserType = 'staff'"
        queryStatement = sql
        cond = sql
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
        #connection.close()
    return render_template('viewStaff.html', staffs = query, sqlQ = cond)


@app.route('/DeleteAdminStaff/<sqlQ>', methods=['GET','POST'])
def AdminDeletestaff(sqlQ):
    words = sqlQ.split("Delete")
    sqlQ = words[0]
    username = words[1]
    #email = words[2]
    sql = "DELETE FROM User WHERE Username = %s"
    cursor.execute(sql, (username))
    connection.commit()
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    return render_template('viewStaff.html', staffs = query, sqlQ = sqlQ)


########shows
@app.route('/admin_view_shows', methods=['GET','POST'])
def admin_show_page():
    query = []
    if request.method == 'POST':
        print("home")
        Name = request.form["Name"]
        Exhibit = request.form["Exhibit"]
        DateAndTime = request.form["DateAndTime"]

        dict = {"Name":Name,"Location":Exhibit,"DateAndTime":DateAndTime}

        cond = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "Name":
                    cond = cond + "Name = '" + dict[key] + "' AND "
                elif key is "Location":
                    cond = cond + "Location = '" + dict[key] + "' AND "
                elif key is "DateAndTime":
                    cond = cond + "DateAndTime LIKE '%" + dict[key] + "%' AND "
        if (len(cond) > 0):
            cond = "WHERE " + cond[:-5]
        cond = "SELECT * FROM Shows " + cond
        print(cond)
        sql = cond
        queryStatement = cond
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
    else:
        sql = "SELECT * FROM Shows"
        queryStatement = sql
        cond = sql
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
    return render_template('viewShow.html', shows = query, sqlQ = cond)


@app.route('/AdminDeleteShow/<sqlQ>', methods=['GET','POST'])
def DeleteShow(sqlQ):
    words = sqlQ.split("Delete")
    sqlQ = words[0]
    name = words[1]
    sql = "DELETE FROM Shows WHERE Name = %s"
    cursor.execute(sql, (name))
    connection.commit()
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    return render_template('viewShow.html', shows = query, sqlQ = sqlQ)


# Sheng's part
@app.route('/admin_view_animals', methods=['GET','POST'])
def admin_view_animals():
    query = []
    if request.method == 'POST':
        print("home")
        Name = request.form["Name"]
        Species = request.form["Species"]
        Exhibit = request.form["Exhibit"]
        Type = request.form["Type"]
        AgeMin = request.form["AgeMin"]
        AgeMax = request.form["AgeMax"]

        dict = {"AgeMin":AgeMin,"AgeMax":AgeMax,"Type":Type,"Name":Name,"Species":Species,"Location":Exhibit}
        cond = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "AgeMin":
                    cond = cond + "Age >= " + str(dict[key]) + " AND "
                elif key is "AgeMax":
                    cond = cond + "Age <= " + str(dict[key]) + " AND "
                elif key is "Type":
                    cond = cond + "Type = '" + dict[key] + "' AND "
                elif key is "Name":
                    cond = cond + "Name = '" + dict[key] + "' AND "
                elif key is "Species":
                    cond = cond + "Species = '" + dict[key] + "' AND "
                elif key is "Location":
                    cond = cond + "Location = '" + dict[key] + "' AND "
        if (len(cond) > 0):
            cond = "WHERE " + cond[:-5]
        cond = "SELECT * FROM Animal " + cond
        #print(cond)

        sql = cond
        queryStatement = cond
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
    else:
        sql = "SELECT * FROM Animal"
        queryStatement = sql
        cond = sql
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
        # for row in query:
        #     print(row)
    return render_template('viewAnimals.html', animals = query, sqlQ = cond)


#"/Delete/{{animal.Name+animal.Deletion+animal.Species}}
@app.route('/Delete/<sqlQ>', methods=['GET','POST'])
def DeleteAnimal(sqlQ):
    words = sqlQ.split("Delete")
    sqlQ = words[0]
    name = words[1]
    species = words[2]
    sql = "DELETE FROM Animal WHERE Name = %s AND Species = %s"
    cursor.execute(sql, (name, species))
    connection.commit()
    #after deletion, requery
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    #print("In DELETION")
    # for row in query:
    #     print(row)
    for row in query:
        row["Deletion"] = "Delete"
    return render_template('viewAnimals.html', animals = query, sqlQ = sqlQ)


@app.route('/admin_add_animal', methods=['GET','POST'])
def addAnimal():
    query = []
    if request.method == 'POST':
        Name = request.form["Name"]
        Species = request.form["Species"]
        Exhibit = request.form["Exhibit"]
        Type = request.form["Type"]
        Age = request.form["Age"]

        name_species_query = "SELECT Name, Species FROM Animal;"
        cursor.execute(name_species_query)
        connection.commit()
        name_species = cursor.fetchall()
        list_name_species = []
        for ns in name_species:
            curr = (ns['Name'], ns['Species'])
            list_name_species.append(curr)

        input_tuple = (Name, Species)

        if input_tuple in list_name_species:
            return render_template('addAnimal.html', animalnotunique=True)
        else:
            cond = "INSERT INTO Animal(Age,Type,Name,Species,Location) Values (%s, %s, %s, %s, %s)"
            sql = cond
            cursor.execute(sql, (Age, Type, Name, Species, Exhibit))
            connection.commit()
    return render_template('addAnimal.html')

@app.route('/admin_add_show', methods=['GET','POST'])
def addShow():
    query = []
    if request.method == 'POST':
        Name = request.form["Name"]
        Exhibit = request.form["Exhibit"]
        Staff = request.form["Staff"]
        Date = request.form["Date"]
        Time = request.form["Time"]

        # find month,day,year
        Date = Date.split("/")
        month = Date[0]
        day = Date[1]
        year = Date[2]
        #find hr,min,sec
        Time = Time.split(":")
        hour = Time[0]
        minute = Time[1]
        second = Time[2]

        key = {"Name": Name, "DateAndTime": datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second)), "Location": Exhibit,
               "Host": Staff}

        name_datetime_query = "SELECT Name, DateAndTime FROM Shows;"
        cursor.execute(name_datetime_query)
        connection.commit()
        name_datetime = cursor.fetchall()
        list_name_datetime = []
        for nd in name_datetime:
            curr = (nd['Name'], nd['DateAndTime'])
            list_name_datetime.append(curr)

        input_tuple = (Name, key["DateAndTime"])

        if input_tuple in list_name_datetime:
            sql = "SELECT Username FROM User WHERE UserType = 'staff'"
            cursor.execute(sql)
            connection.commit()
            query = cursor.fetchall()
            return render_template('addShow.html', shownotunique=True, staffs=query)
        else:
            sql = "INSERT INTO Shows(Name, DateAndTime, Location, Host) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (key["Name"], key["DateAndTime"], key["Location"], key["Host"]))
            connection.commit()
            return redirect("/admin_add_show")
    else:
        #get all the staff members' names
        sql = "SELECT Username FROM User WHERE UserType = 'staff'"
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        return render_template('addShow.html', staffs=query)


# Balkrishna's post
@app.route('/visitor_search_animal', methods=['GET','POST'])
def animal_search():
    result = []
    where = ''
    if request.method == "POST":
        Name = request.form["Name"]
        Species = request.form["Species"]
        Exhibit = request.form["Exhibit"]
        Type = request.form["Type"]
        AgeMin = request.form["AgeMin"]
        AgeMax = request.form["AgeMax"]

        dict = {"AgeMin": AgeMin, "AgeMax": AgeMax, "Type": Type,
                "Name": Name, "Species": Species, "Location": Exhibit}
        # dict = request.form()
        for key in dict:
            if len(dict[key]) is not 0:
                if key is 'AgeMin':
                    where += "Age >= " + str(dict[key]) + " AND "
                elif key is 'AgeMax':
                    where += "Age <= " + str(dict[key]) + " AND "
                elif key is 'Type':
                    where += "Type = '" + dict[key] + "' AND "
                elif key is 'Name':
                    where += "Name = '" + dict[key] + "' AND "
                elif key is 'Species':
                    where += "Species = '" + dict[key] + "' AND "
                elif key is 'Location':
                    where += "Location = '" + dict[key] + "' AND "
        if len(where) > 0:
            where = "WHERE " + where[:-5]

        query = "SELECT * FROM Animal " + where
        cursor.execute(query)
        connection.commit()
        result = cursor.fetchall()
    else:
        query = "SELECT * FROM Animal"
        cursor.execute(query)
        connection.commit()
        result = cursor.fetchall()
    return render_template('animalsearch.html', animals=result,
                           sqlQ = query)


@app.route('/Location/<exhibitName>', methods=['GET', 'POST'])
def exhibit_details(exhibitName):
    username = get_logged_user()
    name = exhibitName
    if request.method =='POST':
        insertSQL = "INSERT INTO Exhibit_Visit(Name, DateAndTime, " \
                    "Username) VALUES (%s, %s, %s) "
        dt = datetime.datetime.now().strftime(
            "%Y-%m-%d-%H-%M-%S")
        Date = dt.split("-")
        year = Date[0]
        month = Date[1]
        day = Date[2]
        hour = Date[3]
        minute = Date[4]
        second = Date[5]
        date = datetime.datetime(int(
            year), int(month), int(day), int(hour), int(minute),
            int(second))
        cursor.execute(insertSQL, (name, date, username))
        connection.commit()
        return redirect('/Location/'+exhibitName)
    query = "SELECT Exhibit.Name, WaterFeature, Size, count(*) as " \
            "Animal_Count FROM Exhibit INNER JOIN Animal ON " \
            "Exhibit.Name = Animal.Location AND Exhibit.Name = %s " \
            "GROUP BY Animal.Location"
    cursor.execute(query, exhibitName)
    connection.commit()
    exhibitDetails = cursor.fetchall()
    getAnimals = "Select Name, Species From Animal Where Location " \
                 "= '" + exhibitName + "'"
    cursor.execute(getAnimals)
    connection.commit()
    animalsList = cursor.fetchall()
    exhibitDetails = exhibitDetails[0]
    if (exhibitDetails['WaterFeature'] == 1):
        exhibitDetails['WaterFeature'] = 'Yes'
    else:
        exhibitDetails['WaterFeature'] = 'No'
    return render_template('exhibitdetails.html', exhibitDetails=
    exhibitDetails, exhibitAnimals=animalsList, sqlQ = getAnimals)


@app.route('/AnimalDetails/<animalName>', methods=['GET'])
def animal_details(animalName):
    query = "SELECT * FROM Animal Where Name = '" + animalName + "'"
    cursor.execute(query)
    connection.commit()
    aDetails = cursor.fetchall()
    aDetails = aDetails[0]
    print aDetails

    return render_template('animaldetails.html', animals=
    aDetails, sqlQ=query)


# Josh's code!!
@app.route('/visitor_search_exhibit', methods=['GET','POST'])
def visitor_search_exhibit():
    query = []
    if request.method == 'POST':
        print("Exhibit Search")
        Name = request.form["Exhibit"]
        WaterFeature = request.form["WaterFeature"]
        Size = request.form["Size"]
        Min = request.form["Minimum"]
        Max = request.form["Maximum"]

        dict = {"Name": Name, "WaterFeature": WaterFeature, "Size": Size, "Min": Min, "Max": Max}

        cond = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "Name":
                    cond = cond + "Name = '" + dict[key] + "' AND "
                elif key is "WaterFeature":
                    cond = cond + "WaterFeature = '" + dict[key] + "' AND "
                elif key is "Size":
                    cond = cond + "Size = '" + dict[key] + "' AND "
                elif key is "Min":
                    cond = cond + "AnimalCount >= " + str(dict[key]) + " AND "
                elif key is "Max":
                    cond = cond + "AnimalCount <= " + str(dict[key]) + " AND "
        if (len(cond) > 0):
            cond = "WHERE " + cond[:-5]
        sql = "SELECT * FROM (SELECT Exhibit.Name, WaterFeature, Size, count(*) as AnimalCount FROM Exhibit INNER JOIN Animal ON Exhibit.Name = Animal.Location GROUP BY Animal.Location) AS t " + cond

        #sql = cond
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
        for data in query:
            if (data['WaterFeature'] == 1):
                data['WaterFeature'] = 'Yes'
            else:
                data['WaterFeature'] = 'No'
    else:
        sql = "SELECT Exhibit.Name, WaterFeature, Size, count(*) AS " \
              "AnimalCount FROM Exhibit INNER JOIN Animal ON " \
              "Exhibit.Name = Animal.Location " \
              "GROUP BY Animal.Location"
        querystatement = sql
        cond = sql
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
        for data in query:
            if (data['WaterFeature'] == 1):
                data['WaterFeature'] = 'Yes'
            else:
                data['WaterFeature'] = 'No'
    return render_template('exhibitsearch.html', exhibits = query, sqlQ = cond)


@app.route('/visitor_search_show', methods=['GET','POST'])
def visitor_search_show():
    query = []
    if request.method == 'POST':
        print("Show Search")
        Name = request.form["Name"]
        DateAndTime = request.form["DateAndTime"]
        Location = request.form["Location"]
        dt = datetime.datetime.now().strftime(
            "%Y-%m-%d-%H-%M-%S")
        Date = dt.split("-")
        year = Date[0]
        month = Date[1]
        day = Date[2]
        hour = Date[3]
        minute = Date[4]
        second = Date[5]
        curr_date = datetime.datetime(int(
            year), int(month), int(day), int(hour), int(minute),
            int(second))
        dict = {"Name": Name, "Location": Location, "DateAndTime": DateAndTime}

        cond = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "Name":
                    cond = cond + "Name = '" + dict[key] + "' AND "
                elif key is "DateAndTime":
                    cond = cond + "DateAndTime LIKE '" + dict[key] + "%' AND "
                elif key is "Location":
                    cond = cond + "Location = '" + dict[key] + "' AND "
        if (len(cond) > 0):
            cond = "WHERE " + cond[:-5]
        cond = "SELECT * FROM Shows " + cond
        print(cond)

        print(query)
        sql = cond
        queryStatement = cond
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
    else:
        sql = "SELECT * FROM Shows"
        querystatement = sql
        cond = sql
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
    return render_template('showsearch.html', shows = query, sqlQ = cond)


@app.route('/visitor_view_exhibit_history', methods=['GET','POST'])
def visitor_view_exhibit_history():
    query = []
    Username = get_logged_user()
    if request.method == 'POST':
        print("Exhibit History")
        Name = request.form["Location"]
        DateAndTime = request.form["DateAndTime"]

        dict = {"Name": Name, "DateAndTime": DateAndTime, "Username": Username}

        cond = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "Name":
                    cond = cond + "Name = '" + dict[key] + "' AND "
                elif key is "DateAndTime":
                    cond = cond + "DateAndTime LIKE '%" + dict[key] + "%' AND "
        if (len(cond) > 0):
            cond = "WHERE Username = '" + Username + "' AND " + cond[:-5]
        cond = "SELECT *, COUNT(Name) AS Occurences FROM Exhibit_Visit " + cond
        print(cond)

        sql = cond
        queryStatement = cond
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
    else:
        sql = "SELECT * FROM Exhibit_Visit WHERE Username = '" + Username + "'"
        print(sql)
        cond = sql
        cursor.execute(sql)
        connection.commit()
        query = cursor.fetchall()
        for row in query:
            row["Deletion"] = "Delete"
        print query
    return render_template('exhibithistory.html', exhibits = query, sqlQ = cond, jank=True)


@app.route('/visitor_view_show_history', methods=['GET', 'POST'])
def visitor_view_show_history():
    username = get_logged_user()
    query = "SELECT * FROM(SELECT Shows.Location as Exhibit, " \
            "Show_Visit.Name as Name, " \
            "Show_Visit.ShowDateAndTime as Date FROM Shows INNER " \
            "JOIN Show_Visit ON Shows.Name = Show_Visit.Name AND " \
            "Show_Visit.Username  = %s) as t "
    if request.method == 'POST':
        show_name = request.form["Name"]
        exhibit_name = request.form["Location"]
        date = request.form["DateAndTime"]
        dict = {"Show": show_name, "Exhibit": exhibit_name, "Date": date}
        condition = ''
        for key in dict:
            if len(dict[key]) is not 0:
                if key is "Show":
                    condition += "Name = '" + dict[key] + "' AND "
                elif key is "Exhibit":
                    condition += "Exhibit = '" + dict[key] + "' AND "
                elif key is "Date":
                    condition += "Date = '" + dict[key] + "' AND "
        if len(condition) > 0:
            condition = 'WHERE ' + condition[:-5]
        query += condition
        cursor.execute(query, username)
        connection.commit()
        result = cursor.fetchall()
    else:
        cursor.execute(query, username)
        connection.commit()
        result = cursor.fetchall()
    return render_template('showhistory.html', shows=result, sqlQ=query)


@app.route('/visitor_search_show/LogVisit/<sqlQ>', methods=['GET', 'POST'])
def log_show_visit(sqlQ):
    print("heres sqlq the first time")
    print(sqlQ)
    info = sqlQ.split("+")
    # print(info)
    query = info[0]
    # print(query)
    showName = info[1]
    # print(showName)
    showTime = info[2]
    # print(showTime)

    info2 = showTime.split(" ")
    date = info2[0]
    date = date.split("-")
    year = date[0]
    month = date[1]
    day = date[2]

    time = info2[1]
    time = time.split(":")
    hour = time[0]
    minute = time[1]
    sec = time[2]

    time = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(sec))
    dt = datetime.datetime.now().strftime(
        "%Y-%m-%d-%H-%M-%S")
    Date = dt.split("-")
    year = Date[0]
    month = Date[1]
    day = Date[2]
    hour = Date[3]
    minute = Date[4]
    second = Date[5]
    curr_date = datetime.datetime(int(
        year), int(month), int(day), int(hour), int(minute),
        int(second))

    print curr_date
    print time
    if curr_date < time:
        return render_template('visitor_home.html', cannotlog=True)
    else:
        sqlQ = query
        print("here's sqlQ")
        print(sqlQ)

        # print(showName)
        # print(showTime)

        # sqlQu = sqlQ + " WHERE Name = '" + showName + "' AND DateAndTime = " + showTime
        # sql = sqlQu
        # cursor.execute(sql)
        # connection.commit()
        # insertionQuery = cursor.fetchall()
        cond = "INSERT INTO Show_Visit(Name,ShowDateAndTime,Username) Values (%s,%s,%s)"
        print(cond)
        # Name = insertionQuery[0]
        # DateAndTime = insertionQuery[1]
        Username = get_logged_user()
        cursor.execute(cond, (showName, time, Username))
        connection.commit()

        cursor.execute(sqlQ)
        connection.commit()
        query = cursor.fetchall()

        query1 = "SELECT Location FROM Shows WHERE Name = %s AND " \
                "DateAndTime = %s"
        cursor.execute(query1, (showName, time))
        connection.commit()
        loc = cursor.fetchone()
        print loc

        query2 = "INSERT INTO Exhibit_Visit (Name, DateAndTime, " \
                 "Username) Values (%s, %s, %s)"
        cursor.execute(query2, (loc["Location"], time, Username))
        connection.commit()

        return render_template("showsearch.html", shows=query, sqlQ=sqlQ)

@app.route('/Age/<sqlQ>', methods=['GET','POST'])
def sortByAge(sqlQ):
    print(sqlQ)
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Age"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    # for row in query:
    #     print(row)
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-13])


@app.route('/Type/<sqlQ>', methods=['GET','POST'])
def sortByType(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Type"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    # for row in query:
    #     print(row)
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-14])

@app.route('/Name/<sqlQ>', methods=['GET','POST'])
def sortByName(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Name"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    # for row in query:
    #     print(row)
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-14])

@app.route('/Species/<sqlQ>', methods=['GET','POST'])
def sortBySpecies(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Species"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    # for row in query:
    #     print(row)
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-17])


@app.route('/Locations/<sqlQ>', methods=['GET','POST'])
def sortByLocation(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Location"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    # for row in query:
    #     print(row)
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-18])


@app.route('/AdminVisitorUsername/<sqlQ>', methods=['GET','POST'])
def AdminVisitorsortByUsername(sqlQ):
    print(sqlQ)
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Username"
    sql = sqlQ
    print(sqlQ)
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, visitors = query, sqlQ = sqlQ[:-18])


@app.route('/AdminVisitorEmail/<sqlQ>', methods=['GET','POST'])
def AdminVisitorsortByEmail(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Email"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, visitors = query, sqlQ = sqlQ[:-15])


@app.route('/AdminStaffUsername/<sqlQ>', methods=['GET','POST'])
def AdminsortByUsername(sqlQ):
    print(sqlQ)
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Username"
    sql = sqlQ
    print(sqlQ)
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, staffs = query, sqlQ = sqlQ[:-18])


@app.route('/AdminStaffEmail/<sqlQ>', methods=['GET','POST'])
def AdminsortByEmail(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Email"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, staffs = query, sqlQ = sqlQ[:-15])


@app.route('/AdminShowName/<sqlQ>', methods=['GET','POST'])
def AdminSortShowByName(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Name"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows = query, sqlQ = sqlQ[:-14])

@app.route('/AdminShowLocation/<sqlQ>', methods=['GET','POST'])
def AdminSortShowByLocation(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY Location"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()
    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows = query, sqlQ = sqlQ[:-18])

@app.route('/AdminShowsDatetime/<sqlQ>', methods=['GET','POST'])
def sortShowsByDT(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]

    sqlQ = sqlQ + " ORDER BY DateAndTime"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()

    for row in query:
        row["Deletion"] = "Delete"
    return render_template('viewShow.html', shows = query, sqlQ = sqlQ[:-21])


@app.route('/StaffAnimalAge/<sqlQ>', methods=['GET','POST'])
def sortStaffAnimalByAge(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Age"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()

    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-13])


@app.route('/StaffAnimalType/<sqlQ>', methods=['GET','POST'])
def sortStaffAnimalByType(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Type"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()

    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-14])


@app.route('/StaffAnimalName/<sqlQ>', methods=['GET','POST'])
def sortStaffAnimalByName(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Name"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()

    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-14])


@app.route('/StaffAnimalSpecies/<sqlQ>', methods=['GET','POST'])
def sortStaffAnimalBySpecies(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Species"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()

    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-16])


@app.route('/StaffAnimalLocation/<sqlQ>', methods=['GET','POST'])
def sortStaffAnimalByLocation(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Location"
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    query = cursor.fetchall()

    for row in query:
        row["Deletion"] = "Delete"
    return render_template(renderPage, animals = query, sqlQ = sqlQ[:-18])


@app.route('/StaffShowName/<sqlQ>', methods=['GET','POST'])
def sortStaffShowByName(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Name"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-14])


@app.route('/StaffShowTime/<sqlQ>', methods=['GET','POST'])
def sortStaffShowByTime(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY DateAndTime"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-21])


@app.route('/StaffShowExhibit/<sqlQ>', methods=['GET','POST'])
def sortStaffShowByExhibit(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Location"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-18])


# Visitor Sorting
@app.route('/Exhibits/Name/<sqlQ>', methods=['GET','POST'])
def sortVisitorExhibitByName(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Name"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    for query in data:
        if (query['WaterFeature'] == 1):
            query['WaterFeature'] = 'Yes'
        else:
            query['WaterFeature'] = 'No'
    return render_template(renderPage, exhibits=data, sqlQ = sqlQ[:-14])


@app.route('/Exhibits/Size/<sqlQ>', methods=['GET','POST'])
def sortVisitorExhibitBySize(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Size"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    for query in data:
        if (query['WaterFeature'] == 1):
            query['WaterFeature'] = 'Yes'
        else:
            query['WaterFeature'] = 'No'
    return render_template(renderPage, exhibits=data, sqlQ = sqlQ[:-14])


@app.route('/Exhibits/WaterFeature/<sqlQ>', methods=['GET','POST'])
def sortVisitorExhibitByWater(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY WaterFeature"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    for query in data:
        if (query['WaterFeature'] == 1):
            query['WaterFeature'] = 'Yes'
        else:
            query['WaterFeature'] = 'No'
    return render_template(renderPage, exhibits=data, sqlQ = sqlQ[:-22])


@app.route('/Exhibits/AnimalCount/<sqlQ>', methods=['GET','POST'])
def sortVisitorExhibitByAnimalCount(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY AnimalCount"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    for query in data:
        if (query['WaterFeature'] == 1):
            query['WaterFeature'] = 'Yes'
        else:
            query['WaterFeature'] = 'No'
    return render_template(renderPage, exhibits=data, sqlQ = sqlQ[:-21])


@app.route('/Shows/Name/<sqlQ>', methods=['GET','POST'])
def sortVisitorShowByName(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Name"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-14])


@app.route('/Shows/Datetime/<sqlQ>', methods=['GET','POST'])
def sortVisitorShowByDateandtime(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY DateAndTime"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-21])


@app.route('/Shows/Exhibit/<sqlQ>', methods=['GET','POST'])
def sortVisitorShowByExhibit(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Location"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-18])


@app.route('/ExhibitHistory/Name/<sqlQ>', methods=['GET','POST'])
def sortVisitorExhibitHistoryByName(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Name"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, exhibits=data, sqlQ = sqlQ[:-14])


@app.route('/ExhibitHistory/Datetime/<sqlQ>', methods=['GET','POST'])
def sortVisitorExhibitHistoryByTime(sqlQ):
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY DateAndTime"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, exhibits=data, sqlQ = sqlQ[:-21])


@app.route('/ShowHistory/Name/<sqlQ>', methods=['GET','POST'])
def sortVisitorShowHistoryByName(sqlQ):
    username = get_logged_user()
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Name"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql, username)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-14])


@app.route('/ShowHistory/Datetime/<sqlQ>', methods=['GET','POST'])
def sortVisitorShowHistoryByTime(sqlQ):
    username = get_logged_user()
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Date"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql, username)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-14])


@app.route('/ShowHistory/Exhibit/<sqlQ>', methods=['GET','POST'])
def sortVisitorShowHistoryByExhibit(sqlQ):
    username = get_logged_user()
    keywords = sqlQ.split("+")
    print(keywords)
    sqlQ = keywords[0]
    renderPage = keywords[1]
    print sqlQ
    sqlQ = sqlQ + " ORDER BY Exhibit"
    print sqlQ
    sql = sqlQ
    cursor.execute(sql, username)
    connection.commit()
    data = cursor.fetchall()
    print 'done'
    for row in data:
        row["Deletion"] = "Delete"
    return render_template(renderPage, shows=data, sqlQ = sqlQ[:-17])


if __name__ == '__main__':
    app.run(debug=True, port=5000)