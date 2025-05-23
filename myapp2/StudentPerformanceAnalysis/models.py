from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=50, choices=[
        ('Admin', 'Admin'), ('Subadmin', 'Subadmin'), ('Faculty', 'Faculty'), ('Student', 'Student')
    ])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return f"{self.username} ({self.role})"

class Course(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Semester(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=50)
    def __str__(self):
        return f"{self.course.name} - {self.name}"

class Subject(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    faculty = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                               limit_choices_to={'role': 'Faculty'}, related_name='subjects')
    def __str__(self):
        return f"{self.name} ({self.semester})"

class Batch(models.Model):
    name = models.CharField(max_length=4)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches')
    subadmin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                limit_choices_to={'role': 'Subadmin'}, related_name='batches')
    def __str__(self):
        return f"{self.name} ({self.course.name})"

class StudentEnrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, 
                               limit_choices_to={'role': 'Student'}, related_name='enrollments')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='enrollments')
    def __str__(self):
        return f"{self.student.username} - {self.batch.name} - {self.semester.name}"

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    file = models.FileField(upload_to='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class AssignmentResponse(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'Student'}, related_name='assignment_responses')
    file = models.FileField(upload_to='responses/')
    status = models.CharField(max_length=50, default='Pending')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

class Test(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='tests', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    options = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=100)

    def __str__(self):
        return self.question_text

class TestResponse(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'Student'}, related_name='test_responses')
    answers = models.JSONField(default=dict)
    score = models.FloatField(default=0.0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.test.title}"