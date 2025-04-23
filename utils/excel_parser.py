import pandas as pd
from io import BytesIO

def load_dataframe(file):
    filename = file.filename.lower()
    if filename.endswith(".csv"):
        return pd.read_csv(file.file)
    elif filename.endswith(".xls") or filename.endswith(".xlsx"):
        return pd.read_excel(BytesIO(file.file.read()))
    else:
        raise ValueError("Unsupported file type. Upload a .csv or .xlsx file.")

def parse_students_file(file):
    """
    Parse Excel or CSV file for student registration.
    Expected columns: email, password,stream,name
    """
    df = load_dataframe(file)
    students = []
    for _, row in df.iterrows():
        student = {
            "email": str(row["email"]).strip(),
            "password": str(row["password"]).strip(),
            "stream": str(row["stream"]).strip(),
            "name": str(row["name"]).strip(),
            "contact_number": str(row["contact_number"]).strip(),
            "university": str(row["university"]).strip(),
            "year_of_study": str(row["year_of_study"]).strip()
        }
        students.append(student)
    return students

def parse_questions_file(file, category):
    """
    Parse Excel or CSV file for questions.
    Expected columns: question, option_a, option_b, option_c, option_d, correct_option
    """
    df = load_dataframe(file)
    questions = []
    for _, row in df.iterrows():
        question = {
            "category": category,
            "question": str(row["question"]).strip(),
            "option_a": str(row["option_a"]).strip(),
            "option_b": str(row["option_b"]).strip(),
            "option_c": str(row["option_c"]).strip(),
            "option_d": str(row["option_d"]).strip(),
            "correct_option": str(row["correct_option"]).strip().lower()
        }
        questions.append(question)
    return questions
