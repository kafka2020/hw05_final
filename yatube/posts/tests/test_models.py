from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост в котором больше, чем 15 символов',
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем корректную работу __str__."""
        expected_object_name = (
            (str(self.group), self.group.title),
            (str(self.post), self.post.text[:settings.STRING_LENGTH])
        )
        for instance, expected in expected_object_name:
            with self.subTest(instance=instance):
                self.assertEqual(instance, expected)

    def test_field_verboses_for_models(self):
        """Проверяем verbose names."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected)

    def test_help_texts_for_models(self):
        """Проверяем help_text."""
        post = PostModelTest.post
        field_help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
        }
        for field, expected in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected)
