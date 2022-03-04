import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user_1 = User.objects.create_user(username='TestUser_1')
        cls.user_2 = User.objects.create_user(username='TestUser_2')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user_1,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.user_1)

        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    # Тестирование шаблонов
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': self.post.author}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Тестирование словаря контекста
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(response.context['author'], self.post.author)
        self.assertEqual(response.context['count_posts'], 1)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['count_posts'], 1)
        self.assertEqual(response.context['post'], self.post)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_1.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context['post'].id, self.post.id)

    def test_index_page_cache_delete_content(self):
        """При удалении записи из базы, кэш остаётся в response.content
        главной страницы."""
        old_content = self.authorized_client_1.get(
            reverse('posts:index')).content
        Post.objects.filter(id=self.post.id).delete()
        new_content = self.authorized_client_1.get(
            reverse('posts:index')).content
        self.assertEqual(old_content, new_content)

    def test_index_page_clear_cache_delete_content(self):
        """При удалении записи из базы, и очистки кэша, он не остается
        в response.content главной страницы."""
        old_content = self.authorized_client_1.get(
            reverse('posts:index')).content
        Post.objects.filter(id=self.post.id).delete()
        cache.clear()
        new_content = self.authorized_client_1.get(
            reverse('posts:index')).content
        self.assertNotEqual(old_content, new_content)

    def test_authorized_user_follow_other_users(self):
        """Авторизованный пользователь может подписываться на других
        пользователей."""
        count_following = Follow.objects.count()

        response = self.authorized_client_2.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.user_1.username}))
        self.assertEqual(Follow.objects.count(), count_following + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user_1.username}))

    def test_authorized_user_unfollow_other_users(self):
        """Авторизованный пользователь может отписаться от других
        пользователей."""
        Follow.objects.create(user=self.user_2, author=self.user_1)
        count_following = Follow.objects.count()

        response = self.authorized_client_2.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.user_1.username}))
        self.assertEqual(Follow.objects.count(), count_following - 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user_1.username}))

    def test_new_post_appears_feed_subscribed(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан."""
        Follow.objects.create(user=self.user_2, author=self.user_1)
        post = Post.objects.create(author=self.user_1, text='Тестовый текст')
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0], post)

    def test_new_post_appears_feed_subscribed(self):
        """Новая запись пользователя не появляется в ленте тех, кто
        не подписан."""
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        self.assertNotEqual(response.context['page_obj'], self.post)


class PaginatorViewsTest(TestCase):
    @ classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        objs = [
            Post(
                author=cls.user,
                text=f'Тестовый текст {str(i)}',
                group=cls.group
            )
            for i in range(13)
        ]

        cls.post = Post.objects.bulk_create(objs)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        count_posts_first_page = 10
        urls_context_name = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): 'page_obj',
            reverse('posts:profile',
                    kwargs={'username': self.post[0].author}): 'page_obj',
        }
        for value, expected in urls_context_name.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(
                    len(response.context[expected]), count_posts_first_page)

    def test_second_page_contains_three_records(self):
        count_posts_second_page = 3
        urls_context_name = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): 'page_obj',
            reverse('posts:profile',
                    kwargs={'username': self.post[0].author}): 'page_obj',
        }
        for value, expected in urls_context_name.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value + '?page=2')
                self.assertEqual(
                    len(response.context[expected]), count_posts_second_page)
