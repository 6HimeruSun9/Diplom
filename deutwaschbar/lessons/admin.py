from django.contrib import admin
from .models import Section, Lesson, Question, AnswerOption, TextAnswer, OrderAnswer, TestResult

class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 3

class TextAnswerInline(admin.StackedInline):
    model = TextAnswer
    can_delete = False

class OrderAnswerInline(admin.StackedInline):
    model = OrderAnswer
    can_delete = False

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'lesson', 'text_preview', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'lesson__section']
    search_fields = ['text']
    list_editable = ['points', 'order']
    
    def get_inlines(self, request, obj=None):
        if obj:
            if obj.question_type == 'choice':
                return [AnswerOptionInline]
            elif obj.question_type == 'text':
                return [TextAnswerInline]
            elif obj.question_type == 'order':
                return [OrderAnswerInline]
        return []
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Вопрос'

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'lessons_count']
    list_editable = ['order']
    
    def lessons_count(self, obj):
        return obj.lessons.count()
    lessons_count.short_description = 'Уроков'

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'order', 'questions_count']
    list_filter = ['section']
    list_editable = ['order']
    
    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'Вопросов'

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'score', 'is_passed', 'created_at']
    list_filter = ['is_passed', 'created_at']