import re
from django.core.management.base import BaseCommand
from icecream import ic

from exam.models import Level, Question, Answer
from docx import Document


class Command(BaseCommand):
    help = 'Parse Word doc and create Level, Questions, and Answers'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the .docx Word file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        doc = Document(file_path)
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        level = Level.objects.filter(name__icontains='B1').first()

        question_number = 1
        i = 1  # Start after the level name
        while i < len(lines):
            line = lines[i]
            q_match = re.match(rf"^{question_number}\.\s*(.*)", line)

            if q_match:
                question_text_lines = [q_match.group(1)]
                ic(question_text_lines)
                i += 1
                # Read any continuation lines for the question
                while i < len(lines) and not re.match(r"^[\*\s]?[a-dA-D]\)", lines[i]):
                    question_text_lines.append(lines[i])
                    ic(lines[i])
                    i += 1

                question_text = ' '.join(question_text_lines).strip()
                ic(question_text)
                question = Question.objects.create(name=question_text, level=level)

                # Read answers
                while i < len(lines) and re.match(r"^[\*\s]?[a-dA-D]\)", lines[i]):
                    ans_line = lines[i]
                    is_correct = ans_line.startswith("*")
                    ans_text = re.sub(r"^[\*\s]?([a-dA-D])\)\s*", "", ans_line).strip()
                    Answer.objects.create(question=question, name=ans_text, is_correct=is_correct)
                    i += 1

                question_number += 1
            else:
                i += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully parsed level "{level.name}" with {question_number - 1} questions.'))
