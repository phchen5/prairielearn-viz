from prairielearn_classes import Course, Assessment, Student

def fetch_data(course_ids, token):

    global_students = {}
    global_courses = {}
    global_assessments = {}

    for course_code, course_id in course_ids.items():

        course = Course(course_code, course_id)
        global_courses[course_id] = course

        course.fetch_students(global_students, token)
        course.fetch_assessments(global_assessments, token)
    
    return global_courses, global_assessments, global_students

