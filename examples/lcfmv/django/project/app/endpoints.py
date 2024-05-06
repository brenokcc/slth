from slth import endpoints
from slth import forms
from slth.components import Boxes, Indicators
from .models import TipoLegislacao, Legislacao, Acordao, Relator, Conselho
from slth.models import Role, User


class TiposLegislacao(endpoints.AdminEndpoint[TipoLegislacao]):
    def check_permission(self):
        return self.check_role('adm', 'opl')

class Conselhos(endpoints.AdminEndpoint[Conselho]):
    pass

class Legislacoes(endpoints.AdminEndpoint[Legislacao]):
    def check_permission(self):
        return self.check_role('adm', 'opl')

class Acordaos(endpoints.AdminEndpoint[Acordao]):
    def check_permission(self):
        return self.check_role('adm', 'opa')

class Relatores(endpoints.AdminEndpoint[Relator]):
    pass


class Usuarios(endpoints.Users):
    def get(self):
        return super().get().actions(add='cadastrarusuario', edit='editarusuario')


class CadastrarUsuario(endpoints.AddEndpoint[User]):
    adm = forms.BooleanField(label='Administrador', required=False)
    opl = forms.BooleanField(label='Operador de Legislação', required=False)
    opa = forms.BooleanField(label='Operador de Acordão', required=False)

    class Meta:
        icon = 'plus'
        verbose_name = 'Cadastrar Usuário'
        modal = True

    def get(self):
        return super().get().fieldset('Papéis', ('adm', 'opl', 'opa'))

    def post(self):
        for name in ['adm', 'opl', 'opa']:
            Role.objects.get_or_create(username=self.instance.username, name=name)
        return super().post()

    def check_permission(self):
        return self.check_role('adm')
    
class EditarUsuario(endpoints.EditEndpoint[User]):
    adm = forms.BooleanField(label='Administrador', required=False)
    opl = forms.BooleanField(label='Operador de Legislação', required=False)
    opa = forms.BooleanField(label='Operador de Acordão', required=False)

    class Meta:
        icon = 'pen'
        verbose_name = 'Editar Usuário'

    def get(self):
        initial = {}
        for name in ['adm', 'opl', 'opa']:
            initial[name] = Role.objects.filter(username=self.instance.username, name=name).exists()
        return super().get().fieldset('Papéis', ('adm', 'opl', 'opa')).initial(**initial)
    
    def post(self):
        for name in ['adm', 'opl', 'opa']:
            if self.cleaned_data.get(name):
                Role.objects.get_or_create(username=self.instance.username, name=name)
            else:
                Role.objects.filter(username=self.instance.username, name=name).delete()
        return super().post()


class AcessoRapido(endpoints.Endpoint):
    def get(self):
        boxes = Boxes(title='Acesso Rápido')
        if self.check_role('adm'):
            boxes.append(icon='users-line', label='Usuários', url='/api/usuarios/')
        if self.check_role('adm', 'opl'):
            boxes.append(icon='list', label='Tipos de Legislação', url='/api/tiposlegislacao/')
        if self.check_role('adm'):
            boxes.append(icon='building', label='Conselhos', url='/api/conselhos/')
            boxes.append(icon='person-chalkboard', label='Relatores', url='/api/relatores/')
        if self.check_role('adm', 'opl'):
            boxes.append(icon='file-contract', label='Legislações', url='/api/legislacoes/')
        if self.check_role('adm', 'opa'):
            boxes.append(icon='file-signature', label='Acordãos', url='/api/acordaos/')
        return boxes

    def check_permission(self):
        return self.request.user.is_authenticated


class AreaPublica(endpoints.PublicEndpoint):

    class Meta:
        verbose_name = 'Área Pública'

    def get(self):
        return (
            self.serializer()
            .endpoint('Consultar', 'consultar', wrap=False)
            .endpoint('Totais', 'totais', wrap=False)
        )


class Totais(endpoints.Endpoint):
    def get(self):
        totais = Indicators('Legislação')
        for tipo in TipoLegislacao.objects.all():
            totais.append(tipo, Legislacao.objects.filter(tipo=tipo).count())
        totais.append('Acordão', Acordao.objects.count())
        return totais

    def check_permission(self):
        return True


