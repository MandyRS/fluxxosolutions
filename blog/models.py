from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Post(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    conteudo = models.TextField()
    imagem = models.ImageField(upload_to='posts/imagens/', blank=True, null=True)
    arquivo = models.FileField(upload_to='posts/arquivos/', blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    data_publicacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.slug])
