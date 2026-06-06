from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Section(models.Model):
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    order = models.IntegerField('Порядок', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'
        ordering = ['order']

    def __str__(self):
        return self.name

    def get_progress(self, user):
        if not user.is_authenticated:
            return 0
        lessons = self.lessons.all()
        if not lessons:
            return 0
        from .models import TestResult
        completed = 0
        for lesson in lessons:
            if TestResult.objects.filter(user=user, lesson=lesson, is_passed=True).exists():
                completed += 1
        return int(completed / len(lessons) * 100)

class Lesson(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons', verbose_name='Раздел')
    title = models.CharField('Название', max_length=200)
    theory = models.TextField('Теоретический материал')
    order = models.IntegerField('Порядок', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']

    def __str__(self):
        return self.title

    def is_completed_by(self, user):
        if not user.is_authenticated:
            return False
        from .models import TestResult
        return TestResult.objects.filter(user=user, lesson=self, is_passed=True).exists()

class Question(models.Model):
    QUESTION_TYPES = [
        ('choice', 'Выбор варианта'),
        ('text', 'Ввод слова'),
        ('order', 'Порядок слов'),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions', verbose_name='Урок')
    text = models.TextField('Текст вопроса')
    question_type = models.CharField('Тип вопроса', max_length=10, choices=QUESTION_TYPES, default='choice')
    points = models.IntegerField('Баллы', default=1)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['order']

    def __str__(self):
        return f'{self.lesson.title}: {self.text[:50]}'

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer_options', verbose_name='Вопрос')
    text = models.CharField('Текст варианта', max_length=500)
    is_correct = models.BooleanField('Правильный', default=False)

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'

    def __str__(self):
        return self.text

class TextAnswer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='text_answer', verbose_name='Вопрос')
    correct_text = models.CharField('Правильный ответ', max_length=500)
    case_sensitive = models.BooleanField('Учитывать регистр', default=False)

    class Meta:
        verbose_name = 'Текстовый ответ'
        verbose_name_plural = 'Текстовые ответы'

    def __str__(self):
        return self.correct_text

class OrderAnswer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='order_answer', verbose_name='Вопрос')
    correct_order = models.CharField('Правильный порядок (через запятую)', max_length=500)

    class Meta:
        verbose_name = 'Ответ с порядком слов'
        verbose_name_plural = 'Ответы с порядком слов'

    def __str__(self):
        return self.correct_order

    def get_order_list(self):
        return [word.strip() for word in self.correct_order.split(',')]

class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_results', verbose_name='Пользователь')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='test_results', verbose_name='Урок')
    score = models.IntegerField('Результат (%)', validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_passed = models.BooleanField('Пройден', default=False)
    answers_json = models.JSONField('Ответы пользователя', default=dict, blank=True)
    created_at = models.DateTimeField('Дата прохождения', auto_now_add=True)

    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.lesson.title} - {self.score}%'