import requests
import statistics
import altair as alt
import pandas as pd


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
