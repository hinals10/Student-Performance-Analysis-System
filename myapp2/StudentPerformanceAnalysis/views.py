from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import User, Course, Semester, Subject, Batch, StudentEnrollment, Assignment, AssignmentResponse, Test, TestQuestion, TestResponse
import mimetypes
import logging
import json

# Set up logging
logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'Admin':
                return redirect('admin_dashboard')
            elif user.role == 'Faculty':
                return redirect('faculty_dashboard')
            elif user.role == 'Student':
                return redirect('student_dashboard')
            elif user.role == 'Subadmin':
                return redirect('subadmin_dashboard')
            else:
                messages.error(request, 'Unknown role')
                return redirect('login')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    return render(request, 'login.html')

@login_required
def admin_dashboard(request):
    if request.user.role != 'Admin':
        return redirect('login')
    if request.method == 'POST':
        subadmin_name = request.POST.get('subadminName')
        course_id = request.POST.get('course')
        batch_name = request.POST.get('batch')
        if subadmin_name and course_id and batch_name:
            course = Course.objects.get(id=course_id)
            subadmin = User.objects.create_user(username=subadmin_name, password='subadmin123', role='Subadmin')
            Batch.objects.create(name=batch_name, course=course, subadmin=subadmin)
            messages.success(request, f'{subadmin_name} assigned to {batch_name} for {course.name}.')
            return redirect('admin_dashboard')
    courses = Course.objects.all()
    batches = Batch.objects.all()
    all_users = User.objects.filter(role__in=['Faculty', 'Student'])
    return render(request, 'admin_dashboard.html', {'courses': courses, 'batches': batches, 'all_users': all_users})

@login_required
def subadmin_dashboard(request):
    if request.user.role != 'Subadmin':
        return redirect('login')
    if request.method == 'POST':
        if 'add_student' in request.POST:
            username = request.POST['username']
            batch_id = request.POST['batch']
            semester_id = request.POST['semester']
            student = User.objects.create_user(username=username, password='student123', role='Student')
            batch = Batch.objects.get(id=batch_id)
            semester = Semester.objects.get(id=semester_id)
            StudentEnrollment.objects.create(student=student, batch=batch, semester=semester)
        elif 'assign_faculty' in request.POST:
            faculty_id = request.POST['faculty']
            subject_id = request.POST['subject']
            faculty = User.objects.get(id=faculty_id)
            subject = Subject.objects.get(id=subject_id)
            subject.faculty = faculty
            subject.save()
        elif 'add_semester' in request.POST:
            name = request.POST['name']
            course_id = request.POST['course']
            course = Course.objects.get(id=course_id)
            Semester.objects.create(name=name, course=course)
            messages.success(request, f'Semester {name} added successfully.')
            return redirect('subadmin_dashboard')
        elif 'add_subject' in request.POST:
            name = request.POST['name']
            semester_id = request.POST['semester']
            semester = Semester.objects.get(id=semester_id)
            Subject.objects.create(name=name, semester=semester)
            messages.success(request, f'Subject {name} added successfully.')
            return redirect('subadmin_dashboard')

    batches = Batch.objects.filter(subadmin=request.user)
    semesters = Semester.objects.filter(course__in=[b.course for b in batches])
    subjects = Subject.objects.filter(semester__in=semesters)
    students = StudentEnrollment.objects.filter(batch__in=batches)
    faculty = User.objects.filter(role='Faculty')
    context = {
        'batches': batches,
        'semesters': semesters,
        'subjects': subjects,
        'students': students,
        'faculty': faculty,
        'student_count': students.count(),
        'faculty_count': faculty.count(),
        'course_count': batches.values('course').distinct().count(),
    }
    return render(request, 'subadmin_dashboard.html', context)

