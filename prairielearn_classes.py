import requests
import matplotlib.pyplot as plt


class Course:
    def __init__(self, course_id, token):
        """
        Initialize a Course instance.

        Args:
            course_id (str): ID of the course instance.
            token (str): Personal access token for PrairieLearn API.
        """
        self.course_id = course_id
        self.token = token
        self.students = []
        self.assessments = []

    def fetch_students(self):
        """Fetch all students in the course and populate the `students` list."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/gradebook"
        headers = {"Private-Token": self.token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            gradebook_data = response.json()
            self.students = [
                Student(student["user_id"], student["user_name"], student["user_uid"], student["assessments"])
                for student in gradebook_data
            ]
            # Print the number of students fetched
            print(f"Fetched {len(self.students)} students.")
        else:
            raise ValueError(f"Failed to fetch students. Status Code: {response.status_code}")

    def fetch_assessments(self):
        """Fetch all assessments in the course and populate the `assessments` list."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/assessments"
        headers = {"Private-Token": self.token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            assessments_data = response.json()
            self.assessments = [
                Assessment(assessment["assessment_id"], assessment["assessment_name"], assessment["assessment_label"])
                for assessment in assessments_data
            ]

            # Print each assessment name on a new line
            print("Fetched assessments:")
            for assessment in self.assessments:
                print(f"- {assessment.name} (Label: {assessment.label})")
        else:
            raise ValueError(f"Failed to fetch assessments. Status Code: {response.status_code}")

    def get_assessment_summary_statistics(self):
        """Compute and print summary statistics for each assessment in the course."""
        if not self.assessments:
            print("No assessments available. Please fetch assessments first.")
            return

        print("\nAssessment Summary Statistics:")
        for assessment in self.assessments:
            # Fetch submissions for the assessment
            url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/assessments/{assessment.assessment_id}/assessment_instances"
            headers = {"Private-Token": self.token}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                submissions = response.json()
                scores = [
                    submission.get("score_perc", 0)
                    for submission in submissions
                    if submission.get("score_perc") is not None
                ]

                if scores:
                    mean_score = sum(scores) / len(scores)
                    max_score = max(scores)
                    min_score = min(scores)
                    print(f"\nAssessment: {assessment.name} (Label: {assessment.label})")
                    print(f"  - Number of submissions: {len(scores)}")
                    print(f"  - Mean score: {mean_score:.2f}%")
                    print(f"  - Max score: {max_score:.2f}%")
                    print(f"  - Min score: {min_score:.2f}%")
                else:
                    print(f"\nAssessment: {assessment.name} (Label: {assessment.label})")
                    print("  - No submissions available.")
            else:
                print(f"Failed to fetch submissions for assessment {assessment.name}.")


class Assessment:
    def __init__(self, assessment_id, name, label):
        """
        Initialize an Assessment instance.

        Args:
            assessment_id (str): ID of the assessment.
            name (str): Name of the assessment.
            label (str): Label of the assessment.
        """
        self.assessment_id = assessment_id
        self.name = name
        self.label = label
        self.scores = []

    def fetch_submissions(self, course_id, token):
        """Fetch all submissions for this assessment."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{course_id}/assessments/{self.assessment_id}/assessment_instances"
        headers = {"Private-Token": token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            submissions = response.json()
            self.scores = [submission.get("score_perc", 0) for submission in submissions]
        else:
            raise ValueError(f"Failed to fetch submissions. Status Code: {response.status_code}")


class Student:
    def __init__(self, student_id, name, email, grades):
        """
        Initialize a Student instance.

        Args:
            student_id (str): ID of the student.
            name (str): Name of the student.
            email (str): Email of the student.
            grades (list): List of dictionaries containing assessment grades.
        """
        self.student_id = student_id
        self.name = name
        self.email = email
        self.grades = grades

    def get_performance(self):
        """Visualize the student's performance across assessments."""
        assessment_names = [grade["assessment_name"] for grade in self.grades]
        scores = [
            grade["score_perc"] if grade["score_perc"] is not None else 0
            for grade in self.grades
        ]

        # Visualize the data
        plt.figure(figsize=(10, 6))
        plt.bar(assessment_names, scores, color="skyblue", edgecolor="black")
        plt.title(f"Performance of {self.name} Across Assessments", fontsize=14)
        plt.xlabel("Assessment Name", fontsize=12)
        plt.ylabel("Score Percentage (%)", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.ylim(0, 100)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()
