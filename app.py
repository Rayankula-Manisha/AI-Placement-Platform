
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import hashlib
import secrets
import re

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CareerPilot | Placement Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# DATABASE
# =====================================================

DB_NAME = "users.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_data (
            user_id INTEGER PRIMARY KEY,
            target TEXT DEFAULT 'Data Scientist',
            skills TEXT DEFAULT 'Python,SQL,HTML,CSS,Pandas,NumPy,Git',
            solved INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password, salt):

    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        200000
    ).hex()


def register_user(name, email, password):

    salt = secrets.token_hex(16)

    password_hash = hash_password(
        password,
        salt
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (name, email, salt, password_hash)
            VALUES (?, ?, ?, ?)
        """, (name, email, salt, password_hash))

        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO student_data (user_id)
            VALUES (?)
        """, (user_id,))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def login_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, salt, password_hash
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()
    conn.close()

    if user:

        user_id, name, salt, stored_hash = user

        entered_hash = hash_password(
            password,
            salt
        )

        if secrets.compare_digest(
            entered_hash,
            stored_hash
        ):
            return user_id, name

    return None


def load_student_data(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT target, skills, solved
        FROM student_data
        WHERE user_id = ?
    """, (user_id,))

    data = cursor.fetchone()
    conn.close()

    if data:
        return {
            "target": data[0],
            "skills": data[1].split(","),
            "solved": data[2]
        }

    return {
        "target": "Data Scientist",
        "skills": ["Python", "SQL", "HTML", "CSS"],
        "solved": 0
    }


def save_student_data():

    conn = get_connection()
    cursor = conn.cursor()

    skills = ",".join(st.session_state.skills)

    cursor.execute("""
        UPDATE student_data
        SET target = ?, skills = ?, solved = ?
        WHERE user_id = ?
    """, (
        st.session_state.target,
        skills,
        st.session_state.solved,
        st.session_state.user_id
    ))

    conn.commit()
    conn.close()


create_database()


# =====================================================
# SESSION STATE
# =====================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "interview_answers" not in st.session_state:
    st.session_state.interview_answers = {}


# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #f5f7fc;
}

[data-testid="stSidebar"] {
    background: #111827;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.main-title {
    font-size: 32px;
    font-weight: 800;
    color: #111827;
}

.subtitle {
    color: #64748b;
    font-size: 14px;
    margin-bottom: 25px;
}

.metric-card {
    background: white;
    padding: 22px;
    border-radius: 15px;
    border: 1px solid #e5e7eb;
    box-shadow: 0px 3px 12px rgba(0,0,0,0.03);
}

.metric-label {
    color: #64748b;
    font-size: 14px;
}

.metric-value {
    color: #111827;
    font-size: 29px;
    font-weight: 800;
    margin-top: 8px;
}

.metric-note {
    color: #16a34a;
    font-size: 12px;
    margin-top: 5px;
}

.section-title {
    font-size: 21px;
    font-weight: 700;
    color: #111827;
    margin-top: 25px;
    margin-bottom: 15px;
}

.job-card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    margin-bottom: 12px;
}

.job-title {
    font-size: 18px;
    font-weight: 700;
    color: #111827;
}

.job-company {
    color: #64748b;
    font-size: 13px;
}

.tag {
    display: inline-block;
    background: #eef2ff;
    color: #4338ca;
    padding: 6px 10px;
    border-radius: 7px;
    font-size: 12px;
    margin: 4px;
}

div.stButton > button {
    background-color: #4f46e5;
    color: white;
    border-radius: 9px;
    border: none;
    padding: 9px 18px;
    font-weight: 600;
}

div.stButton > button:hover {
    background-color: #3730a3;
    color: white;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# LOGIN AND SIGNUP
# =====================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <br>
        <h1 style='text-align:center;color:#4f46e5;'>
        🚀 CareerPilot
        </h1>
        <p style='text-align:center;color:#64748b;'>
        Your journey towards your dream job starts here.
        </p>
        <br>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        login_tab, signup_tab = st.tabs(
            ["Login", "Create Account"]
        )

        # ---------------- LOGIN ----------------

        with login_tab:

            st.subheader("Welcome Back!")

            email = st.text_input(
                "Email Address",
                key="login_email"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            if st.button(
                "Login",
                use_container_width=True
            ):

                if not email or not password:

                    st.error("Please enter email and password.")

                else:

                    result = login_user(
                        email.strip().lower(),
                        password
                    )

                    if result:

                        user_id, name = result

                        student = load_student_data(user_id)

                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.student_name = name
                        st.session_state.target = student["target"]
                        st.session_state.skills = student["skills"]
                        st.session_state.solved = student["solved"]

                        st.session_state.interview_answers = {}

                        st.rerun()

                    else:

                        st.error("Invalid email or password.")

        # ---------------- SIGNUP ----------------

        with signup_tab:

            st.subheader("Create Your Account")

            new_name = st.text_input(
                "Full Name",
                key="signup_name"
            )

            new_email = st.text_input(
                "Email Address",
                key="signup_email"
            )

            new_password = st.text_input(
                "Create Password",
                type="password",
                key="signup_password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="signup_confirm"
            )

            if st.button(
                "Sign Up",
                use_container_width=True
            ):

                if not new_name.strip() or not new_email.strip() or not new_password:

                    st.error("Please fill in all fields.")

                elif not re.fullmatch(
                    r"[^@\s]+@[^@\s]+\.[^@\s]+",
                    new_email.strip()
                ):

                    st.error("Enter a valid email address.")

                elif len(new_password) < 8:

                    st.error("Password must contain at least 8 characters.")

                elif new_password != confirm_password:

                    st.error("Passwords do not match.")

                else:

                    success = register_user(
                        new_name.strip(),
                        new_email.strip().lower(),
                        new_password
                    )

                    if success:

                        st.success(
                            "Account created successfully! Please login."
                        )

                    else:

                        st.error(
                            "This email is already registered."
                        )

    st.stop()


# =====================================================
# JOB DATA
# =====================================================

job_data = {

    "Data Scientist": {

        "skills": [
            "Python", "SQL", "Statistics",
            "Machine Learning", "Pandas",
            "NumPy", "Data Visualization",
            "Scikit-learn", "Deep Learning"
        ],

        "companies": [
            ("Data Scientist", "Google", "8-12 LPA"),
            ("Junior Data Scientist", "Infosys", "4-7 LPA"),
            ("Data Analyst", "Accenture", "4-6 LPA")
        ]
    },

    "Python Developer": {

        "skills": [
            "Python", "SQL", "Django",
            "Flask", "REST APIs", "Git",
            "OOP", "Docker"
        ],

        "companies": [
            ("Python Developer", "TCS", "4-7 LPA"),
            ("Backend Developer", "Wipro", "4-8 LPA"),
            ("Software Engineer", "Infosys", "4-7 LPA")
        ]
    },

    "AI Engineer": {

        "skills": [
            "Python", "Machine Learning",
            "Deep Learning", "NLP",
            "TensorFlow", "PyTorch",
            "LLMs", "REST APIs"
        ],

        "companies": [
            ("AI Engineer", "IBM", "6-12 LPA"),
            ("Junior ML Engineer", "Accenture", "5-9 LPA"),
            ("AI Developer", "Wipro", "4-8 LPA")
        ]
    },

    "Web Developer": {

        "skills": [
            "HTML", "CSS", "JavaScript",
            "React", "Python", "SQL",
            "REST APIs", "Git"
        ],

        "companies": [
            ("Frontend Developer", "Infosys", "4-7 LPA"),
            ("Web Developer", "TCS", "4-6 LPA"),
            ("Full Stack Developer", "Wipro", "5-9 LPA")
        ]
    }
}


# =====================================================
# REUSABLE FUNCTIONS
# =====================================================

def metric_card(label, value, note):

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-note">{note}</div>
    </div>
    """, unsafe_allow_html=True)


