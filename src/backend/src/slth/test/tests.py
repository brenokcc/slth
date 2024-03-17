from ..tests import ServerTestCase
from ..permissions import apply_lookups

class ApiTestCase(ServerTestCase):
    def test_form(self):
        self.debug = False
        self.get('/api/add-user/')
        self.assert_model_count('auth.user', 0)
        self.assert_model_count('auth.group', 0)
        data = dict(
            username='brenokcc', email='brenokcc@yahoo.com.br',
            groups__0__id='', groups__0__name='A', groups__0__permissions='',
            groups__1__id='', groups__1__name='B', groups__1__permissions=''
        )
        self.post('/api/add-user/', data=data)
        self.assert_model_count('auth.user', 1)
        self.assert_model_count('auth.group', 2)
        self.get('/api/list-users/')
        user = self.objects('auth.user').first()
        self.get('/api/view-user/{}/'.format(user.pk))
        self.post('/api/login/', data=dict(username='brenokcc', password='213'))
        user.set_password('123')
        user.save()
        self.post('/api/login/', data=dict(username='brenokcc', password='123'))

        self.get('/api/cadastrar-pessoa/')
        data = dict(
            nome='Pedro',
            telefone_pessoal__id='',
            telefone_pessoal__ddd=84,
            telefone_pessoal__numero='99106-2760',
            telefones_profissionais__0__id='',
            telefones_profissionais__0__ddd=84,
            telefones_profissionais__0__numero='3272-3898'
        )
        self.post('/api/cadastrar-pessoa/', data=data)
        self.assert_model_count('test.telefone', 2)
        pessoa = self.objects('test.pessoa').last()
        self.get('/api/visualizar-pessoa/{}/'.format(pessoa.pk))
        self.get('/api/visualizar-pessoa2/{}/'.format(pessoa.pk))

    def test_json(self):
        self.debug = False
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
            telefone_pessoal=dict(ddd=84, numero='99106-2760'),
            telefones_profissionais=[dict(ddd=84, numero='33272-3898')]
        )
        self.post('/api/cadastrar-pessoa/', json=data)
        self.assert_model_count('test.pessoa', 1)
        self.assert_model_count('test.telefone', 2)
        pessoa = self.objects('test.pessoa').last()
        self.assertEqual(pessoa.telefone_pessoal.numero,'99106-2760')
        data = dict(
            nome='Pedro',
            telefone_pessoal=dict(id=pessoa.telefone_pessoal.id, ddd=84, numero='99999-9999'),
            telefones_profissionais=[dict(id=pessoa.telefones_profissionais.first().pk, ddd=84, numero='91111-1111')]
        )
        self.post(f'/api/editar-pessoa/{pessoa.id}/', json=data)
        self.assert_model_count('test.pessoa', 1)
        self.assert_model_count('test.telefone', 2)
        pessoa = self.objects('test.pessoa').last()
        self.assertEqual(pessoa.telefone_pessoal.numero,'99999-9999')
        self.assertEqual(pessoa.telefones_profissionais.first().numero,'91111-1111')

        self.get('/api/visualizar-pessoa/{}/'.format(pessoa.pk))
        self.get('/api/visualizar-pessoa2/{}/'.format(pessoa.pk))

    def test_serialization(self):
        self.debug = False
        juca = self.objects('test.pessoa').create(nome='Juca da Silva')
        cidade = self.objects('test.cidade').create(nome='Natal', prefeito=juca)
        self.get('/api/visualizar-pessoa/{}/'.format(juca.pk))
        self.get('/api/visualizar-pessoa2/{}/'.format(juca.pk))
        self.get('/api/visualizar-cidade/{}/'.format(cidade.pk))
        self.get('/api/visualizar-cidade/{}/?only=dados-gerais&only=cidades-vizinhas'.format(cidade.pk))

    def test_model(self):
        telefone = self.objects('test.telefone').create(ddd=84, numero='99999-9999')
        self.objects('test.pessoa').create(nome='Juca da Silva', telefone_pessoal=telefone)
        self.objects('test.pessoa').create(nome='Maria da Silva')
        qs1 = self.objects('test.pessoa').com_telefone_pessoal()
        qs2 = self.objects('test.pessoa').sem_telefone_pessoal()
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(qs2.count(), 1)
        pessoas = self.objects('test.pessoa').fields('id', 'nome', 'telefone')
        print(pessoas.metadata)
        print(pessoas.counter('telefone_pessoal'))

    def test_queryset(self):
        telefone = self.objects('test.telefone').create(ddd=84, numero='99999-9999')
        self.objects('test.pessoa').create(nome='Juca da Silva', telefone_pessoal=telefone)
        self.objects('test.pessoa').create(nome='Maria da Silva')
        self.objects('auth.user').create(username='juca', email='juca@mail.com', is_superuser=True)
        self.objects('auth.user').create(username='joh', email='john@mail.com')
        #self.get('/api/list-users/?page=2&page_size=1')
        #self.get('/api/list-users/?q=ju&is_superuser=true')
        self.get('/api/listar-pessoas/')

    def test_roles(self):
        a = self.objects('test.funcionario').create(email='adm@mail.com', is_admin=True)
        self.assert_model_count('slth.role', 1)
        a.is_admin = False
        a.save()
        self.assert_model_count('slth.role', 0)
        a.is_admin = True
        a.save()
        self.assert_model_count('slth.role', 1)
        s1 = self.objects('test.funcionario').create(email='s1@mail.com')
        s2 = self.objects('test.funcionario').create(email='s2@mail.com')
        r1 = self.objects('test.rede').create(nome='r1', supervisor=s1)
        r2 = self.objects('test.rede').create(nome='r2', supervisor=s2)
        
        self.objects('slth.role').debug()
        self.assert_model_count('slth.role', 3)
        redes = self.objects('test.rede').all()
        print(redes.lookup('Administrador').apply_lookups(a.email))
        print(redes.lookup('Supervisor', pk='rede').apply_lookups(s1.email))
        print(redes.lookup(supervisor__email='username').apply_lookups(s1.email))

        g1 = self.objects('test.funcionario').create(email='s1@mail.com')
        g2 = self.objects('test.funcionario').create(email='s2@mail.com')
        va1 = self.objects('test.funcionario').create(email='va1@mail.com')
        vb1 = self.objects('test.funcionario').create(email='vb1@mail.com')
        va2 = self.objects('test.funcionario').create(email='va2@mail.com')
        vb2 = self.objects('test.funcionario').create(email='vb2@mail.com')
        la1 = self.objects('test.loja').create(rede=r1, nome='la1', gerente=g1)
        la1.vendedores.add(va1)
        self.objects('test.produto').create(nome='p1a', loja=la1)
        self.objects('test.produto').create(nome='p2a', loja=la1)
        la2 = self.objects('test.loja').create(rede=r1, nome='la2', gerente=g2)
        la2.vendedores.add(va2)
        self.objects('test.produto').create(nome='p1b', loja=la2)
        self.objects('test.produto').create(nome='p2b', loja=la2)
        self.objects('slth.role').debug()

        

        