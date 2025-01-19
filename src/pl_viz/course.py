import requests
import altair as alt
import pandas as pd
from assessment import Assessment
from student import Student

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
