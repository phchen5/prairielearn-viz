import requests
import matplotlib.pyplot as plt
import statistics

class Course:
    def __init__(self, course_code, course_id):
        """
        Initialize a Course instance.

        Args:
            course_id (str): ID of the course instance.
            token (str): Personal access token for PrairieLearn API.
        """
        self.course_code = course_code
        self.course_id = course_id
        self.students = []
        self.assessments = []

    def fetch_students(self, global_students, token):
        """Fetch all students in the course and populate the `students` list."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/gradebook"
        headers = {"Private-Token": token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            gradebook_data = response.json()

            for student in gradebook_data:

                student_id = student["user_id"]
                name = student["user_name"]
                email = student["user_uid"]

                if student_id not in global_students:
                    student_instance = Student(student_id, name, email)
                    student_instance.add_course(self)
                    global_students[student_id] = student_instance
                else:
                    student_instance = global_students[student_id]
                    student_instance.add_course(self)

                self.students.append(student_instance)

            # Print the number of students fetched
            print(f"Fetched {len(self.students)} students for course code {self.course_code}.")
        else:
            raise ValueError(f"Failed to fetch students. Status Code: {response.status_code}")

    def fetch_assessments(self, global_assessments, token):
        """Fetch all assessments in the course and populate the `assessments` list."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/assessments"
        headers = {"Private-Token": token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            assessments_data = response.json()

            for assessment in assessments_data:

                assessment_id = assessment["assessment_id"]
                assessment_name = assessment["assessment_name"]
                assessment_label = assessment["assessment_label"]

                global_assessments[assessment_id] = Assessment(assessment_id, assessment_name, assessment_label, self.course_id)
                self.assessments.append(global_assessments[assessment_id])

            # Print each assessment name on a new line
            print("Fetched assessments:")
            for assessment in self.assessments:
                print(f"- {assessment.name} (Label: {assessment.label})")
        else:
            raise ValueError(f"Failed to fetch assessments. Status Code: {response.status_code}")

    def show_student_list(self):
        """Show the list of students enrolled in the course."""
        print(f"\nThere are {len(self.students)} students in Course {self.course_code}:")

        for student in self.students:
            print(f"User ID: {student.user_id}, User Name: {student.user_name}, User UID: {student.user_uid}")

    def get_assessment_summary_statistics(self, token):
        """Compute and print summary statistics for each assessment in the course."""
        if not self.assessments:
            print("No assessments available. Please fetch assessments first.")
            return

        print("\nAssessment Summary Statistics:")
        for assessment in self.assessments:
            # Fetch submissions for the assessment
            assessment.fetch_submissions(self.course_id, token)

            # Get summary statistics using the Assessment class method
            stats = assessment.get_summary_statistics()

            print(f"\nAssessment: {assessment.name} (Label: {assessment.label})")
            print(f"  - Number of submissions: {stats['num_submissions']}")
            print(f"  - Mean score: {stats['mean_score']:.2f}%" if stats['mean_score'] is not None else "  - Mean score: N/A")
            print(f"  - Median score: {stats['median_score']:.2f}%" if stats['median_score'] is not None else "  - Median score: N/A")
            print(f"  - Max score: {stats['max_score']:.2f}%" if stats['max_score'] is not None else "  - Max score: N/A")
            print(f"  - Min score: {stats['min_score']:.2f}%" if stats['min_score'] is not None else "  - Min score: N/A")


class Assessment:
    def __init__(self, assessment_id, name, label, course_id):
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
        self.course_id = course_id
        self.submissions_fetched = False  # Tracks whether submissions have been fetched

        self.scores = []

    def fetch_submissions(self, token):
        """Fetch all submissions for this assessment."""
        url = f"https://us.prairielearn.com/pl/api/v1/course_instances/{self.course_id}/assessments/{self.assessment_id}/assessment_instances"
        headers = {"Private-Token": token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            submissions = response.json()
            self.scores = [submission.get("score_perc", 0) for submission in submissions if submission.get("score_perc") is not None]
            self.submissions_fetched = True  # Mark that submissions have been fetched
        else:
            raise ValueError(f"Failed to fetch submissions for assessment {self.name}. Status Code: {response.status_code}")

    def get_summary_statistics(self):
        """Compute summary statistics for the assessment."""

        if self.submissions_fetched == False:
            print("Please fetch submissions for this assessment first!")
            return

        if not self.scores:
            return {
                "num_submissions": 0,
                "mean_score": None,
                "median_score": None,
                "max_score": None,
                "min_score": None
            }

        return {
            "num_submissions": len(self.scores),
            "mean_score": sum(self.scores) / len(self.scores),
            "median_score": statistics.median(self.scores),
            "max_score": max(self.scores),
            "min_score": min(self.scores)
        }

    def plot_score_histogram(self):
        """Plot a histogram of the score percentages."""
        if not self.scores:
            print(f"No scores available for assessment {self.name}. Fetch submissions first.")
            return

        plt.figure(figsize=(8, 6))
        plt.hist(self.scores, bins=10, color="skyblue", edgecolor="black", alpha=0.7)
        plt.title(f"Score Distribution for {self.name} (Label: {self.label})", fontsize=14)
        plt.xlabel("Score Percentage", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()



class Student:
    def __init__(self, user_id, user_name, user_uid):
        """
        Initialize a Student instance.

        Args:
            student_id (str): ID of the student.
            name (str): Name of the student.
            email (str): Email of the student.
            grades (list): List of dictionaries containing assessment grades.
        """
        self.user_id = user_id
        self.user_name = user_name
        self.user_uid = user_uid

        self.courses = []

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
