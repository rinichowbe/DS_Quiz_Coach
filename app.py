import sqlite3, random
from datetime import datetime
import streamlit as st
import pandas as pd

st.set_page_config(page_title="DS Quiz Coach", page_icon="🧠", layout="centered")

# ---------- Database ----------
conn = sqlite3.connect("quiz.db", check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS attempts(
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, subject TEXT,
    correct INT, wrong INT, skipped INT, accuracy REAL, taken_at TEXT)""")

# ---------- Question bank: (question, options, answer, explanation) ----------
BANK = {
 "Python": [
  ("Which is a valid variable name?", ["2name","first_name","first-name","class"], "first_name",
   "Names may contain letters, digits, underscores but cannot start with a digit or be a keyword."),
  ("Output of len([1,2,3])?", ["2","3","4","Error"], "3", "len() returns the number of items."),
  ("Which type is immutable?", ["list","dict","tuple","set"], "tuple", "Tuples cannot be changed after creation."),
  ("Which keyword defines a function?", ["func","def","function","lambda only"], "def", "Functions start with def."),
  ("What does range(3) produce?", ["1,2,3","0,1,2","0,1,2,3","3"], "0,1,2", "range starts at 0 and stops before 3."),
 ],
 "Data Science": [
  ("Which library gives DataFrames?", ["NumPy","Pandas","Seaborn","SciPy"], "Pandas", "Pandas provides Series and DataFrame."),
  ("df.head() shows?", ["Last 5 rows","First 5 rows","Column names","Summary stats"], "First 5 rows", "head() defaults to 5 rows."),
  ("Which handles missing values?", ["fillna()","merge()","pivot()","plot()"], "fillna()", "fillna() replaces NaN values."),
  ("np.mean([2,4,6]) is?", ["3","4","5","6"], "4", "(2+4+6)/3 = 4."),
  ("Which measure is robust to outliers?", ["Mean","Median","Range","Variance"], "Median", "Median ignores extreme values."),
 ],
 "Visualization": [
  ("Best chart for category comparison?", ["Bar chart","Scatter","Histogram","Heatmap"], "Bar chart", "Bars compare discrete categories."),
  ("Which plots a distribution?", ["Histogram","Pie","Line","Bar of means"], "Histogram", "Histograms show frequency across bins."),
  ("A log scale is useful when data...", ["is tiny","spans orders of magnitude","is negative","is categorical"], "spans orders of magnitude", "Log axes compress large ranges."),
  ("Scatter plots show?", ["Trend over time only","Relationship of two variables","Proportions","Rankings"], "Relationship of two variables", "Each point is an (x, y) pair."),
  ("Which library is built on Matplotlib?", ["Seaborn","Flask","Requests","Pytest"], "Seaborn", "Seaborn wraps Matplotlib."),
 ],
}

def grade(acc):
    return "A" if acc >= 85 else "B" if acc >= 70 else "C" if acc >= 50 else "D"

ss = st.session_state
for k, v in {"page": "home", "i": 0, "c": 0, "w": 0, "s": 0, "qs": [], "fb": None}.items():
    ss.setdefault(k, v)

st.sidebar.title("🧠 DS Quiz Coach")
ss.page = st.sidebar.radio("Go to", ["home", "quiz", "results", "history", "leaderboard", "about"],
                           index=["home","quiz","results","history","leaderboard","about"].index(ss.page))

# ---------- Home ----------
if ss.page == "home":
    st.title("🧠 DS Quiz Coach")
    a, b, c = st.columns(3)
    a.info("📚 **Learn**\n\nPractice subject-wise quizzes.")
    b.success("📊 **Analyze**\n\nTrack accuracy and grade.")
    c.warning("🏆 **Improve**\n\nReview weak topics.")
    st.subheader("🎓 Student Information")
    name = st.text_input("Enter your name")
    subject = st.selectbox("Choose subject", list(BANK))
    tutor = st.checkbox("AI Tutor mode (explain answers)", value=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Subjects", len(BANK)); m2.metric("Questions", sum(map(len, BANK.values())))
    m3.metric("Tutor", "ON" if tutor else "OFF")
    if st.button("▶ Start Quiz") and name.strip():
        qs = BANK[subject][:]; random.shuffle(qs)
        ss.update(name=name.strip(), subject=subject, tutor=tutor, qs=qs, i=0, c=0, w=0, s=0, fb=None, page="quiz")
        st.rerun()
    elif name == "":
        st.caption("Enter your name to begin.")

# ---------- Quiz ----------
elif ss.page == "quiz":
    if not ss.qs:
        st.warning("Start a quiz from Home first.")
    elif ss.i >= len(ss.qs):
        acc = ss.c / len(ss.qs) * 100
        conn.execute("INSERT INTO attempts(name,subject,correct,wrong,skipped,accuracy,taken_at) VALUES(?,?,?,?,?,?,?)",
                     (ss.name, ss.subject, ss.c, ss.w, ss.s, acc, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit(); ss.acc = acc; ss.qs = []; ss.page = "results"; st.rerun()
    else:
        q, opts, ans, exp = ss.qs[ss.i]
        st.progress(ss.i / len(ss.qs)); st.caption(f"Question {ss.i+1} of {len(ss.qs)}")
        st.subheader(q)
        pick = st.radio("Select your answer:", opts, index=None, key=f"r{ss.i}")
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ Submit") and pick and ss.fb is None:
            ok = pick == ans; ss.c += ok; ss.w += (not ok); ss.fb = (ok, ans, exp)
        if c2.button("⏭ Skip") and ss.fb is None:
            ss.s += 1; ss.i += 1; st.rerun()
        if c3.button("💡 Hint"):
            st.info(f"Hint: the answer starts with '{ans[0]}'.")
        if ss.fb:
            ok, ans, exp = ss.fb
            (st.success if ok else st.error)("🎉 Correct!" if ok else f"❌ Wrong. Answer: {ans}")
            if ss.tutor:
                st.info(f"🧠 **AI Tutor Explanation**\n\n✔ Correct answer: {ans}\n\n💡 {exp}")
            if st.button("Next ➡"):
                ss.fb = None; ss.i += 1; st.rerun()

# ---------- Results ----------
elif ss.page == "results":
    row = conn.execute("SELECT name,subject,correct,wrong,skipped,accuracy FROM attempts ORDER BY id DESC LIMIT 1").fetchone()
    if row:
        n, s, c, w, k, acc = row
        st.header("📊 Performance Report")
        a, b = st.columns(2)
        a.metric("Student", n); b.metric("Accuracy", f"{acc:.2f}%")
        a.metric("Subject", s); b.metric("Grade", grade(acc))
        st.header("📈 Analytics Dashboard")
        x, y, z = st.columns(3); x.metric("Correct", c); y.metric("Wrong", w); z.metric("Skipped", k)
        st.bar_chart(pd.DataFrame({"count": [c, w, k]}, index=["Correct", "Wrong", "Skipped"]))
    else:
        st.info("No attempts yet.")

# ---------- History ----------
elif ss.page == "history":
    st.header("🕘 Quiz History")
    df = pd.read_sql("SELECT name,subject,correct,wrong,skipped,accuracy,taken_at FROM attempts ORDER BY id DESC", conn)
    if len(df):
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No history yet.")

# ---------- Leaderboard ----------
elif ss.page == "leaderboard":
    st.header("🏆 Leaderboard")
    df = pd.read_sql("SELECT name,subject,accuracy FROM attempts ORDER BY accuracy DESC LIMIT 10", conn)
    if len(df):
        st.table(df)
    else:
        st.info("No scores yet.")

# ---------- About ----------
else:
    st.header("ℹ About DS Quiz Coach")
    st.write("An interactive quiz platform built with **Python** and **Streamlit** to strengthen "
             "Python, Data Science and Visualization concepts through quizzes, explanations and analytics.")
