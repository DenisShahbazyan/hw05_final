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
            text='Тестовая группа',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        result_str_group = PostModelTest.group
        expected_str_group = result_str_group.title
        self.assertEqual(expected_str_group, str(result_str_group),
                         '__str__ в модели Group не возвращает title')

        result_str_post = PostModelTest.post
        expected_str_post = result_str_post.text[:15]
        self.assertEqual(expected_str_post, str(result_str_post),
                         '__str__ в модели Post не возвращает text[:15]')

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        result = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(result._meta.get_field(
                    field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        result = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(result._meta.get_field(
                    field).help_text, expected_value)
