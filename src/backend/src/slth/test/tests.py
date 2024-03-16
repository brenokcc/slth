from ..tests import ServerTestCase

class ApiTestCase(ServerTestCase):
    def test_form(self):
        self.debug = True
        self.get('/api/add-user/')
        self.assert_model_count('auth.user', 0)
        self.assert_model_count('auth.group', 0)
        data = dict(
            username='brenokcc', email='brenokcc@yahoo.com.br',
            groups__0='', groups__0__name='A', groups__0__permissions='',
            groups__1='', groups__1__name='B', groups__1__permissions=''
        )
        self.post('/api/add-user/', data)
        self.assert_model_count('auth.user', 1)
        self.assert_model_count('auth.group', 2)
        self.get('/api/list-users/')
        user = self.objects('auth.user').first()
        self.get('/api/view-user/{}/'.format(user.pk))
        self.post('/api/login/', json=dict(username='brenokcc', password='213'))
        user.set_password('123')
        user.save()
        self.post('/api/login/', json=dict(username='brenokcc', password='123'))

        self.get('/api/cadastrar-pessoa/')
        data = dict(
            nome='Pedro',
            telefone_pessoal__0='',
            telefone_pessoal__0__ddd=84,
            telefone_pessoal__0__numero='99106-2760',
            telefones_profissionais__0='',
            telefones_profissionais__0__ddd=84,
            telefones_profissionais__0__numero='3272-3898'
        )
        self.post('/api/cadastrar-pessoa/', data)
        self.assert_model_count('test.telefone', 2)
        pessoa = self.objects('test.pessoa').last()
        self.get('/api/visualizar-pessoa/{}/'.format(pessoa.pk))
        self.get('/api/visualizar-pessoa2/{}/'.format(pessoa.pk))

    def test_json(self):
        self.debug = True
        self.get('/api/add-user/')
        self.assert_model_count('auth.user', 0)
        self.assert_model_count('auth.group', 0)
        data = dict(
            username='brenokcc', email='brenokcc@yahoo.com.br',
            groups=[dict(name='A'), dict(name='B')]
        )
        self.post('/api/add-user/', json=data)
        self.assert_model_count('auth.user', 1)
        self.assert_model_count('auth.group', 2)
        self.get('/api/list-users/')
        user = self.objects('auth.user').first()
        self.get('/api/view-user/{}/'.format(user.pk))
        self.post('/api/login/', json=dict(username='brenokcc', password='213'))
        user.set_password('123')
        user.save()
        self.post('/api/login/', json=dict(username='brenokcc', password='123'))

        self.get('/api/cadastrar-pessoa/')
        data = dict(
            nome='Pedro',
            # telefone_pessoal=[dict(ddd=84, numero='99106-2760')],
            # telefones_profissionais=[dict(ddd=84, numero='33272-3898')]
        )
        self.post('/api/cadastrar-pessoa/', data)
        # self.assert_model_count('test.telefone', 2)
        pessoa = self.objects('test.pessoa').last()
        self.get('/api/visualizar-pessoa/{}/'.format(pessoa.pk))
        self.get('/api/visualizar-pessoa2/{}/'.format(pessoa.pk))

    def test_serialization(self):
        self.debug = True
        juca = self.objects('test.pessoa').create(nome='Juca da Silva')
        cidade = self.objects('test.cidade').create(nome='Natal', prefeito=juca)
        self.get('/api/visualizar-pessoa/{}/'.format(juca.pk))
        self.get('/api/visualizar-pessoa2/{}/'.format(juca.pk))
        self.get('/api/visualizar-cidade/{}/'.format(cidade.pk))
        self.get('/api/visualizar-cidade/{}/?only=dados-gerais&only=cidades-vizinhas'.format(cidade.pk))
        

        