'''
---------------------------------------------------------------------------------------------------------------------
Name:			SethsBCS.py

Version:		1.0

Author:			Seth Pruitt

Usage:			import SethsBCS

Description:	Contains classes and functions for building applications to rapidly connect to perform administrative
				duties on BootCampSpot.

Comments:		10-10-20 Began writing script
--------
'''


# ~~~~~~~~~~~~~~~~ DEPENDENCIES


import requests, json, re
import pandas as pd


# ~~~~~~~~~~~~~~~~ FUNCTIONS DEFINITIONS


def BCSAPIlogin(email, password):
	s = requests.Session()
	cred = json.dumps({"email": email, "password": password})
	url_base = "https://bootcampspot.com/api/instructor/v1"
	response = s.post(url_base + "/login", data=cred)
	if response.status_code == 200:
		if response.json()['success'] == True:
			token = response.json()['authenticationInfo']['authToken']
			s.headers.update({"Content-Type": "application/json", "authToken": token})

			return s

		else:
			token = False
			print("Login Failed")
	else:
		token = False
		print(f"Login request failed with exit code {response.status_code}")

def brokerLogin(email, password):
	b = requests.Session()
	broker_base_url = "https://bootcampspot.com/broker"
	cred = json.dumps({"email": email, "password": password})
	response = b.post(broker_base_url + "/login", data=cred)

	if response.status_code == 200:
		if response.json()['active'] == True:
			token = response.json()['authToken']
			b.headers.update({"Content-Type": "application/json", "authToken": token})

			return b

		else:
			token = False
			print("Login Failed")
	else:
		token = False
		print(f"Request failed with exit code {response.status_code}")


def MyBCSconstructor(email, password):

	s = BCSAPIlogin(email, password)

	url_base = "https://bootcampspot.com/api/instructor/v1"
	response = s.get(url_base + "/me")
	if response.status_code == 200:
		response = response.json()
		return response
	else:
		print(f"Request failed with exit code {response.status_code}")
	
def enrolInfo(course):
	enrollment_id = course['id']
	course_id = course['courseId']
	status = course['active']
	cohortId = course['course']['cohortId']
	course_code = course['course']['code']
	start_date = course['course']['startDate']
	end_date = course['course']['endDate']
	program_name = course['course']['cohort']['program']['name']
	program_type = course['course']['cohort']['program']['programType']['name']
	university = course['course']['cohort']['program']['university']['name']
	course_role = course['courseRole']['name']
	return({"enrollment_id": enrollment_id,
			"course_id": course_id,
			"status": status,
			"cohortId": cohortId,
			"course_code": course_code,
			"start_date": start_date,
			"end_date": end_date,
			"program_name": program_name,
			"program_type": program_type,
			"university": university,
			"course_role": course_role})

def cohortConstructor(email, password, enrollmentID):

	s = BCSAPIlogin(email, password)

	url_base = "https://bootcampspot.com/api/instructor/v1"
	data = json.dumps({"enrollmentId": enrollmentID})
	response = s.post(url_base + "/assignments", data=data)

	if response.status_code == 200:
		asses = response.json()['calendarAssignments']
		assignments = [{"id": ass['id'], "assignment": ass['title']} for ass in asses]

		data = json.dumps({"assignmentId": asses[0]['id']})
		response = s.post(url_base + "/assignmentDetail", data=data)

		if response.status_code == 200:
			students1 = response.json()['students']
			students = []
			for student in students1:
				students.append({"id": student['student']['id'],
				"Name": f"{student['student']['firstName']} {student['student']['lastName']}",
				"email": student['student']['email']})
			
		else:
			print(f"Students retrieval request failed with exit code {response.status_code}")
			students = ""

	else:
		print(f"Assignments retrieval request failed with exit code {response.status_code}")
		assignments = ""
		students = ""


	return {"studentsList": students, "assignments": assignments}


