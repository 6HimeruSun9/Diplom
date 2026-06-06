from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import Section, Lesson, Question, AnswerOption, TextAnswer, OrderAnswer, TestResult
from .forms import UserRegistrationForm

def index(request):
    sections = Section.objects.all()
    sections_with_progress = []
    
    for section in sections:
        progress = 0 
        if request.user.is_authenticated:
            progress = section.get_progress(request.user)
        
        sections_with_progress.append({
            'section': section,
            'progress': progress,
            'lessons_count': section.lessons.count()
        })
    
    return render(request, 'lessons/index.html', {'sections_with_progress': sections_with_progress})

def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'lessons/lesson_detail.html', {'lesson': lesson})

@login_required
def test_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    questions = lesson.questions.all().order_by('order')
    
    if not questions:
        messages.warning(request, 'Для этого урока пока нет вопросов.')
        return redirect('lesson_detail', lesson_id=lesson_id)
    
    questions_data = []
    for q in questions:
        q_data = {
            'id': q.id,
            'text': q.text,
            'type': q.question_type,
            'points': q.points,
        }
        if q.question_type == 'choice':
            q_data['options'] = list(q.answer_options.values('id', 'text'))
        elif q.question_type == 'order':
            if hasattr(q, 'order_answer'):
                words = q.order_answer.get_order_list()
                import random
                shuffled = random.sample(words, len(words))
                q_data['words'] = shuffled
                q_data['correct_order'] = q.order_answer.correct_order
        questions_data.append(q_data)
    
    return render(request, 'lessons/test.html', {
        'lesson': lesson,
        'questions': questions_data,
        'questions_json': json.dumps(questions_data, ensure_ascii=False)
    })

@login_required
@require_http_methods(['POST'])
def submit_test(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    try:
        data = json.loads(request.body)
        user_answers = data.get('answers', {})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    questions = lesson.questions.all()
    total_points = sum(q.points for q in questions)
    earned_points = 0
    
    for q in questions:
        user_answer = user_answers.get(str(q.id))
        if not user_answer:
            continue
            
        if q.question_type == 'choice':
            try:
                answer_id = int(user_answer)
                correct_option = q.answer_options.filter(is_correct=True).first()
                if correct_option and answer_id == correct_option.id:
                    earned_points += q.points
            except (ValueError, TypeError):
                pass
                
        elif q.question_type == 'text':
            correct_answer = TextAnswer.objects.get(question=q)
            user_text = user_answer.strip().lower() if isinstance(user_answer, str) else ''
            correct_text = correct_answer.correct_text
            if not correct_answer.case_sensitive:
                correct_text = correct_text.lower()
            if user_text == correct_text:
                earned_points += q.points
                
        elif q.question_type == 'order':
            correct_answer = OrderAnswer.objects.get(question=q)
            correct_list = correct_answer.get_order_list()
            if isinstance(user_answer, list) and user_answer == correct_list:
                earned_points += q.points
    
    score = int(earned_points / total_points * 100) if total_points > 0 else 0
    is_passed = score >= 70
    
    TestResult.objects.create(
        user=request.user,
        lesson=lesson,
        score=score,
        is_passed=is_passed,
        answers_json=user_answers
    )
    
    return JsonResponse({
        'score': score,
        'is_passed': is_passed,
        'total_questions': questions.count(),
        'correct_answers': earned_points
    })

@login_required
def profile(request):
    test_results = TestResult.objects.filter(user=request.user).select_related('lesson')
    total_lessons = test_results.count()
    avg_score = 0
    if test_results:
        total_score = sum(r.score for r in test_results)
        avg_score = int(total_score / len(test_results))
    passed_lessons = test_results.filter(is_passed=True).count()
    
    sections_progress = []
    for section in Section.objects.all():
        lessons_in_section = section.lessons.all()
        if lessons_in_section:
            completed = sum(1 for lesson in lessons_in_section if lesson.is_completed_by(request.user))
            progress = int(completed / len(lessons_in_section) * 100)
        else:
            completed = 0
            progress = 0
        sections_progress.append({
            'section': section,
            'progress': progress,
            'completed': completed,
            'total': lessons_in_section.count()
        })
    
    return render(request, 'lessons/profile.html', {
        'test_results': test_results,
        'total_lessons': total_lessons,
        'avg_score': avg_score,
        'passed_lessons': passed_lessons,
        'sections_progress': sections_progress,
    })

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно')
            return redirect('index')
    else:
        form = UserRegistrationForm()
    return render(request, 'lessons/auth/register.html', {'form': form})
def section_detail(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    lessons = section.lessons.all().order_by('order')
    return render(request, 'lessons/section_detail.html', {'section': section, 'lessons': lessons})