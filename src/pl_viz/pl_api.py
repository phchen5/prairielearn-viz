import requests
import altair as alt
import pandas as pd
import statistics

class Course:
    def __init__(self, course_code, course_id, token):
        """
        Initialize a Course instance.
        """
        self.course_code = course_code
        self.course_id = course_id
        self.students = []
        self.assessments = []

        self.token = token

    def fetch_students(self, global_students=None):
        """Fetch all students in the course and populate the `students` list."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/gradebook"
        headers = {"Private-Token": self.token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            gradebook_data = response.json()

            for student in gradebook_data:

                student_id = student["user_id"]
                name = student["user_name"]
                email = student["user_uid"]

                # Create or retrieve the student instance
                if global_students is not None:
                    if student_id not in global_students:
                        student_instance = Student(student_id, name, email, self.token)
                        global_students[student_id] = student_instance
                    else:
                        student_instance = global_students[student_id]
                else:
                    student_instance = Student(student_id, name, email)

                # Add course to the student and append to the course's student list
                student_instance.add_course(self)
                self.students.append(student_instance)

            # Print the number of students fetched
            print(f"\nFetched {len(self.students)} students for course code {self.course_code}.")
        else:
            raise ValueError(f"Failed to fetch students. Status Code: {response.status_code}")

    def fetch_assessments(self, global_assessments=None):
        """Fetch all assessments in the course and populate the `assessments` list."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/assessments"
        headers = {"Private-Token": self.token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            assessments_data = response.json()

            for assessment in assessments_data:

                assessment_id = assessment["assessment_id"]
                assessment_name = assessment["assessment_name"]
                assessment_label = assessment["assessment_label"]

                # Create or retrieve the assessment instance
                if global_assessments is not None:
                    if assessment_id not in global_assessments:
                        global_assessments[assessment_id] = Assessment(
                            assessment_id, assessment_name, assessment_label, self.course_id, self.token
                        )
                    assessment_instance = global_assessments[assessment_id]
                else:
                    assessment_instance = Assessment(
                        assessment_id, assessment_name, assessment_label, self.course_id
                    )

                # Append to the course's assessments list
                self.assessments.append(assessment_instance)

            # Print each assessment name on a new line
            print("Fetched assessments:")
            for assessment in self.assessments:
                print(f"- {assessment.name} (Label: {assessment.label})")
        else:
            raise ValueError(f"Failed to fetch assessments. Status Code: {response.status_code}")

    def show_student_list(self):
        """Show the list of students enrolled in the course."""

        if not self.students:
            self.fetch_students()
            
        print(f"\nThere are {len(self.students)} students in Course {self.course_code}:")

        for student in self.students:
            print(f"User ID: {student.user_id}, User Name: {student.user_name}, User UID: {student.user_uid}")

    def get_assessment_summary_statistics(self):
        """Compute and print summary statistics for each assessment in the course."""
        if not self.assessments:
            self.fetch_assessments()

        print("\nAssessment Summary Statistics:")
        for assessment in self.assessments:
            # Fetch submissions for the assessment
            assessment.fetch_submissions()

            # Get summary statistics using the Assessment class method
            stats = assessment.get_summary_statistics()

            print(f"\nAssessment: {assessment.name} (Label: {assessment.label})")
            print(f"  - Number of submissions: {stats['num_submissions']}")
            print(f"  - Mean score: {stats['mean_score']:.2f}%" if stats['mean_score'] is not None else "  - Mean score: N/A")
            print(f"  - Median score: {stats['median_score']:.2f}%" if stats['median_score'] is not None else "  - Median score: N/A")
            print(f"  - Max score: {stats['max_score']:.2f}%" if stats['max_score'] is not None else "  - Max score: N/A")
            print(f"  - Min score: {stats['min_score']:.2f}%" if stats['min_score'] is not None else "  - Min score: N/A")


    def plot_boxplot(self, assessment_label=None):
        """
        Plot boxplots for score distributions of all assessments in the course.

        Args:
            token (str): Access token for fetching submissions.
        """
        if not self.assessments:
            self.fetch_assessments()

        # Collect data for all assessments
        data = []
        for assessment in self.assessments:
            # Fetch submissions for the assessment

            if assessment_label and assessment.label in assessment_label:

                assessment.fetch_submissions()

                # Append the scores with assessment metadata
                data.extend([
                    {"assessment_name": f"{assessment.name} ({assessment.label})", "score": score}
                    for score in assessment.scores
                ])

        # Check if there's data to plot
        if not data:
            print("No data available to plot.")
            return

        # Convert to a DataFrame
        df = pd.DataFrame(data)

        # Create the Altair boxplot
        chart = (
            alt.Chart(df)
            .mark_boxplot()
            .encode(
                y=alt.Y("assessment_name:N", title="Assessments", sort=None),
                x=alt.X("score:Q", title="Score Percentage", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("assessment_name:N", legend=None),  # Optional for differentiation
                tooltip=["assessment_name", "score"],
            )
            .properties(
                title=f"Score Distribution Across Assessments in {self.course_code}",
                width=600,
                height=400,
            )
        )

        # Display the chart
        chart.display()
            

    def plot_histogram(self, assessment_label=None, bins=20):
        """
        Plot boxplots for score distributions of all assessments in the course.

        Args:
            token (str): Access token for fetching submissions.
        """
        if not self.assessments:
            self.fetch_assessments()

        # Collect data for all assessments
        data = []
        for assessment in self.assessments:
            # Fetch submissions for the assessment

            if assessment_label and assessment.label in assessment_label:

                assessment.fetch_submissions()

                # Append the scores with assessment metadata
                data.extend([
                    {"assessment_name": f"{assessment.name} ({assessment.label})", "score": score}
                    for score in assessment.scores
                ])

        # Check if there's data to plot
        if not data:
            print("No data available to plot.")
            return

        # Convert to a DataFrame
        df = pd.DataFrame(data)

        # Create the Altair layered histogram
        chart = (
            alt.Chart(df)
            .mark_bar(opacity=0.3, binSpacing=0)
            .encode(
                x=alt.X("score:Q", bin=alt.Bin(maxbins=bins), title="Score Percentage"),
                y=alt.Y("count():Q", title="Count").stack(None),
                color=alt.Color("assessment_name:N", title="Assessments"),
            )
            .properties(
                title=f"Layered Histogram of Scores in {self.course_code}",
                width=600,
                height=400,
            )
        )

        # Display the chart
        chart.display()

class Assessment:
    def __init__(self, assessment_id, name, label, course_id, token):
        """
        Initialize an Assessment instance.
        """
        self.assessment_id = assessment_id
        self.name = name
        self.label = label
        self.course_id = course_id
        self.token = token

        self.scores = []

    def fetch_submissions(self):
        """Fetch all submissions for this assessment."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/assessments/{self.assessment_id}/assessment_instances"
        headers = {"Private-Token": self.token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            submissions = response.json()
            self.scores = [submission.get("score_perc", 0) for submission in submissions if submission.get("score_perc") is not None]
        else:
            raise ValueError(f"Failed to fetch submissions for assessment {self.name}. Status Code: {response.status_code}")

    def get_summary_statistics(self):
        """Compute summary statistics for the assessment."""

        if not self.scores:
            self.fetch_submissions()

        return {
            "num_submissions": len(self.scores),
            "mean_score": sum(self.scores) / len(self.scores),
            "median_score": statistics.median(self.scores),
            "max_score": max(self.scores),
            "min_score": min(self.scores)
        }

    def plot_score_histogram(self):
        """Plot a histogram of the score percentages using Altair."""
        if not self.scores:
            self.fetch_submissions()

        # Create a DataFrame from the scores
        df = pd.DataFrame({"scores": self.scores})

        # Create the Altair histogram
        histogram = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("scores:Q", bin=alt.Bin(maxbins=10), title="Score Percentage"),
                y=alt.Y("count():Q", title="Frequency"),
                tooltip=[
                    alt.Tooltip("scores:Q", title="Score Range"),
                    alt.Tooltip("count():Q", title="Frequency")
                ]
            )
            .properties(
                title=f"Score Distribution for {self.name} (Label: {self.label})",
                width=600,
                height=400
            )
        )

        # Display the histogram
        histogram.display()


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