def getGrades(email, password, courseID, selected_student=""):    

	s = BCSAPIlogin(email, password)

	url_base = "https://bootcampspot.com/api/instructor/v1"
	data = json.dumps({"courseId": courseID})
	response = s.post(url_base + "/grades", data=data)

	if response.status_code == 200:

		grades = response.json()

		gradebook = pd.DataFrame(grades)
		gradebook = gradebook.rename(columns={'assignmentTitle': 'ASSIGNMENT','studentName':'STUDENT','submitted':'SUBMISSION STATUS','grade':'GRADE'})

		students = list(gradebook['STUDENT'].unique())

		assignments = list(gradebook['ASSIGNMENT'].unique())
		assignments = [ass for ass in assignments if "Prework" not in ass and "Milestone" not in ass and "Career Services" not in ass]

		def SortFunc(ass):
			if "Project" in ass:
				return 1000
			else:
				return int(ass.split(".")[0])

		assignments.sort(key=SortFunc)

		grades_dict = {"Student": []}
		for ass in assignments:
			grades_dict[ass] = []

		for student in students:
			grades_dict['Student'].append(student) #.replace("\xa0"," "))
			for assignment in assignments:
				student_gradebook = gradebook[gradebook['STUDENT'] == student]
				sub_status = student_gradebook[student_gradebook['ASSIGNMENT'] == assignment]['SUBMISSION STATUS'].values[0]
				grade = student_gradebook[student_gradebook['ASSIGNMENT'] == assignment]['GRADE'].values[0]
				if grade != 'None':
					grade = student_gradebook[student_gradebook['ASSIGNMENT'] == assignment]['GRADE'].values[0]
				else:
					grade = "Not Submitted"
				grades_dict[assignment].append(grade)

		gradesDF = pd.DataFrame(grades_dict).set_index('Student')

	else:
		print(f"Grades retrieval request failed with exit code {response.status_code}")
		gradesDF = ""

	if selected_student == "":
		return gradesDF
	else:
		return gradesDF.loc[selected_student]


def getSubID(email, password, student_id, ass_id):
	s = BCSAPIlogin(email, password)

	cred = json.dumps({"assignmentId": ass_id})
	url_base = "https://bootcampspot.com/api/instructor/v1"
	response = s.post(url_base + "/assignmentDetail", data=cred)

	students = response.json()['students']
	ass_details = [stu for stu in students if stu['student']['id'] == student_id][0]
	sub_id = ass_details['submission']['id']

	return sub_id


def updateGrade(assignment, grade):
	r = assignment.summary()
	subGradeID = r['subGradeID']
	subID = r['subID']

	b = brokerLogin(assignment.myEmail, assignment.myPassword)
	broker_base_url = "https://bootcampspot.com/broker"

	if subGradeID != "" and subID != "":
		data = json.dumps({"id": subGradeID, "submissionId": subID, "grade": grade})
		response = b.post(broker_base_url + "/updateSubmissionGrade", data=data)
		
		if response.status_code != 200:
			print("Unable to update grade.")
	
	elif subGradeID == "" and subID != "":
		data = json.dumps({"id": None, "submissionId": subID, "grade": grade})
		response = b.post(broker_base_url + "/createSubmissionGrade", data=data)
		
		if response.status_code != 200:
			print("Unable to update grade.")

	elif subGradeID == "" and subID == "":
		subID = getSubID(assignment.myEmail, assignment.myPassword, assignment.studentID, assignment.assignmentID)
		if subID != "":
			data = json.dumps({"id": None, "submissionId": subID, "grade": grade})
			response = b.post(broker_base_url + "/createSubmissionGrade", data=data)
			
			if response.status_code != 200:
				print("Unable to update grade.")

		else:
			print("Unable to update grade.")

	else:
		print("Unable to update grade.")

	return assignment.summary()


def convertGrade(grade):
	if 1 < grade <= 100:
		if grade >= 97:
			grade = "A+"
		elif grade >= 93:
			grade = "A"
		elif grade >= 90:
			grade = "A-"
		elif grade >= 87:
			grade = "B+"
		elif grade >= 83:
			grade = "B"
		elif grade >= 80:
			grade = "B-"
		elif grade >= 77:
			grade = "C+"
		elif grade >= 73:
			grade = "C"
		elif grade >= 70:
			grade = "C-"
		elif grade >= 67:
			grade = "D+"
		elif grade >= 63:
			grade = "D"
		elif grade >= 60:
			grade = "D-"
		else:
			grade = "F"

	return grade