class Consultar(endpoints.PublicEndpoint):

    class Meta:
        icon = 'file-contract'
        verbose_name = 'Consultar'

    tipo_documento = forms.ChoiceField(
        label='Tipo de Documento', choices=[
            ['legislacao', 'Legislação'],
            ['acordao', 'Acórdão'],
        ], pick=True, initial='legislacao'
    )
    tipo_legislacao = forms.ModelChoiceField(queryset=TipoLegislacao.objects, label='Tipo de Legislação', required=False, pick=True, help_text='Não informar caso deseje buscar em todos os tipos.')
    orgao_julgador = forms.ChoiceField(label='Órgão Julgador', choices=Acordao.ORGAO_JULGADOR_CHOICES, required=False, pick=True, help_text='Não informar caso deseje buscar em todos os órgãos.')
    natureza = forms.ChoiceField(label='Natureza', choices=Acordao.NATUREZA_CHOICES, required=False, pick=True, help_text='Não informar caso deseje buscar em todos as naturezas.')
    relator = forms.ModelChoiceField(queryset=Relator.objects, label='Relator', required=False, help_text='Não informar caso deseje buscar por todos os relatores.')
    palavas_chaves = forms.CharField(label='Palavras-chaves', required=True)
    criterio_busca = forms.ChoiceField(
        label='Critério da Busca', choices=[
            ['toda', 'Contendo todas palavras'],
            ['qualquer', 'Contendo qualquer uma das palavras'],
            ['exato', 'Contendo a expressão exata'],
        ], pick=True, initial='toda'
    )
    escopo_busca_legislacao = forms.MultipleChoiceField(
        label='Escopo da Busca', choices=[
            ['numero', 'Número'],
            ['ementa', 'Ementa'],
            ['conteudo', 'Conteúdo'],
        ], pick=True, initial=['conteudo']
    )
    escopo_busca_acordao = forms.MultipleChoiceField(
        label='Escopo da Busca', choices=[
            ['numero', 'Número'],
            ['ano', 'Ano'],
            ['ementa', 'Ementa'],
            ['conteudo', 'Conteúdo'],
            ['orgao_julgador', 'Órgão Julgador'],
        ], pick=True, initial=['conteudo']
    )

    def get(self):
        return (
            self.formfactory(method='GET')
            .info('Busque pelas legislações/acordãos cadastradros no sistema através de uma ou mais palavras-chaves.')
            .fields('tipo_documento', 'tipo_legislacao', 'orgao_julgador', 'natureza', 'relator', 'palavas_chaves', 'criterio_busca', 'escopo_busca_legislacao', 'escopo_busca_acordao')
            .hidden('escopo_busca_acordao', 'orgao_julgador', 'natureza', 'relator')
        )

    def post(self):
        palavas_chaves = self.cleaned_data.get('palavas_chaves')
        criterio_busca = self.cleaned_data.get('criterio_busca')
        if self.cleaned_data.get('tipo_documento') == 'legislacao':
            escopo_busca = self.cleaned_data.get('escopo_busca_legislacao')
            tipo_legislacao = self.cleaned_data.get('tipo_legislacao')
            qs = Legislacao.objects
            if tipo_legislacao:
                qs = qs.filter(tipo=tipo_legislacao)
        else:
            escopo_busca = self.cleaned_data.get('escopo_busca_acordao')
            orgao_julgador = self.cleaned_data.get('orgao_julgador')
            natureza = self.cleaned_data.get('natureza')
            relator = self.cleaned_data.get('relator')
            qs = Acordao.objects
            if orgao_julgador:
                qs = qs.filter(orgao_julgador=orgao_julgador)
            if natureza:
                qs = qs.filter(natureza=natureza)
            if relator:
                qs = qs.filter(relator=relator)
        resultado = qs.none()
        if criterio_busca == 'toda':
            for campo in escopo_busca:
                resultado = resultado | qs.filter(**{f'{campo}__icontains': palavas_chaves})
        elif criterio_busca == 'qualquer':
            for campo in escopo_busca:
                for palavra in palavas_chaves.split():
                    resultado = resultado | qs.filter(**{f'{campo}__icontains': palavra})
        else:
            for campo in escopo_busca:
                resultado = resultado | qs.filter(**{campo: palavas_chaves})
        return resultado.fields('get_descricao', 'ementa', 'get_arquivo').contextualize(self.request).limit(5)
    
    def on_tipo_documento_change(self, controller, values):
        if values.get('tipo_documento') == 'legislacao':
            controller.show('tipo_legislacao', 'escopo_busca_legislacao')
            controller.hide('escopo_busca_acordao', 'orgao_julgador', 'natureza', 'relator')
        else:
            controller.hide('tipo_legislacao', 'escopo_busca_legislacao')
            controller.show('escopo_busca_acordao', 'orgao_julgador', 'natureza', 'relator')



class RevogarLegislacao(endpoints.Endpoint):

    class Meta:
        target = 'instance'
        model = Legislacao
        fields = 'revogada_por',
        help_text = 'Serão listadas apenas legislações do mesmo tipo e com data posterior ou igual a data da legislação que está sendo revogada.'

    def get_revogada_por_queryset(self, queryset):
        return queryset.filter(tipo=self.instance.tipo, data__gte=self.instance.data).exclude(pk=self.instance.pk)

    def check_permission(self):
        return self.check_role('adm', 'opl')

