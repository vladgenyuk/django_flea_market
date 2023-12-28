import mptt
import datetime

from mptt.models import MPTTModel, TreeForeignKey
from pytils.translit import slugify

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(blank=False, null=False, verbose_name='фото')

    def last_seen(self):
        return cache.get('seen_%s' % self.user)

    def online(self):
        if self.last_seen():
            now = datetime.datetime.now()
            if now > self.last_seen() + datetime.timedelta(
                         seconds=settings.USER_ONLINE_TIMEOUT):
                return False
            else:
                return True
        else:
            return False

    def __str__(self):
        return f'{self.user}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Category(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категория'
        ordering = ['id']

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse('category', kwargs={'Category_id': self.id})


mptt.register(Category, order_insertion_by=['name'])


class Product(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название')
    author = models.ForeignKey(User, blank=True, null=True, default=None, on_delete=models.PROTECT)
    text = models.TextField(verbose_name='Описание')
    cost = models.PositiveIntegerField(default=None, verbose_name='Стоимость', blank=False, )
    photo = models.FileField(blank=True, verbose_name='Главное фото')
    slug = models.SlugField(max_length=255, unique=False, db_index=True, verbose_name='URL')
    condition = models.BooleanField(default=True)
    cat = models.ForeignKey('Category',  verbose_name='Категория', on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True, auto_now=False, null=True)

    def __str__(self):
        return f'{self.title}'

    def get_absolute_url(self):
        return reverse('product', kwargs={'pk': self.id, })

    class Meta:
        verbose_name = 'Products'
        verbose_name_plural = 'Products'
        ordering = ['id']

    def save(self, *args, **kwargs): # new
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)


class PostImage(models.Model):
    post = models.ForeignKey('Product', default=None, on_delete=models.CASCADE, related_name='postimages')
    image = models.ImageField()

    def __str__(self):
        return self.post.title


class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    members = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return f"{self.id}"


class Messages(models.Model):
    id = models.AutoField(primary_key=True)
    chat = models.ForeignKey(Chat, null=True, blank=True, on_delete=models.PROTECT)
    author = models.ForeignKey(User, default=1, on_delete=models.PROTECT)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True, auto_now=False, null=True)

    def __str__(self):
        return self.text