# ~~~~~~~~~~~~~~~~ CLASS DEFINITIONS


class student:
	def __init__(self, student, email, password, courseID, assignments):

		self.name = student['Name']
		self.id = student['id']
		self.email = student['email']
		self.myEmail = email
		self.myPassword = password
		self.courseID = courseID
		self.assignmentsList = {}
		for ass in assignments:
			self.assignmentsList[ass["assignment"]] = ass["id"]
		self.assignment = {}
		for ass in assignments:
			self.assignment[ass["assignment"]] = assignment(ass["id"], self.id, self.myEmail, self.myPassword)

	def grades(self):
		return getGrades(self.myEmail, self.myPassword, self.courseID, self.name)

	def help(self):
		print()
		print("Student class attributes:")
		print()
		print("\t1) student().name")
		print("\t\t")
		print()
		print("\t2) Student().email")
		print("\t\t")
		print()
		print("\t3) Student().studentID")
		print("\t\t")
		print()
		print("\t4) Student().assignment")
		print("\t\t")
		print()
		print("Student class Methods:")
		print()
		print("\t1) student().grades()")
		print("\t\t")
		print()


class assignment:
	def __init__(self, assignmentID, studentID, myEmail, myPassword):
		self.assignmentID = assignmentID
		self.studentID = studentID
		self.myEmail = myEmail
		self.myPassword = myPassword

	def summary(self):
		b = brokerLogin(self.myEmail, self.myPassword)

		data = json.dumps({"assignmentId": self.assignmentID, "studentId": self.studentID})
		broker_base_url = "https://bootcampspot.com/broker"
		response = b.post(broker_base_url + "/grade", data=data)

		if response.status_code == 200:
			sub = response.json()

			try:
				assignmentDate = sub['assignment']['assignmentDate']
			except:
				assignmentDate = ""
			try:
				dueDate = sub['assignment']['dueDate']
			except:
				dueDate = ""
			try:
				content = sub['assignment']['assignmentContent']['content']
			except:
				content = ""
			try:
				subGradeID = sub['submission']['submissionGrade']['id']
			except:
				subGradeID = ""
			try:
				subID = sub['submission']['submissionGrade']['submissionId']
			except:
				subID = ""
			try:
				submissionDate = sub['submission']['submissionGrade']['date']
			except:
				submissionDate = ""
			try:
				grade = sub['submission']['submissionGrade']['grade']
			except:
				grade = ""
			try:
				submissionURLs = [i['url'] for i in sub['submission']['submissionUrlList']]
			except:
				submissionURLs = []

			r = {'Assignment Date': assignmentDate,
				 'Due Date': dueDate,
				 'Content': content,
				 'subGradeID': subGradeID,
				 'subID': subID,
				 'Submission Date': submissionDate,
				 'Grade': grade,
				 'Submissions': submissionURLs}

		else:
			print(f"Assignment summary retrieval request failed with exit code {response.status_code}")
			r = ""

		return r

	def updateGrade(self, grade):

		if isinstance(grade, int):
			grade = convertGrade(float(grade))

		if isinstance(grade, float):
			grade = convertGrade(grade)

		if isinstance(grade, str):
			re_str = re.compile(r'[A-F]')
			re_str2 = re.compile(r'[A-F][+-]')
			grade = grade.upper()
		
		if grade.isdigit():
			grade = float(grade)
			grade = convertGrade(grade)

		if (re_str.search(grade) and len(grade) <= 1) or (re_str2.search(grade) and len(grade) <= 2):
			
			# Update Grade
			return updateGrade(self, grade)

		else:
			print("Please enter grades in either numerical percent format (i.e. 70,80,90,100) or +/- letter grade format (i.e 'C-','B','A+')")

	def addComment(self, comment):
		print("Coming soon!")
		# b = brokerLogin(self.myEmail, self.myPassword)

		# r = assignment.summary()
		# subGradeID = r['subGradeID']
		# subID = r['subID']

		# data = {"id": None, "submissionId": , "enrollmentId": , "comment": comment}
		# broker_base_url = "https://bootcampspot.com/broker"
		# response = b.post(broker_base_url + "/createSubmissionComment", data=data)


	def help(self):
		print()
		print("Assignment class attributes:")
		print()
		print("\t1) .assignmentID")
		print("\t\t")
		print()
		print("\t2) .studentID")
		print("\t\t")
		print()
		print("Assignment class Methods:")
		print()
		print("\t1) .summary()")
		print("\t\tReturns a dict displaying a summary of the assignment and any student submissions.")
		print()
		print("\t2) .updateGrade(<grade>)")
		print("\t\tUpdates the assignment grade. Accepts grades in either numerical percent format (i.e. 70,80,90,100) or +/- letter grade format (i.e 'C-','B','A+'). Returns a assignment().summary() dict with the updated grade.")
		print()
		print("\t3) .addComment(<comment>)")
		print("\t\tStill experimental.")
		print()


