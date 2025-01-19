import requests
import altair as alt
import pandas as pd

class Student:
    def __init__(self, user_id, user_name, user_uid, token):
        """
        Initialize a Student instance.
        """
        self.user_id = user_id
        self.user_name = user_name
        self.user_uid = user_uid
        self.token = token

        self.courses = []
        self.grades = []

    def add_course(self, course):
        """Add a course to the student's list of courses."""
        if course not in self.courses:
            self.courses.append(course)

    def list_courses(self):
        """Print the student's name and the courses they are enrolled in."""
        print(f"Student: {self.user_name}")
        if self.courses:
            print("Enrolled in the following courses:")
            for course in self.courses:
                print(f"- Course ID: {course.course_id}")
        else:
            print("Not enrolled in any courses.")

    def fetch_all_grades(self):
        """
        Fetch all grades for the student across their courses.
        """
        grades = []

        for course in self.courses:
            # Fetch the gradebook for the course
            url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{course.course_id}/gradebook"
            headers = {"Private-Token": self.token}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                gradebook_data = response.json()

                # Find the current student in the gradebook
                student_data = next((student for student in gradebook_data if student["user_id"] == self.user_id), None)

                if student_data:
                    # Extract grades for this student's assessments
                    for assessment in student_data["assessments"]:
                        grades.append({
                            "course_code": course.course_code,  # Add course_code if available
                            "course_id": course.course_id,
                            "assessment_id": assessment["assessment_id"],
                            "assessment_name": assessment["assessment_name"],
                            "assessment_label": assessment["assessment_label"],
                            "score_perc": assessment["score_perc"]
                        })

            else:
                print(f"Failed to fetch gradebook for course {course.course_id}. Status Code: {response.status_code}")

        self.grades = grades
        return grades

    def plot_grades(self, course_code=None, assessment_label=None):
        """
        Plot the grades of the student using Altair. Optionally filter by one or more course_codes.

        Args:
            course_code (str or list of str, optional): If provided, only plot grades for the specified course code(s).
        """
        if not self.grades:
            self.fetch_all_grades()

        # Normalize course_code to a list for consistent handling
        if isinstance(course_code, str):
            course_code = [course_code]
        if isinstance(assessment_label, str):
            assessment_label = [assessment_label]

        # Filter grades by course_code and assessment_label if provided
        grades_to_plot = [
            grade
            for grade in self.grades
            if (course_code is None or grade["course_code"] in course_code) and
            (assessment_label is None or grade["assessment_label"] in assessment_label)
        ]

        if not grades_to_plot:
            if course_code or assessment_label:
                filters = []
                if course_code:
                    filters.append(f"course(s): {', '.join(course_code)}")
                if assessment_label:
                    filters.append(f"assessment label(s): {', '.join(assessment_label)}")
                print(f"No grades found for {', '.join(filters)}.")
            else:
                print("No grades found.")
            return

        # Create a DataFrame from the grades
        df = pd.DataFrame(grades_to_plot)

        # Replace None scores with 0 for visualization
        df["score_perc"] = df["score_perc"].fillna(0)

        # Create a new variable for the x-axis to uniquely identify assessments
        df["true_assessment_name"] = (
            df["course_code"]
            + " - "
            + df["assessment_name"]
            + " ("
            + df["assessment_label"]
            + ")"
        )

        # Create the Altair bar chart
        bars = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("score_perc:Q", title="Score Percentage", scale=alt.Scale(domain=[0, 100])),
                y=alt.Y("true_assessment_name:N", title="Assessments", sort=None),
                color=alt.Color("course_code:N", title="Course Code"),
                tooltip=["course_code", "assessment_name", "assessment_label", "score_perc"],
            )
            .properties(
                width=600,
                height=400,
            )
        )

        # Add text annotations for the scores
        annotations = (
            alt.Chart(df)
            .mark_text(dx=15, fontSize=10, fontWeight="bold", color="black")
            .encode(
                y=alt.Y("true_assessment_name:N", sort=None),
                x=alt.X("score_perc:Q"),
                text=alt.Text("score_perc:Q", format=".1f"),
            )
        )

        # Combine bars and annotations
        chart = (bars + annotations).properties(
            title=f"Grades for {self.user_name}" + (f" in {', '.join(course_code)}" if course_code else "")
        )

        # Display the chart
        chart.display()


def fetch_data(course_ids, token):

    global_students = {}
    global_courses = {}
    global_assessments = {}

    for course_code, course_id in course_ids.items():

        course = Course(course_code, course_id, token)
        global_courses[course_code] = course

        course.fetch_students(global_students)
        course.fetch_assessments(global_assessments)
    
    return global_courses, global_assessments, global_students

def find_students(global_students, user_names=None, cwls=None):
    """
    Retrieve student instances from global_students using either user_names or CWLs.

    Args:
        global_students (dict): Dictionary of student instances with user_id as keys.
        user_names (list[str], optional): List of names of students to search for.
        cwls (list[str], optional): List of CWLs (Campus Wide Login) of students to search for.

    Returns:
        dict: A dictionary where the key is the provided identifier (user_name or cwl),
              and the value is the matching student instance(s).

    Raises:
        ValueError: If both `user_names` and `cwls` are provided, or if neither is provided.
    """
    # Validate input to ensure only one of user_names or cwls is provided
    if (user_names and cwls) or (not user_names and not cwls):
        raise ValueError("You must provide either user_names or cwls, but not both.")

    # Normalize inputs to lists if they are not already
    if user_names and isinstance(user_names, str):
        user_names = [user_names]
    if cwls and isinstance(cwls, str):
        cwls = [cwls]

    # Initialize the results dictionary
    results = {}

    # Search by user_names
    if user_names:
        for name in user_names:
            matches = [
                student for student in global_students.values() if student.user_name == name
            ]
            if len(matches) == 1:
                results[name] = matches[0]
            elif len(matches) > 1:
                print(f"Ambiguity: Multiple students found with name '{name}'.")
                results[name] = matches  # Add all matches to allow the caller to resolve ambiguity
            else:
                print(f"No students found with name '{name}'.")
                results[name] = None

    # Search by CWLs
    if cwls:
        for cwl in cwls:
            # Construct user_uid from CWL
            user_uid = f"{cwl}@ubc.ca"
            match = next((student for student in global_students.values() if student.user_uid == user_uid), None)
            if match:
                results[cwl] = match
            else:
                print(f"No students found with CWL '{cwl}'.")
                results[cwl] = None

    return results