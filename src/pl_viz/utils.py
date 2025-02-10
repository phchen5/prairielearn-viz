from pl_api import Course

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