import streamlit as st
import mysql.connector
import bcrypt
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
import matplotlib.pyplot as plt

#database connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="MyNewSecurePassword",
        database="student_dashboard"
    )

#managing passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

#sign up function
def create_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()

    hashed_pw = hash_password(password).decode('utf-8')
    try:
        cursor.execute("INSERT INTO user_data (name, password) VALUES (%s, %s)", (username, hashed_pw))
        conn.commit()
        return True
    except mysql.connector.errors.IntegrityError:
        return False
    finally:
        conn.close()

# Function to login user
def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM user_data WHERE name = %s", (username,))
    result = cursor.fetchone()
    conn.close()
    if result and check_password(password, result[0]):
        st.session_state.username = username  # Store username
        return True
    return False



#streamlit app
#student dashboard login
st.title("Student Dashboard Login")
menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if choice == "Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(username, password):
            st.session_state.logged_in = True
            st.success("welcome back, {}".format(username))
        else:
            st.error("Invalid username or password.")
elif choice == "Sign Up":
    st.subheader("Create a new account")
    new_username=st.text_input('Username')
    new_password=st.text_input('Password', type='password')
    confirm_password=st.text_input('Confirm Password', type='password')
    if new_password == confirm_password:
        if st.button("Sign Up"):
            if create_user(new_username, new_password):
                st.success("Account created successfully!")
            else:
                st.error("Username already exists.")
    else:
        st.error("Passwords do not match.")
if st.session_state.logged_in:
    st.sidebar.success("You are logged in as {}".format(st.session_state.username))

#marks addition by students
# Get student ID by username
def get_user_id(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM user_data WHERE name = %s", (username,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None
# Display dashboard based on user type
if st.session_state.logged_in:
    st.sidebar.title("Dashboard")   


    if st.session_state.username == "admin":
        if st.button("📋 Show Total Students"):
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_data")
            total_students = cursor.fetchone()[0]
            st.success(f"Total Students: {total_students}")
            cursor.close()
            conn.close()

        if st.button("📊 View Marks Table"):
            conn = connect_db()
            query = """
            SELECT u.name AS student_name, s.sub_name, s.max_marks, r.res_id
            FROM results r
            JOIN user_data u ON r.st_id = u.id
            JOIN subjects s ON r.sb_id = s.sub_id
            """
            df = pd.read_sql(query, conn)
            st.dataframe(df)
            conn.close()
       
        if st.button("📊 Calculate Average & Percentage"):
                conn = connect_db()
                query = """
                SELECT 
                    u.name AS student,
                    COUNT(DISTINCT s.sub_id) AS total_subjects,
                    SUM(s.max_marks) AS total_max_marks,
                    SUM(r.marks) AS obtained_marks,
                    ROUND(AVG(r.marks), 2) AS avg_marks,
                    ROUND((SUM(r.marks) / SUM(s.max_marks)) * 100, 2) AS percentage
                FROM user_data u
                LEFT JOIN results r ON u.id = r.st_id
                LEFT JOIN subjects s ON r.sb_id = s.sub_id
                GROUP BY u.name
                """
                df_avg = pd.read_sql(query, conn)
                st.dataframe(df_avg)
                conn.close()
        # Create session state variable for chart section
        if "show_chart_section" not in st.session_state:
            st.session_state.show_chart_section = False

        # Button to trigger chart section
        if st.button("📈 Show Charts"):
            st.session_state.show_chart_section = True

        # If button was clicked, show dropdown and chart
        if st.session_state.show_chart_section:
            conn = connect_db()
            query = """
            SELECT 
                u.name AS student,
                ROUND((SUM(r.marks) / SUM(s.max_marks)) * 100, 2) AS percentage
            FROM user_data u
            JOIN results r ON u.id = r.st_id
            JOIN subjects s ON r.sb_id = s.sub_id
            GROUP BY u.name
            """
            df_chart = pd.read_sql(query, conn)
            conn.close()

            chart_type = st.selectbox("Choose chart type", ["Line Chart", "Bar Chart", "Pie Chart"])

            st.markdown("### 📊 Chart of Student Percentages")

            if chart_type == "Line Chart":
                line_data = df_chart.set_index("student")
                st.line_chart(line_data)

            elif chart_type == "Bar Chart":
                bar_data = df_chart.set_index("student")
                st.bar_chart(bar_data)

            elif chart_type == "Pie Chart":
                try:
                    fig, ax = plt.subplots()
                    ax.pie(df_chart["percentage"], labels=df_chart["student"], autopct='%1.1f%%', startangle=140)
                    ax.axis("equal")
                    st.pyplot(fig)
                except:
                    st.write("Error generating pie chart. Ensure there are enough data points.")

    else:
        if st.session_state.username != "admin": 
            st.header("Student Dashboard ")
            st.info("You are logged in as a student. Displaying student-specific content...")
            st.subheader("📥 Enter Your Marks")

        user_id = get_user_id(st.session_state.username)

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT sub_id, sub_name, max_marks FROM subjects")
        subjects = cursor.fetchall()
        conn.close()

        subject_options = {f"{name} (Max: {max_marks})": (sub_id, max_marks) for sub_id, name, max_marks in subjects}
        
        selected_subject = st.selectbox("Select Subject", list(subject_options.keys()))
        sub_id, max_marks = subject_options[selected_subject]

        marks = st.number_input(f"Enter your marks out of {max_marks}:", min_value=0, max_value=max_marks)

        if st.button("Submit Marks"):
            # Check if marks already submitted
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM results WHERE st_id = %s AND sb_id = %s", (user_id, sub_id))
            already_exists = cursor.fetchone()

            if already_exists:
                st.warning("You already submitted marks for this subject.")
            else:
                cursor.execute("INSERT INTO results (st_id, sb_id, marks) VALUES (%s, %s, %s)",
                            (user_id, sub_id, marks))
                conn.commit()
                st.success("Marks submitted successfully!")
            conn.close()


        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.success("You have been logged out.")
            st.stop()

else:
    st.sidebar.info("Please log in to access the dashboard.")
    st.stop()

# This code is a simple Streamlit application for a student dashboard that allows users to log in or sign up.
# It uses MySQL for user data storage and bcrypt for password hashing.
# Get user ID after login
# password of the admin is ...Admin@123