@login_required
def faculty_dashboard(request):
    if request.user.role != 'Faculty':
        return redirect('login')
    subjects = Subject.objects.filter(faculty=request.user)
    assignments = Assignment.objects.filter(subject__in=subjects)
    tests = Test.objects.filter(subject__in=subjects)
    assignment_responses = AssignmentResponse.objects.filter(assignment__in=assignments)
    test_responses = TestResponse.objects.filter(test__in=tests)
    latest_test = None

    if request.method == 'POST':
        if 'assignmentTitle' in request.POST:
            subject = Subject.objects.get(id=request.POST['subject'])
            assignment_file = request.FILES.get('assignmentFile')
            if assignment_file:
                content_type = mimetypes.guess_type(assignment_file.name)[0]
                allowed_types = [
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ]
                if content_type not in allowed_types:
                    messages.error(request, 'Only PDF, DOC, or DOCX files are allowed.')
                    return redirect('faculty_dashboard')
                assignment = Assignment(
                    title=request.POST['assignmentTitle'],
                    subject=subject,
                    file=assignment_file
                )
                assignment.save()
            else:
                messages.error(request, 'Please upload a file.')
                return redirect('faculty_dashboard')
        elif 'create_test' in request.POST:
            subject = Subject.objects.get(id=request.POST['subject'])
            test_title = request.POST['testTitle']
            if test_title and subject:
                test = Test(title=test_title, subject=subject)
                test.save()
                logger.info(f"Created Test: {test}")
                messages.success(request, f'Test "{test.title}" created successfully. Proceed to add questions.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'test_id': test.id, 'test_title': test.title})
                else:
                    latest_test = test
            else:
                messages.error(request, 'Test title and subject are required.')
                logger.error(f'Validation failed: test_title={test_title}, subject={subject}')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Test Buttitle and subject are required.'}, status=400)
        elif 'add_question' in request.POST:
            test_id = request.POST.get('test_id')
            test = Test.objects.get(id=test_id)
            question_text = request.POST.get('question_text')
            options = [
                request.POST.get('option1'),
                request.POST.get('option2'),
                request.POST.get('option3'),
                request.POST.get('option4')
            ]
            correct_answer = request.POST.get('correct_answer')
            response_data = {'status': 'error', 'message': ''}
            if not question_text or not all(options) or not correct_answer:
                response_data['message'] = 'All fields (question and options) and a correct answer are required.'
                logger.error(f'Validation failed: question_text={question_text}, options={options}, correct_answer={correct_answer}')
            elif correct_answer not in options:
                response_data['message'] = 'Correct answer must be one of the provided options.'
                logger.error(f'Mismatch: correct_answer={correct_answer} not in options={options}')
            else:
                options_str = ','.join([opt for opt in options if opt])
                if options_str:
                    try:
                        test_question = TestQuestion(
                            test=test,
                            question_text=question_text,
                            options=options_str,
                            correct_answer=correct_answer
                        )
                        test_question.save()
                        logger.info(f"Successfully created TestQuestion: {test_question}")
                        response_data = {'status': 'success'}
                        messages.success(request, 'Question added successfully.')
                    except Exception as e:
                        response_data['message'] = f'Failed to save question: {str(e)}'
                        logger.error(f'Exception during TestQuestion save: {str(e)}')
                else:
                    response_data['message'] = 'No valid options provided.'
                    logger.error('No valid options provided for TestQuestion creation')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(response_data)
            return redirect('faculty_dashboard')

    context = {
        'subjects': subjects,
        'assignments': assignments,
        'tests': tests,
        'assignment_responses': assignment_responses,
        'test_responses': test_responses,
        'latest_test': latest_test,
        'messages': messages.get_messages(request)
    }
    return render(request, 'faculty_dashboard.html', context)

@login_required
def get_test_question_count(request, test_id):
    if request.user.role != 'Faculty':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    try:
        test = Test.objects.get(id=test_id, subject__faculty=request.user)
        count = test.questions.count()
        return JsonResponse({'status': 'success', 'count': count})
    except Test.DoesNotExist:
        return JsonResponse({'error': 'Test not found'}, status=404)

@login_required
def student_dashboard(request):
    if request.user.role != 'Student':
        return redirect('login')
    enrollment = StudentEnrollment.objects.filter(student=request.user).first()
    subjects = Subject.objects.filter(semester=enrollment.semester) if enrollment else []
    
    # Get assignments excluding those with responses
    assignments = Assignment.objects.filter(subject__in=subjects)
    submitted_assignment_ids = AssignmentResponse.objects.filter(
        student=request.user
    ).values_list('assignment_id', flat=True)
    available_assignments = assignments.exclude(id__in=submitted_assignment_ids)
    
    logger.info(f"Student: {request.user.username}, Subjects: {subjects.count()}, Total Assignments: {assignments.count()}, Available Assignments: {available_assignments.count()}")
    
    tests = Test.objects.filter(subject__in=subjects)
    test_responses = TestResponse.objects.filter(student=request.user, test__in=tests)
    test_scores = {str(response.test.id): response.score for response in test_responses}
    
    # Prepare data for charts
    test_response_data = [
        {
            'test_title': response.test.title,
            'score': response.score,
            'submitted_at': response.submitted_at.strftime('%Y-%m-%d')
        } for response in test_responses
    ]
    assignment_response_data = [
        {
            'assignment_title': response.assignment.title,
            'status': response.status,
            'submitted_at': response.submitted_at.strftime('%Y-%m-%d') if response.submitted_at else ''
        } for response in AssignmentResponse.objects.filter(student=request.user)
    ]
    
    logger.debug(f"Initial test_scores: {test_scores}, tests: {[t.id for t in tests]}")

    if request.method == 'POST':
        if 'assignment' in request.POST:
            assignment_id = request.POST['assignment']
            try:
                assignment = Assignment.objects.get(id=assignment_id)
                if 'responseFile' not in request.FILES:
                    messages.error(request, 'Please upload a response file.')
                    return redirect('student_dashboard')
                response_file = request.FILES['responseFile']
                content_type = mimetypes.guess_type(response_file.name)[0]
                allowed_types = [
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ]
                if content_type not in allowed_types:
                    messages.error(request, 'Only PDF, DOC, or DOCX files are allowed.')
                    return redirect('student_dashboard')
                response = AssignmentResponse(
                    assignment=assignment,
                    student=request.user,
                    file=response_file,
                    status='Done'  # Set status to Done
                )
                response.save()
                messages.success(request, 'Assignment response submitted successfully.')
                return redirect('student_dashboard')
            except Assignment.DoesNotExist:
                messages.error(request, 'Assignment not found.')
                logger.error(f"Assignment {assignment_id} not found.")
                return redirect('student_dashboard')
        elif 'test_id' in request.POST:
            test_id = request.POST['test_id']
            try:
                test = Test.objects.get(id=test_id)
                if TestResponse.objects.filter(student=request.user, test=test).exists():
                    messages.error(request, 'You have already submitted this test.')
                    return redirect('student_dashboard')
                answers = {f'question{q.id}': request.POST.get(f'question{q.id}') for q in test.questions.all()}
                total_questions = test.questions.count()
                correct_count = 0
                for q in test.questions.all():
                    student_answer = answers.get(f'question{q.id}')
                    is_correct = student_answer == q.correct_answer if student_answer else False
                    if is_correct:
                        correct_count += 1
                score = (correct_count / total_questions * 100) if total_questions > 0 else 0.0
                logger.debug(f"Test {test_id}: Answers={answers}, Correct={correct_count}, Total={total_questions}, Score={score}%")
                response = TestResponse.objects.create(
                    student=request.user,
                    test=test,
                    answers=answers,
                    score=score
                )
                test_scores[str(test_id)] = score
                messages.success(request, f'Test submitted successfully. Your score: {score:.2f}%')
                logger.debug(f"Updated test_scores: {test_scores}")
            except Test.DoesNotExist:
                messages.error(request, 'Test not found.')
                logger.error(f"Test {test_id} not found.")
                return redirect('student_dashboard')
            except Exception as e:
                messages.error(request, 'An error occurred while submitting the test.')
                logger.error(f"Error submitting test {test_id}: {str(e)}")
                return redirect('student_dashboard')

    context = {
        'enrollment': enrollment,
        'subjects': subjects,
        'assignments': available_assignments,
        'tests': tests,
        'test_scores': test_scores,
        'test_questions': [
            {
                'id': q.id,
                'question_text': q.question_text,
                'options': q.options.split(','),
                'correct_answer': q.correct_answer,
                'test_id': q.test.id
            } for t in tests for q in t.questions.all()
        ],
        'test_responses': test_response_data,
        'assignment_responses': assignment_response_data
    }
    logger.debug(f"Context: test_scores={test_scores}")
    return render(request, 'student_dashboard.html', context)

@login_required
def get_test_responses(request, test_id):
    if request.user.role != 'Faculty':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    try:
        test = Test.objects.get(id=test_id, subject__faculty=request.user)
        responses = TestResponse.objects.filter(test=test)
        response_data = [{
            'question': q.question_text,
            'answer': r.answers.get(f'question{q.id}', 'Not answered'),
            'score': f"{r.score:.2f}%"
        } for r in responses for q in test.questions.all()]
        return JsonResponse({'responses': response_data})
    except Test.DoesNotExist:
        return JsonResponse({'error': 'Test not found'}, status=404)