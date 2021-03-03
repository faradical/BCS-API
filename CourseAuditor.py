import SethsBCS as sb
import datetime
import getpass
import os

script_path = os.path.realpath(__file__)
parent = os.path.abspath(os.path.join(script_path, os.pardir))

email = input("Enter Email: ")
password = getpass.getpass("Enter Password: ")

myBCS = sb.myBCS(email, password)

print("Select a course to audit from the list below by inputting the courseID:")
print()

for c in myBCS.enrollmentsList:
	print(f"course_id: {c['course_id']}")
	print(f"program_name: {c['program_name']}")
	print(f"course_code: {c['course_code']}")
	print(f"Duration: {c['start_date'].split('T')[0]} - {c['end_date'].split('T')[0]}")
	print()

ID = input("Course ID: ")

cohort = myBCS.courseByID[ID]

name = cohort.enrollmentInfo['course']['code']

today = datetime.datetime.today().strftime('%m-%d-%Y')

filename = os.path.join(parent, f"{name}_gradebook_{today}.csv")

cohort.gradebook().to_csv(filename)