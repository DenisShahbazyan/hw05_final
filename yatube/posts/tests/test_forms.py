import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_authorized_user(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
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
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'author': self.user.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        test_data = {
            form_data['text']: PostCreateFormTests.post.text,
            form_data['group']: PostCreateFormTests.post.group.id,
            form_data['author']: PostCreateFormTests.post.author.id,
        }
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.post.author}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        for f_data, fixture_data in test_data.items():
            with self.subTest(f_data=f_data):
                self.assertEqual(f_data, fixture_data)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=form_data['author'],
                group=form_data['group'],
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post_authorized_user(self):
        """Валидная форма редактирует запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text + ' немного нового.',
            'group': self.group.id,
            'author': self.user.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), post_count)

    def test_create_post_unauthorized_user(self):
        """Неавторизованный пользователь не создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse('posts:post_create'))
        self.assertEqual(Post.objects.count(), post_count)


class CommentFormFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment_authorized_user(self):
        """Валидная форма создает запись в Comment."""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'text': self.comment.text,
            'author': self.user,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        test_data = {
            form_data['post']: CommentFormFormTests.post,
            form_data['text']: CommentFormFormTests.comment.text,
            form_data['author']: CommentFormFormTests.user,
        }

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)

        for f_data, fixture_data in test_data.items():
            with self.subTest(f_data=f_data):
                self.assertEqual(f_data, fixture_data)

        self.assertTrue(
            Comment.objects.filter(
                post=form_data['post'],
                text=form_data['text'],
                author=form_data['author'],
            ).exists()
        )

    def test_create_comment_unauthorized_user(self):
        """Неавторизованный пользователь не создает запись в Comment."""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'text': self.comment.text,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse('posts:add_comment', kwargs={
                'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count)
