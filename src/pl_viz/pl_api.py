from typing import List, Optional, Dict, Union
import requests
import altair as alt
import pandas as pd
import statistics

class Course:
    """A class to represent a course."""

    def __init__(self, course_code: str, course_id: int, token: str):
        """
        Initialize a Course instance.

        Parameters
        ----------
        course_code : str
            The code of the course (e.g., 'MATH101').
        course_id : int
            The unique identifier for the course.
        token : str
            Authentication token for the course.
        """
        self.course_code: str = course_code
        self.course_id: int = course_id
        self.students: List['Student'] = []
        self.assessments: List['Assessment'] = []
        self.token: str = token

    def fetch_students(self, global_students: Optional[Dict[int, 'Student']] = None) -> None:
        """Fetch all students in the course and populate the `students` list.

        Parameters
        ----------
        global_students : dict, optional
            A dictionary to map global student instances for reuse.
        """
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
                    student_instance = Student(student_id, name, email, self.token)

                # Add course to the student and append to the course's student list
                student_instance.add_course(self)
                self.students.append(student_instance)

            # Print the number of students fetched
            print(f"\nFetched {len(self.students)} students for course code {self.course_code}.")
        else:
            raise ValueError(f"Failed to fetch students. Status Code: {response.status_code}")

    def fetch_assessments(self, global_assessments: Optional[Dict[int, 'Assessment']] = None) -> None:
        """Fetch all assessments in the course and populate the `assessments` list.

        Parameters
        ----------
        global_assessments : dict, optional
            A dictionary to map global assessment instances for reuse.
        """
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

    def show_student_list(self) -> None:
        """Show the list of students enrolled in the course."""
        if not self.students:
            self.fetch_students()
            
        print(f"\nThere are {len(self.students)} students in Course {self.course_code}:")

        for student in self.students:
            print(f"User ID: {student.user_id}, User Name: {student.user_name}, User UID: {student.user_uid}")

    def get_assessment_summary_statistics(self) -> None:
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


    def plot_boxplot(self, assessment_label: Optional[List[str]] = None) -> None:
        """Plot boxplots for score distributions of all or specified assessments.

        Parameters
        ----------
        assessment_label : list of str, optional
            List of assessment labels to include in the plot.
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
            

    def plot_histogram(self, assessment_label: Optional[List[str]] = None, bins: int = 20) -> None:
        """Plot a layered histogram for score distributions of all or specified assessments.

        Parameters
        ----------
        assessment_label : list of str, optional
            List of assessment labels to include in the plot.
        bins : int, optional
            Number of bins for the histogram, default is 20.
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
    """A class to represent an assessment in a course.

    Attributes
    ----------
    assessment_id : int
        The unique identifier for the assessment.
    name : str
        The name of the assessment (e.g., 'Midterm Exam').
    label : str
        A unique label for the assessment (e.g., 'midterm_1').
    course_id : int
        The unique identifier for the course this assessment belongs to.
    token : str
        Authentication token for accessing course data.
    scores : list
        A list of scores (in percentage) for all submissions to the assessment.

    Methods
    -------
    fetch_submissions()
        Fetch all submissions for this assessment and populate the `scores` list.
    get_summary_statistics()
        Compute and return summary statistics for the scores.
    plot_score_histogram()
        Plot a histogram of the score percentages using Altair.
    """

    def __init__(self, assessment_id: int, name: str, label: str, course_id: int, token: str):
        """
        Initialize an Assessment instance.

        Parameters
        ----------
        assessment_id : int
            The unique identifier for the assessment.
        name : str
            The name of the assessment.
        label : str
            A unique label for the assessment.
        course_id : int
            The unique identifier for the course this assessment belongs to.
        token : str
            Authentication token for accessing course data.
        """
        self.assessment_id = assessment_id
        self.name = name
        self.label = label
        self.course_id = course_id
        self.token = token

        self.scores = []

    def fetch_submissions(self) -> None:
        """Fetch all submissions for this assessment and populate the `scores` list.

        Raises
        ------
        ValueError
            If the API request fails.
        """
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/assessments/{self.assessment_id}/assessment_instances"
        headers = {"Private-Token": self.token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            submissions = response.json()
            self.scores = [submission.get("score_perc", 0) for submission in submissions if submission.get("score_perc") is not None]
        else:
            raise ValueError(f"Failed to fetch submissions for assessment {self.name}. Status Code: {response.status_code}")

    def get_summary_statistics(self) -> Dict[str, float]:
        """Compute and return summary statistics for the scores.

        Returns
        -------
        dict
            A dictionary containing summary statistics:
            - num_submissions : int
                Number of submissions.
            - mean_score : float
                Average score percentage.
            - median_score : float
                Median score percentage.
            - max_score : float
                Maximum score percentage.
            - min_score : float
                Minimum score percentage.
        
        Raises
        ------
        ValueError
            If there are no scores available.
        """
        if not self.scores:
            self.fetch_submissions()

        if not self.scores:
            raise ValueError("No scores available to compute statistics.")

        return {
            "num_submissions": len(self.scores),
            "mean_score": sum(self.scores) / len(self.scores),
            "median_score": statistics.median(self.scores),
            "max_score": max(self.scores),
            "min_score": min(self.scores),
        }

    def plot_score_histogram(self) -> None:
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
    """A class to represent a student.

    Attributes
    ----------
    user_id : int
        The unique identifier for the student.
    user_name : str
        The name of the student.
    user_uid : str
        The UID (email or unique identifier) of the student.
    token : str
        Authentication token for accessing data.
    courses : list
        A list of courses the student is enrolled in.
    grades : list
        A list of grades across all courses.

    Methods
    -------
    add_course(course)
        Add a course to the student's list of courses.
    list_courses()
        Print the student's name and the courses they are enrolled in.
    fetch_all_grades()
        Fetch all grades for the student across their courses.
    plot_grades(course_code=None, assessment_label=None)
        Plot the grades of the student using Altair, optionally filtered by course or assessment.
    """
    
    def __init__(self, user_id: int, user_name: str, user_uid: str, token: str):
        """
        Initialize a Student instance.

        Parameters
        ----------
        user_id : int
            The unique identifier for the student.
        user_name : str
            The name of the student.
        user_uid : str
            The UID (email or unique identifier) of the student.
        token : str
            Authentication token for accessing data.
        """
        self.user_id = user_id
        self.user_name = user_name
        self.user_uid = user_uid
        self.token = token

        self.courses = []
        self.grades = []

    def add_course(self, course: 'Course') -> None:
        """Add a course to the student's list of courses.

        Parameters
        ----------
        course : Course
            The course to add to the student's list.
        """
        if course not in self.courses:
            self.courses.append(course)

    def list_courses(self) -> None:
        """Print the student's name and the courses they are enrolled in."""
        print(f"Student: {self.user_name}")
        if self.courses:
            print("Enrolled in the following courses:")
            for course in self.courses:
                print(f"- Course ID: {course.course_id}")
        else:
            print("Not enrolled in any courses.")

    def fetch_all_grades(self) -> List[Dict[str, Union[str, int, float]]]:
        """Fetch all grades for the student across their courses.

        Returns
        -------
        list of dict
            A list of dictionaries containing grades for each assessment.

        Raises
        ------
        ValueError
            If the gradebook cannot be fetched for any course.
        """
        grades = []
        for course in self.courses:
            url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{course.course_id}/gradebook"
            headers = {"Private-Token": self.token}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                gradebook_data = response.json()
                student_data = next((student for student in gradebook_data if student["user_id"] == self.user_id), None)

                if student_data:
                    for assessment in student_data["assessments"]:
                        grades.append({
                            "course_code": course.course_code,
                            "course_id": course.course_id,
                            "assessment_id": assessment["assessment_id"],
                            "assessment_name": assessment["assessment_name"],
                            "assessment_label": assessment["assessment_label"],
                            "score_perc": assessment["score_perc"]
                        })
            else:
                raise ValueError(f"Failed to fetch gradebook for course {course.course_id}. Status Code: {response.status_code}")

        self.grades = grades
        return grades

    def plot_grades(self, course_code: Optional[Union[str, List[str]]] = None, assessment_label: Optional[Union[str, List[str]]] = None) -> None:
        """Plot the grades of the student using Altair. Optionally filter by course or assessment.

        Parameters
        ----------
        course_code : str or list of str, optional
            The course code(s) to filter grades by.
        assessment_label : str or list of str, optional
            The assessment label(s) to filter grades by.

        Raises
        ------
        ValueError
            If no grades are available for the specified filters.
        """
        if not self.grades:
            self.fetch_all_grades()

        if isinstance(course_code, str):
            course_code = [course_code]
        if isinstance(assessment_label, str):
            assessment_label = [assessment_label]

        grades_to_plot = [
            grade for grade in self.grades
            if (course_code is None or grade["course_code"] in course_code) and
            (assessment_label is None or grade["assessment_label"] in assessment_label)
        ]

        if not grades_to_plot:
            filters = []
            if course_code:
                filters.append(f"course(s): {', '.join(course_code)}")
            if assessment_label:
                filters.append(f"assessment label(s): {', '.join(assessment_label)}")
            raise ValueError(f"No grades found for {', '.join(filters)}.")

        df = pd.DataFrame(grades_to_plot)
        df["score_perc"] = df["score_perc"].fillna(0)
        df["true_assessment_name"] = (
            df["course_code"] + " - " + df["assessment_name"] + " (" + df["assessment_label"] + ")"
        )

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

        annotations = (
            alt.Chart(df)
            .mark_text(dx=15, fontSize=10, fontWeight="bold", color="black")
            .encode(
                y=alt.Y("true_assessment_name:N", sort=None),
                x=alt.X("score_perc:Q"),
                text=alt.Text("score_perc:Q", format=".1f"),
            )
        )

        chart = (bars + annotations).properties(
            title=f"Grades for {self.user_name}" + (f" in {', '.join(course_code)}" if course_code else "")
        )

        chart.display()
