# prairielearn-viz

`pl_viz` is a Python package designed to simplify data extraction and visualization for courses on PrairieLearn. With its object-oriented design, `pl_viz` makes it easy to fetch data for courses, students, and assessments, and generate insightful visualizations to analyze student performance and assessment outcomes.

## Features
- **Object-Oriented Design**: Includes Course, Student, and Assessment classes for modular and intuitive data handling.
- **Data Extraction**: Fetch student lists, assessment details, and submission scores directly from the PrairieLearn API.
- **Data Visualization**:
    - Boxplots for score distributions across assessments.
    - Histograms to analyze score frequency.
- **Summary Statistics**: Compute mean, median, min, and max scores for assessments.

## Installation

To install the pl_viz package, use the following command:

```python
pip install pl_viz
```

## Usage

You will need a PrairieLearn API token to use this package. Store the token as an environment variable for security:

```bash
export PL_API_TOKEN="your_api_token_here"
```

## Classes Overview

1. `Course`

Represents a PrairieLearn course. Use it to:

- Fetch students and assessments.
- Display summary statistics.
- Generate visualizations.

2. `Student`

Represents an individual student, providing access to their user ID, name, and UID.

3. `Assessment`

Represents an assessment within a course. Fetch submissions and analyze score distributions.

## Contributing

Contributions are welcome! If you’d like to contribute to `pl_viz`, please open an issue or submit a pull request. Ensure you follow the coding standards and add tests for new features.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

