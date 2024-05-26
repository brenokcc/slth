
# Tutorial

In this tutorial, you will develop an application equivalent to the one described at https://docs.djangoproject.com/en/5.0/intro/tutorial01/.

## Create models

Open backend/api/models.py and edit it as bellow.

```
from slth.db import models


class Question(models.Model):

    class Meta:
        verbose_name = "Enquete"
        verbose_name_plural = "Enquetes"

    text = models.CharField(verbose_name="Texto", max_length=200)
    pub_date = models.DateTimeField(verbose_name="Data de Publicação")

    def __str__(self):
        return self.text


class Choice(models.Model):

    class Meta:
        verbose_name = "Opção"
        verbose_name_plural = "Opções"

    question = models.ForeignKey(Question, verbose_name="Enquete", on_delete=models.CASCADE)
    text = models.CharField(verbose_name="Texto", max_length=200)
    votes = models.IntegerField(verbose_name="Número de Votos", default=0)

    def __str__(self):
        return self.text
    
```

## Create endpoints

Open backend/api/endpoints.py and edit it as bellow.

```
from slth import endpoints
from .models import Question

class Questions(endpoints.AdminEndpoint[Question]):
    pass

```

Afterwards, access http://localhost:8000/app/questions/. At this point, you are already
able to create, edit, view and delete questions.

*IMPORTANT*: The AdminEndpoint is a special endpoint to easy the creation of CRUD endpoints of a model.

At this point, five endpoints have been created by the frameword:

- Questions
- AddQuestion
- EditQuestion
- ViewQuestion
- DeleteQuestion

Depending of configured language, the prefix differs. For example, in PT-BR, these endpoints would be:

- Questions
- CadastrarQuestion
- EditarQuestion
- VisualizarQuestion
- ExcluirQuestion


## Customize the listing page

Open backend/api/models.py again and edit it as bellow.

```
class QuestionQuerySet(models.QuerySet):
    def all(self):
        return self.search('text').filters('pub_date').fields('text')


class Question(models.Model):
    objects = QuestionQuerySet()

```

Then, access http://localhost:8000/app/questions/ again and see what changed.
By editing four lines of code, you could configure how questions are displayed in the listing page.

## Customize the add form

Open backend/api/models.py again and add the method bellow to the Question model.

```
def formfactory(self):
    return (
        super().formfactory()
        .info('Cadastre uma enquete preenchendo os campos abaixo')
        .fieldset('Dados Gerais', fields=(('text','pub_date'),))
    )
```

Observe that a message is displayed to the user, the fields are in front of the other and grouped in a fieldset.
Separate the fields in two fieldsets by replacing the code above with the follwing one.

```
def formfactory(self):
    return (
        super().formfactory()
        .info('Cadastre uma enquete preenchendo os campos abaixo')
        .fieldset('Dados Gerais', fields=(('text'),))
        .fieldset('Publicação', fields=(('pub_date'),))
    )
```

## Customize the edit form

Supposing that the user cannot change a the publication date of a question, you can make the following changes in
the formfactory() method of Question model.

```
def formfactory(self):
    return (
        super().formfactory()
        .info('Cadastre uma enquete preenchendo os campos abaixo')
        .fieldset('Dados Gerais', fields=(('text'),))
        .fieldset('Publicação', fields=(('pub_date'),))
    ) if self.pk is None else (
        super().formfactory().fieldset('Dados Gerais', fields=(('text'),))
    )
```

## Customize the visualization page

To customize how data is displayed, implement the method serializer() in the Question model as bellow.

```
def serializer(self):
    return (
        super().serializer()
        .fieldset('Dados Gerais', fields=('id', 'text',))
        .fieldset('Publicação', fields=(('pub_date'),))
    )
```

Acess the listing page and click in the "eye" icon to see how data is displayed in the visualization page.

## Attaching actions in the visualization page

To enable the edition of a question from the visualization page, call the method actions() in line 3.

```
def serializer(self):
    return (
        super().serializer().actions('editarquestion')
        .fieldset('Dados Gerais', fields=('id', 'text',))
        .fieldset('Publicação', fields=(('pub_date'),))
    )
```

Actions can be attached in the fieldsets as well as shown bellow in line 5.

```
def serializer(self):
    return (
        super().serializer()
        .fieldset('Dados Gerais', fields=('id', 'text',))
        .fieldset('Publicação', fields=(('pub_date'),), actions=('editarquestion',))
    )
```