def page_heading(title, subtitle):

    st.markdown(
        f'<div class="main-title">{title}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="subtitle">{subtitle}</div>',
        unsafe_allow_html=True
    )


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown("## 🚀 CareerPilot")

    st.caption("Your Placement Companion")

    st.markdown("---")

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Job Matching",
            "Skill Gap Analysis",
            "Interview Preparation",
            "Coding Tracker",
            "My Profile"
        ]
    )

    st.markdown("---")

    st.markdown("### 👩‍🎓 Student")

    st.write(st.session_state.student_name)

    st.caption("Computer Science Engineering")

    if st.button("Logout", use_container_width=True):

        save_student_data()

        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.rerun()

    st.markdown("---")

    st.caption("Build skills. Get placed.")


# =====================================================
# DASHBOARD
# =====================================================

if page == "Dashboard":

    page_heading(
        f"Welcome back, {st.session_state.student_name}! 👋",
        "Track your placement preparation and achieve your career goals."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            "Jobs Matched",
            "24",
            "Explore opportunities"
        )

    with col2:
        metric_card(
            "Skills Acquired",
            str(len(st.session_state.skills)),
            "Your current skills"
        )

    with col3:
        metric_card(
            "Problems Solved",
            str(st.session_state.solved),
            "Keep practicing"
        )

    with col4:
        metric_card(
            "Preparation",
            "65%",
            "Sample progress"
        )

    st.markdown(
        '<div class="section-title">Your Preparation Overview</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        progress_data = pd.DataFrame({
            "Skill": [
                "Python", "SQL", "HTML/CSS",
                "Machine Learning", "DSA"
            ],
            "Progress": [85, 75, 90, 45, 35]
        })

        fig = px.bar(
            progress_data,
            x="Progress",
            y="Skill",
            orientation="h",
            title="Skill Development Progress",
            text="Progress"
        )

        fig.update_traces(marker_color="#6366f1")

        fig.update_layout(
            height=400,
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#1e293b", size=13),
            margin=dict(l=30, r=30, t=60, b=30),
            xaxis=dict(range=[0, 100]),
            yaxis=dict(title="")
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        activity_data = pd.DataFrame({
            "Category": [
                "Python", "SQL", "DSA",
                "Projects", "Interview"
            ],
            "Hours": [8, 5, 4, 6, 3]
        })

        fig = px.pie(
            activity_data,
            names="Category",
            values="Hours",
            hole=0.55,
            title="Weekly Learning Distribution"
        )

        fig.update_layout(
            height=400,
            paper_bgcolor="white",
            font=dict(color="#1e293b", size=13)
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown(
        '<div class="section-title">Recommended Jobs</div>',
        unsafe_allow_html=True
    )

    for title, company, salary in [
        ("Python Developer", "Infosys", "4-7 LPA"),
        ("Data Analyst", "Accenture", "4-6 LPA"),
        ("Junior AI Engineer", "IBM", "5-9 LPA")
    ]:

        st.markdown(f"""
        <div class="job-card">
            <div class="job-title">{title}</div>
            <div class="job-company">{company}</div>
            <br>
            <span class="tag">Fresher</span>
            <span class="tag">{salary}</span>
        </div>
        """, unsafe_allow_html=True)


# =====================================================
# JOB MATCHING
# =====================================================

elif page == "Job Matching":

    page_heading(
        "Job Matching 🎯",
        "Find suitable job opportunities based on your skills."
    )

    role = st.selectbox(
        "Choose your preferred job role",
        list(job_data.keys()),
        index=list(job_data.keys()).index(
            st.session_state.target
        )
    )

    required = job_data[role]["skills"]

    matched = [
        skill for skill in required
        if skill in st.session_state.skills
    ]

    missing = [
        skill for skill in required
        if skill not in st.session_state.skills
    ]

    percentage = round(
        len(matched) / len(required) * 100
    )

    st.markdown("### Your Job Compatibility")

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card("Match Score", f"{percentage}%", "Based on your skills")

    with col2:
        metric_card("Matched Skills", str(len(matched)), "Available skills")

    with col3:
        metric_card("Missing Skills", str(len(missing)), "Skills to develop")

    st.progress(percentage / 100)

    st.markdown("### Matching Skills")

    for skill in matched:
        st.write(f"🟢 {skill}")

    st.markdown("### Skills to Learn")

    for skill in missing:
        st.write(f"🔴 {skill}")

    st.markdown("### Job Opportunities")

    for title, company, salary in job_data[role]["companies"]:

        st.markdown(f"""
        <div class="job-card">
            <div class="job-title">{title}</div>
            <div class="job-company">{company}</div>
            <br>
            <span class="tag">{salary}</span>
            <span class="tag">Entry Level</span>
        </div>
        """, unsafe_allow_html=True)


# =====================================================
# SKILL GAP ANALYSIS
# =====================================================

elif page == "Skill Gap Analysis":

    page_heading(
        "Skill Gap Analysis 📊",
        "Understand what skills you need for your dream role."
    )

    role = st.selectbox(
        "Select your target role",
        list(job_data.keys())
    )

    required = job_data[role]["skills"]

    matched = [
        skill for skill in required
        if skill in st.session_state.skills
    ]

    missing = [
        skill for skill in required
        if skill not in st.session_state.skills
    ]

    col1, col2 = st.columns(2)

    with col1:

        st.success("Skills You Have")

        for skill in matched:
            st.write(f"✅ {skill}")

    with col2:

        st.warning("Skills to Improve")

        for skill in missing:
            st.write(f"📌 {skill}")

    chart_data = pd.DataFrame({
        "Status": ["Available Skills", "Missing Skills"],
        "Count": [len(matched), len(missing)]
    })

    fig = px.bar(
        chart_data,
        x="Status",
        y="Count",
        color="Status",
        title="Your Skill Gap"
    )

    fig.update_layout(
        height=400,
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown("### Suggested Learning Roadmap")

    for index, skill in enumerate(missing, start=1):

        st.markdown(f"""
        <div class="job-card">
            <b>Step {index}: Learn {skill}</b>
            <p>Learn the fundamentals, practice examples and build a small project.</p>
        </div>
        """, unsafe_allow_html=True)


# =====================================================
# INTERVIEW PREPARATION
# =====================================================

elif page == "Interview Preparation":

    page_heading(
        "Interview Preparation 🎤",
        "Practice technical and HR questions for placements."
    )

    topic = st.selectbox(
        "Select Interview Topic",
        [
            "Python",
            "SQL",
            "OOP",
            "Machine Learning",
            "HR"
        ]
    )

    questions = {

        "Python": [
            "What are Python data types?",
            "Difference between list and tuple?",
            "Explain Python dictionaries.",
            "What are functions?",
            "What is exception handling?"
        ],

        "SQL": [
            "What is SQL?",
            "What is a primary key?",
            "Explain JOIN operations.",
            "Difference between WHERE and HAVING?",
            "What is normalization?"
        ],

        "OOP": [
            "What is object-oriented programming?",
            "Explain inheritance.",
            "What is polymorphism?",
            "What is encapsulation?",
            "What is abstraction?"
        ],

        "Machine Learning": [
            "What is machine learning?",
            "Explain supervised learning.",
            "What is overfitting?",
            "What is a training dataset?",
            "What is classification?"
        ],

        "HR": [
            "Tell me about yourself.",
            "What are your strengths?",
            "Why should we hire you?",
            "Where do you see yourself in five years?",
            "Why do you want this job?"
        ]
    }

    for i, question in enumerate(
        questions[topic],
        start=1
    ):

        with st.expander(
            f"Question {i}: {question}"
        ):

            answer = st.text_area(
                "Write your answer",
                key=f"answer_{topic}_{i}"
            )

            if st.button(
                "Save Answer",
                key=f"save_{topic}_{i}"
            ):

                st.session_state.interview_answers[
                    f"{topic}_{i}"
                ] = answer

                st.success("Answer saved for this session!")

    st.info(
        "Tip: Practice explaining your answers in your own words."
    )


# =====================================================
# CODING TRACKER
# =====================================================

elif page == "Coding Tracker":

    page_heading(
        "Coding Practice Tracker 💻",
        "Track your daily coding practice."
    )

    st.metric(
        "Total Problems Solved",
        st.session_state.solved
    )

    number = st.number_input(
        "Newly solved problems",
        min_value=0,
        max_value=100,
        value=0
    )

    if st.button("Update Progress"):

        st.session_state.solved += number

        save_student_data()

        st.success("Your coding progress has been saved!")

        st.rerun()

    st.markdown("### Your Coding Goals")

    st.write("🎯 Daily goal: Solve 3 problems")

    st.write("📚 Practice Python, SQL and DSA")

    st.progress(
        min(st.session_state.solved / 50, 1.0)
    )


# =====================================================
# STUDENT PROFILE
# =====================================================

elif page == "My Profile":

    page_heading(
        "My Profile 👩‍🎓",
        "Manage your student and career information."
    )

    name = st.text_input(
        "Full Name",
        value=st.session_state.student_name
    )

    target = st.selectbox(
        "Career Goal",
        list(job_data.keys()),
        index=list(job_data.keys()).index(
            st.session_state.target
        )
    )

    all_skills = [
        "Python", "Java", "SQL", "HTML",
        "CSS", "JavaScript", "Pandas",
        "NumPy", "Git", "Machine Learning",
        "Django", "Flask", "REST APIs",
        "Statistics", "Scikit-learn",
        "Deep Learning", "React", "Docker",
        "TensorFlow", "PyTorch", "NLP",
        "LLMs", "Data Visualization", "OOP"
    ]

    skills = st.multiselect(
        "Your Skills",
        all_skills,
        default=[
            s for s in st.session_state.skills
            if s in all_skills
        ]
    )

    if st.button("Save Profile"):

        if not name.strip():
            st.error("Name cannot be empty.")

        else:

            st.session_state.student_name = name.strip()
            st.session_state.target = target
            st.session_state.skills = skills

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users
                SET name = ?
                WHERE id = ?
            """, (
                name.strip(),
                st.session_state.user_id
            ))

            conn.commit()
            conn.close()

            save_student_data()

            st.success("Your profile has been updated!")

            st.rerun()

    st.markdown("### Your Current Skills")

    st.write(", ".join(st.session_state.skills))


# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.markdown(
    """
    <center style='color:#64748b;'>
    CareerPilot | Your Journey Towards Your Dream Job 🚀
    </center>
    """,
    unsafe_allow_html=True
)
