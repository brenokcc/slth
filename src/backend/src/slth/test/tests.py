from ..tests import ServerTestCase, HttpRequest
from ..serializer import Serializer
from datetime import date, timedelta
from ..exceptions import JsonResponseException

class ApiTestCase(ServerTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug = False

    def test_form(self):
        self.get('/api/adduser/')
        self.assert_model_count('auth.user', 0)
        self.assert_model_count('auth.group', 0)
        data = dict(
            username='brenokcc', email='brenokcc@yahoo.com.br',
            groups__0__id='', groups__0__name='A', groups__0__permissions='',
            groups__1__id='', groups__1__name='B', groups__1__permissions=''
        )
        self.post('/api/adduser/', data=data)
        self.assert_model_count('auth.user', 1)
        self.assert_model_count('auth.group', 2)
        self.get('/api/listusers/')
        user = self.objects('auth.user').first()
        self.get('/api/viewuser/{}/'.format(user.pk))
        self.post('/api/login/', data=dict(username='brenokcc', password='213'))
        user.set_password('123')
        user.save()
        self.post('/api/login/', data=dict(username='brenokcc', password='123'))

        self.get('/api/cadastrarpessoa/')
        data = dict(
            nome='Pedro',
            telefone_pessoal__id='',
            telefone_pessoal__ddd=84,
            telefone_pessoal__numero='99106-2760',
            telefones_profissionais__0__id='',
            telefones_profissionais__0__ddd=84,
            telefones_profissionais__0__numero='3272-3898'
        )
        self.post('/api/cadastrarpessoa/', data=data)
        self.assert_model_count('test.telefone', 2)
        pessoa = self.objects('test.pessoa').last()
        self.get('/api/visualizarpessoa/{}/'.format(pessoa.pk))
        self.get('/api/visualizarpessoa2/{}/'.format(pessoa.pk))

    def test_json(self):
        self.get('/api/adduser/')
        self.assert_model_count('auth.user', 0)
        self.assert_model_count('auth.group', 0)
        data = dict(
            username='brenokcc', email='brenokcc@yahoo.com.br',
            groups=[dict(name='A'), dict(name='B')]
        )
        self.post('/api/adduser/', json=data)
        self.assert_model_count('auth.user', 1)
        self.assert_model_count('auth.group', 2)
        self.get('/api/listusers/')
        user = self.objects('auth.user').first()
        self.get('/api/edituser/{}/'.format(user.pk))
        self.get('/api/viewuser/{}/'.format(user.pk))
        self.post('/api/login/', json=dict(username='brenokcc', password='213'))
        user.set_password('123')
        user.save()
        self.post('/api/login/', json=dict(username='brenokcc', password='123'))

        self.get('/api/cadastrarpessoa/')
        data = dict(
            nome='Pedro',
            telefone_pessoal=dict(ddd=84, numero='99106-2760'),
            telefones_profissionais=[dict(ddd=84, numero='33272-3898')]
        )
        self.post('/api/cadastrarpessoa/', json=data)
        self.assert_model_count('test.pessoa', 1)
        self.assert_model_count('test.telefone', 2)
        pessoa = self.objects('test.pessoa').last()
        self.assertEqual(pessoa.telefone_pessoal.numero,'99106-2760')
        data = dict(
            nome='Pedro',
            telefone_pessoal=dict(id=pessoa.telefone_pessoal.id, ddd=84, numero='99999-9999'),
            telefones_profissionais=[dict(id=pessoa.telefones_profissionais.first().pk, ddd=84, numero='91111-1111')]
        )
        self.post(f'/api/editarpessoa/{pessoa.id}/', json=data)
        self.assert_model_count('test.pessoa', 1)
        self.assert_model_count('test.telefone', 2)
        pessoa = self.objects('test.pessoa').last()
        self.assertEqual(pessoa.telefone_pessoal.numero,'99999-9999')
        self.assertEqual(pessoa.telefones_profissionais.first().numero,'91111-1111')

        self.get('/api/visualizarpessoa/{}/'.format(pessoa.pk))
        self.get('/api/visualizarpessoa2/{}/'.format(pessoa.pk))

    def test_serialization(self):
        juca = self.objects('test.pessoa').create(nome='Juca da Silva')
        cidade = self.objects('test.cidade').create(nome='Natal', prefeito=juca)
        self.get('/api/visualizarpessoa/{}/'.format(juca.pk))
        self.get('/api/visualizarpessoa2/{}/'.format(juca.pk))
        self.get('/api/visualizarcidade/{}/'.format(cidade.pk))
        self.get('/api/visualizarcidade/{}/?only=dados_gerais__cidades_vizinhas'.format(cidade.pk))

    def test_serializer(self):
        telefone = self.objects('test.telefone').create(ddd=84, numero='99999-9999')
        juca = self.objects('test.pessoa').create(nome='Juca da Silva', telefone_pessoal=telefone, data_nascimento=date.today())
        for numero in ('11111-1111', '22222-2222'):
            juca.telefones_profissionais.add(self.objects('test.telefone').create(ddd=84, numero=numero))
        querystrings = {
            None: 'object',
            '?only=recursos_humanos__ponto__get_usuarios': 'queryset',
            '?only=recursos_humanos__ponto__afastamentos': 'fieldset',
            '?only=ensino__projetos_finais': 'fieldset',
            '?only=ensino__diarios': 'fieldset',
            '?only=telefones_profissionais': 'queryset',
            '?only=dados_para_contato': 'fieldset'
        }
        for querystring, data_type in querystrings.items():
            serializer = (
                Serializer(juca, HttpRequest(querystring))
                .fieldset('Dados Gerais', ['nome', ['sexo', 'data_nascimento']])
                .fieldset('Dados para Contato', ['telefone_pessoal', 'get_qtd_telefones_profissionais'])
                .queryset('Telefones Profissionais', 'telefones_profissionais')
                .section('Ensino')
                    .fieldset('Diários', ())
                    .fieldset('Projetos Finais', ())
                .parent()
                .group('Recursos Humanos')
                    .section('Ponto')
                        .fieldset('Frequências', ())
                        .fieldset('Afastamentos', ())
                        .queryset('Usuários', 'get_usuarios')
                    .parent()
                .parent()
            )
            data = serializer.serialize(self.debug)
            self.assertEquals(data['type'], data_type)

    def test_actions(self):
        telefone = self.objects('test.telefone').create(ddd=84, numero='99999-9999')
        juca = self.objects('test.pessoa').create(nome='Juca da Silva', telefone_pessoal=telefone, data_nascimento=date.today())
        maria = self.objects('test.pessoa').create(nome='Maria da Silva', data_nascimento=date.today())
        
        data = (
            Serializer(juca, HttpRequest('?action=editarpessoa'))
            .actions('slth.test.endpoints.editarpessoa')
            .serialize(self.debug)
        )
        self.assertEquals(data['type'], 'form')
          
        data = (
            self.objects('test.pessoa')
            .serializer(Serializer().actions('slth.test.endpoints.editarpessoa'))
            .contextualize(HttpRequest(f'?pk={maria.pk}&action=editarpessoa')).serialize(debug=self.debug)
        )
        self.assertEquals(data['type'], 'form')

        data = dict(nome='Maria da Silva 2', data_nascimento=date.today())
        data = (
            self.objects('test.pessoa')
            .serializer(Serializer().actions('slth.test.endpoints.editarpessoa'))
            .contextualize(HttpRequest(f'?pk={maria.pk}&action=editarpessoa', data)).serialize(debug=self.debug)
        )
        data = Serializer(self.objects('test.pessoa').get(pk=maria.pk)).serialize(self.debug)
        self.assertEquals(data['title'], 'Maria da Silva 2')
        

    def test_model(self):
        today = date.today()
        next_month = today + timedelta(days=31)
        telefone = self.objects('test.telefone').create(ddd=84, numero='99999-9999')
        juca = self.objects('test.pessoa').create(nome='Juca da Silva', telefone_pessoal=telefone, data_nascimento=today)
        maria = self.objects('test.pessoa').create(nome='Maria da Silva', data_nascimento=next_month)
        qs1 = self.objects('test.pessoa').com_telefone_pessoal()
        qs2 = self.objects('test.pessoa').sem_telefone_pessoal()
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(qs2.count(), 1)

        # using a custom serializer in the queryset
        self.objects('test.pessoa').serializer(
            Serializer().fieldset('Dados Gerais', ('id', 'nome')).fields('telefone_pessoal')
        ).serialize(debug=self.debug)

        # using calendar
        pessoas = (
            self.objects('test.pessoa')
            .fields('id', 'nome', 'telefone_pessoal', 'data_nascimento', 'get_qtd_telefones_profissionais')
            .calendar('data_nascimento')
        )    
        serialized = pessoas.serialize(debug=self.debug)
        self.assertEqual(len(serialized['data']), 1)
        self.assertEqual(serialized['data'][0]['data'][1]['value'], juca.nome)
        
        request = HttpRequest(f'?data_nascimento__day={next_month.day}&data_nascimento__month={next_month.month}&data_nascimento__year={next_month.year}')
        serialized = pessoas.contextualize(request).serialize(debug=self.debug)
        self.assertEqual(len(serialized['data']), 1)
        self.assertEqual(serialized['data'][0]['data'][1]['value'], maria.nome)

        for numero in ('11111-1111', '22222-2222', '33333-3333'):
            juca.telefones_profissionais.add(self.objects('test.telefone').create(ddd=84, numero=numero))

        # test default object serializer
        serialized = Serializer(juca).serialize(self.debug)
        
        # test custom object serializer
        serialized = Serializer(juca).fieldset(
            'Dados Gerais', ['nome', ['sexo', 'data_nascimento']]
        ).fieldset(
            'Dados para Contato', ['telefone_pessoal', 'get_qtd_telefones_profissionais']
        ).queryset('Telefones Profissionais', 'telefones_profissionais').serialize(self.debug)
        
        # test only parameter for fieldset
        serialized = Serializer(juca, HttpRequest('?only=dados_para_contato')).fieldset(
            'Dados Gerais', ['nome', ['sexo', 'data_nascimento']]
        ).fieldset(
            'Dados para Contato', ['telefone_pessoal', 'get_qtd_telefones_profissionais']
        ).queryset('Telefones Profissionais', 'telefones_profissionais').serialize(self.debug)
        
        # test only parameter for fieldset
        serialized = Serializer(juca, HttpRequest('?only=telefones_profissionais&page_size=1&page=1')).serialize(self.debug)
        # test pagination of a queryset relation of an object 
        serialized = Serializer(juca, HttpRequest('?only=telefones_profissionais&page_size=1&page=2')).serialize(self.debug)
        serialized = Serializer(juca, HttpRequest('?only=telefones_profissionais&page_size=1&page=3')).serialize(self.debug)

        #print(pessoas.counter('telefone_pessoal'))

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
        
        if self.debug: self.objects('slth.role').debug()
        self.assert_model_count('slth.role', 3)
        redes = self.objects('test.rede').all()
        self.assertEquals(redes.lookup('Administrador').apply_lookups(a.email).count(), 2)
        self.assertEquals(redes.lookup('Supervisor', pk='rede').apply_lookups(s1.email).count(), 1)
        self.assertEquals(redes.lookup(supervisor__email='username').apply_lookups(s1.email).count(), 1)

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
        if self.debug: self.objects('slth.role').debug()

        

        