class cohort:
	def __init__(self, course, email, password):

		self.courseID = course['courseId']
		self.enrollmentID = course['id']

		cohort = cohortConstructor(email, password, self.enrollmentID)

		self.email = email
		self.password = password
		self.enrollmentInfo = course
		self.studentsList = cohort["studentsList"]
		self.assignmentsList = cohort["assignments"]
		self.student = {}
		for stu in self.studentsList:
			self.student[stu["Name"]] = student(stu, self.email, self.password, course['courseId'], self.assignmentsList)

	def gradebook(self):
		return getGrades(self.email, self.password, self.courseID)

	def help(self):
		print()
		print("Cohort class attributes:")
		print()
		print("\t1) cohort().student")
		print("\t\t")
		print("\t\tSyntax: cohort().student[Student Name]")
		print()
		print("\t2) cohort().enrollmentInfo")
		print("\t\t")
		print()
		print("\t3) cohort().studentsList")
		print("\t\t")
		print()
		print("\t4) cohort().assignmentsList")
		print("\t\t")
		print()
		print("Cohort class methods:")
		print()
		print("\t1) cohort().gradebook()")
		print("\t\t")


class myBCS:
	def __init__(self, email, password):

		myInfo = MyBCSconstructor(email, password)

		self.email = email
		self.password = password
		self.firstName = myInfo['userInfo']['firstName']
		self.lastName = myInfo['userInfo']['lastName']
		self.enrollmentsList = [enrolInfo(course) for course in myInfo['Enrollments']]
		self.enrollmentsListVerbose = myInfo['Enrollments']
		self.courseByID = {}

		for course in self.enrollmentsListVerbose:
			if course['courseRole']['courseRoleCode'] != "student":
				self.courseByID[str(course['courseId'])] = cohort(course, email, password)

	def help(self):
		print()
		print("MyBCS class attributes:")
		print()
		print("\t1) myBCS().email")
		print("\t\tThe email used in the creation of the myBCS object.")
		print()
		print("\t2) myBCS().firstName")
		print("\t\tThe first name associated with the email used in the creation of the myBCS object.")
		print()
		print("\t3) myBCS().lastName")
		print("\t\tThe last name associated with the email used in the creation of the myBCS object.")
		print()
		print("\t6) myBCS().courseByID")
		print("\t\tA dict object that allows you to select child cohort objects by using the course IDs as keys.")
		print("\t\tSyntax: myBCS().courseByID[course ID]")
		print()
		print("\t4) myBCS().enrollmentsList")
		print("\t\tDisplays a list of dictionaries for all the cohorts associated with the email with the following:")
		print("\t\t\t-enrollment_id")
		print("\t\t\t-course_id")
		print("\t\t\t-status")
		print("\t\t\t-cohortId")
		print("\t\t\t-course_code")
		print("\t\t\t-start_date")
		print("\t\t\t-end_date")
		print("\t\t\t-program_name")
		print("\t\t\t-program_type")
		print("\t\t\t-university")
		print("\t\t\t-course_role")
		print()
		print("\t5) myBCS().enrollmentsListVerbose")
		print("\t\tDisplays a list of dictionaries for all the cohorts associated with the email with verbose output")
