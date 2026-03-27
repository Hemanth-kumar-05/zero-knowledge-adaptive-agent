import csv
from pathlib import Path


CSV_PATH = Path(
    r"c:\Users\hemanthk\Project Work II\extensions\general_data_analyzer\faculty_simulated_grade_sheet.csv"
)

TERM2_COLUMNS = [
    "Tamil_Term2",
    "English_Term2",
    "Maths_Term2",
    "Science_Term2",
    "Social_Term2",
]

FINAL_COLUMNS = [
    "Tamil_Final",
    "English_Final",
    "Maths_Final",
    "Science_Final",
    "Social_Final",
]


def below_35_in_all(row, columns):
    try:
        return all(float(row[col]) < 35 for col in columns)
    except (KeyError, ValueError):
        return False


def main():
    matches = []

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if below_35_in_all(row, TERM2_COLUMNS) and below_35_in_all(row, FINAL_COLUMNS):
                matches.append((row["Student_ID"], row["Student_Name"]))

    if not matches:
        print("No students found below 35 in all Term 2 and Final subjects.")
        return

    print("Students below 35 in all Term 2 and Final subjects:")
    for student_id, student_name in matches:
        print(f"{student_id} - {student_name}")


if __name__ == "__main__":
    main()
