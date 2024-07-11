from datetime import datetime, timedelta
from slth.selenium import SeleniumTestCase
class IntegrationTestCase(SeleniumTestCase):
    
    def test(self):
        self.create_superuser('000.000.000-00', '123')

        # Acessando como super-usuário para realizar cadastros básicos
        if self.step('1'):
            self.login('000.000.000-00', '123')
            
            self.click('Cadastros Gerais')
            self.click('CIDs')
            self.click('Cadastrar CID')
            self.enter('Código', 'J01')
            self.enter('Doença', 'Gripe')
            self.click('Enviar')

            self.click('CIAPs')
            self.click('Cadastrar CIAP')
            self.enter('Código', 'A03')
            self.enter('Doença', 'Febre')
            self.click('Enviar')

            self.click('Sexos')
            self.click('Cadastrar sexo')
            self.enter('Nome', 'Masculino')
            self.click('Enviar')
            self.click('Cadastrar sexo')
            self.enter('Nome', 'Feminino')
            self.click('Enviar')

            self.click('Tipos de Atendimento')
            self.click('Cadastrar Tipo de Atendimento')
            self.enter('Nome', 'Teleconsulta')
            self.click('Enviar')
            self.click('Cadastrar Tipo de Atendimento')
            self.enter('Nome', 'Tele-interconsulta')
            self.click('Enviar')

            self.click('Estados')
            self.click('Cadastrar')
            self.enter('Código IBGE', '01')
            self.enter('Sigla', 'RN')
            self.enter('Nome', 'Rio Grande do Norte')
            self.click('Enviar')

            self.click('Municípios')
            self.click('Cadastrar')
            self.choose('Estado', 'Rio Grande do Norte')
            self.enter('Código IBGE', '010001')
            self.enter('Nome', 'Natal')
            self.click('Enviar')

            self.click('Conselhos de Classe')
            self.click('Cadastrar Conselho de Classe')
            self.enter('Sigla', 'CRM')
            self.choose('Estado', 'Rio Grande do Norte')
            self.click('Enviar')

            self.click('Áreas')
            self.click('Cadastrar')
            self.enter('Nome', 'Clínico Geral')
            self.click('Enviar')
            self.click('Cadastrar')
            self.enter('Nome', 'Cardiologia')
            self.click('Enviar')
            self.click('Cadastrar')
            self.enter('Nome', 'Psiquiatria')
            self.click('Enviar')

            self.click('Especialidades')
            self.click('Cadastrar especialidade')
            self.enter('Código', '01')
            self.enter('Nome', 'Clínico Geral')
            self.choose('Área', 'Clínico Geral')
            self.click('Enviar')
            self.click('Cadastrar especialidade')
            self.enter('Código', '02')
            self.enter('Nome', 'Cardiologia')
            self.choose('Área', 'Cardiologia')
            self.click('Enviar')
            self.click('Cadastrar especialidade')
            self.enter('Código', '03')
            self.enter('Nome', 'Psiquiatria')
            self.choose('Área', 'Psiquiatria')
            self.click('Enviar')
            self.logout('000.000.000-00')

        # Acessando como super-usuário para cadastrar pessoas físicas
        if self.step('2'):
            self.login('000.000.000-00', '123')

            self.click('Pessoas Físicas')
            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '466.778.160-28')
            self.enter('Nome', 'João Maria')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '026.219.140-71')
            self.enter('Nome', 'Roberto Carlos')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '779.067.860-41')
            self.enter('Nome', 'Fafá de Belém')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '082.396.140-00')
            self.enter('Nome', 'Marisa Monte')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '385.895.870-02')
            self.enter('Nome', 'Fábio Júnir')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '716.635.620-08')
            self.enter('Nome', 'Ney Matogroso')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '577.106.830-61')
            self.enter('Nome', 'Roberto Justus')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '325.088.940-79')
            self.enter('Nome', 'Tony Ramos')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '263.578.940-10')
            self.enter('Nome', 'Breno Silva')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '580.800.870-08')
            self.enter('Nome', 'Bruno Silva')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')

            self.click('Cadastrar Pessoa Fisica')
            self.enter('CPF', '537.690.540-32')
            self.enter('Nome', 'Juliana Pessoa')
            self.enter('Data de Nascimento', '01/01/1985')
            self.click('Enviar')
        
            self.logout('000.000.000-00')
        
        # Acessando como super-usuário para cadastrar núcleo de telesaúde
        if self.step('3'):
            self.login('000.000.000-00', '123')
            self.click('Núcleos de Telesaúde')
            self.click('Cadastrar Núcleo de Telesaúde')
            self.enter('Nome', 'Núcleo Natal/RN')
            self.choose('Gestores', 'João Maria')
            self.choose('Operadores', 'Roberto Carlos')
            self.click('Enviar')
            self.click('Visualizar')
            self.logout('000.000.000-00')

        # Acessando como gestor de núcleo para cadastrar unidades e adiconar profissionais as unidades
        if self.step('4'):
            self.login('466.778.160-28', '123')

            self.click('Unidades de Saúde')
            self.click('Cadastrar Unidade')
            self.enter('Nome', 'Unidade Capim Macio')
            self.choose('Municipio', 'Natal')
            self.click('Enviar')
            self.enter('Palavras-chaves', 'Unidade Capim Macio')
            self.click('Filtrar')
            self.click('Visualizar')
            self.click('Adicionar Profissional')
            self.choose('Pessoa Física', 'Fafá de Belém')
            self.choose('Especialidade', 'Clínico Geral')
            self.choose('Conselho Profissional', 'CRM')
            self.enter('Nº do Registro Profissional', '46677816028')
            self.click('Enviar')

            self.click('Unidades de Saúde')
            self.click('Cadastrar Unidade')
            self.enter('Nome', 'Unidade Mirassol')
            self.choose('Municipio', 'Natal')
            self.click('Enviar')
            self.enter('Palavras-chaves', 'Unidade Mirassol')
            self.click('Filtrar')
            self.click('Visualizar')
            self.click('Adicionar Profissional')
            self.choose('Pessoa Física', 'Marisa Monte')
            self.choose('Especialidade', 'Clínico Geral')
            self.choose('Conselho Profissional', 'CRM')
            self.enter('Nº do Registro Profissional', '08239614000')
            self.click('Enviar')

            self.logout('466.778.160-28')

        # Acessando como gestor de núcleo para vincular unidades e adicionar profissionais ao núcleo
        if self.step('5'):
            self.login('466.778.160-28', '123')
            self.click('Núcleos de Telesaúde')
            self.click('Visualizar')
            self.click('Editar')
            self.choose('Unidades Atendidas', 'Unidade Capim Macio')
            self.choose('Unidades Atendidas', 'Unidade Mirassol')
            self.click('Enviar')
            
            self.look_at('Detalhamento')
            self.click('Profissionais de Saúde')
            self.click('Adicionar Profissional')
            self.choose('Pessoa Física', 'Fábio Júnir')
            self.choose('Especialidade', 'Cardiologia')
            self.choose('Conselho Profissional', 'CRM')
            self.enter('Nº do Registro Profissional', '38589587002')
            self.choose('Conselho de Especialista', 'CRM')
            self.enter('Nº do Registro de Especialista', '38589587002')

            self.click('Enviar')

            self.click('Adicionar Profissional')
            self.choose('Pessoa Física', 'Ney Matogroso')
            self.choose('Especialidade', 'Psiquiatria')
            self.choose('Conselho Profissional', 'CRM')
            self.enter('Nº do Registro Profissional', '71663562008')
            self.choose('Conselho de Especialista', 'CRM')
            self.enter('Nº do Registro de Especialista', '71663562008')
            self.click('Enviar')

            self.logout('466.778.160-28')
        
        # Agendando teleconsulta como profissional de saúde
        if self.step('6'):
            self.login('779.067.860-41', '123')
            self.click('Alterar Agenda')
            self.click("Noite")
            for i in range(3):
                self.click((datetime.now() + timedelta(hours=i)).strftime('%d/%m/%Y %H:00'))
            self.click('Enviar')
            self.click('Agenda de Atendimentos')
            self.click('Cadastrar Atendimento')
            self.click('Unidade Capim Macio')
            self.click('Teleconsulta')
            self.click('Clínico Geral')
            self.wait(4)
            self.choose('Paciente', 'Roberto Justus')
            self.enter('Motivo', 'Suspetia de Gripe')
            self.enter('Dúvida/Queixa', 'O paciente se queixa de...')
            self.choose('CID', 'Gripe')
            self.choose('CIAP', 'Febre')
            self.click('Fafá de Belém (CPF: 779.067.860-41 / CRM: CRM/RN 46677816028)')
            self.click("Noite")
            self.click((datetime.now() + timedelta(hours=1)).strftime('%d/%m/%Y %H:00'))
            self.click('Enviar')
            self.logout('779.067.860-41')

        # Acessando teleconsulta como paciente
        if self.step('7'):
            self.login('577.106.830-61', '123')
            self.look_at('Próximos Atendimentos')
            self.click('Acessar')
            
            self.click('Sala Virtual')
            self.enter('Imagem', 'tests/imagem.png')
            self.click('Enviar')

            # self.click('Anexar Arquivo')
            # self.enter('Nome', 'Exame')
            # self.enter('Arquivo', 'tests/arquivo.pdf')
            # self.click('Enviar')
            self.logout('577.106.830-61')

        # Acessando como profissional de saúde
        if self.step('8'):
            self.login('779.067.860-41', '123')
            self.look_at('Próximos Atendimentos')
            self.click('Acessar')
            
            self.click('Assinar Termo de Consentimento')
            self.click('Enviar')

            self.click('Sala Virtual')
            self.enter('S - subjetivo', 'Subjetivo....')
            self.enter('O - objetivo', 'Objetivo....')
            self.enter('A - avaliação', 'Avaliação....')
            self.enter('P - Plano', 'Plano....')
            self.enter('Comentário', 'Comentário....')
            self.enter('Encaminhamento', 'Encaminhamento....')
            self.enter('Conduta', 'Conduta....')
            self.click('Enviar')
            self.click('Anexos')
            self.click('Encaminhamentos')
            self.click('Finalizar Atendimento')
            self.click('Enviar')
            self.logout('779.067.860-41')

        # Acessando como tele-interconsultores para definir horários
        if self.step('9'):
            self.login('385.895.870-02', '123')
            self.click('Alterar Agenda')
            self.click('Noite')
            for i in range(3):
                self.click((datetime.now() + timedelta(hours=i)).strftime('%d/%m/%Y %H:00'))
            self.click('Enviar')
            self.logout('385.895.870-02')

            self.login('716.635.620-08', '123')
            self.click('Alterar Agenda')
            self.click('Noite')
            for i in range(3):
                self.click((datetime.now() + timedelta(hours=i)).strftime('%d/%m/%Y %H:00'))
            self.click('Enviar')
            self.logout('716.635.620-08')

        # Agendando tele-interconsulta como profissional de saúde
        if self.step('10'):
            self.login('779.067.860-41', '123')
            self.click('Agenda de Atendimentos')
            self.click('Cadastrar Atendimento')
            self.click('Unidade Capim Macio')
            self.click('Tele-interconsulta')
            self.click('Cardiologia')
            self.wait(4)
            
            self.choose('Paciente', 'Roberto Justus')
            self.enter('Motivo', 'Suspetia de Dengue')
            self.enter('Dúvida/Queixa', 'O paciente se queixa de...')
            self.choose('CID', 'Gripe')
            self.choose('CIAP', 'Febre')
            self.click('Fafá de Belém (CPF: 779.067.860-41 / CRM: CRM/RN 46677816028)')
            self.click('Fábio Júnir (CPF: 385.895.870-02 / CRM: CRM/RN 38589587002)')
            self.click((datetime.now() + timedelta(hours=2)).strftime('%d/%m/%Y %H:00'))
            breakpoint()
            self.click('Enviar')
            self.logout('779.067.860-41')

        # Acessando tele-interconsulta como paciente
        if self.step('11'):
            self.login('577.106.830-61', '123')
            self.look_at('Próximos Atendimentos')
            self.click('Acessar')

            self.click('Sala Virtual')
            self.enter('Imagem', 'tests/imagem.png')
            self.click('Enviar')

            # self.click('Anexar Arquivo')
            # self.enter('Nome', 'Exame')
            # self.enter('Arquivo', 'tests/arquivo.pdf')
            # self.click('Enviar')
            self.logout('577.106.830-61')

        # Acessando tele-interconsulta como tele-interconsultor
        if self.step('12'):
            self.login('385.895.870-02', '123')
            self.look_at('Próximos Atendimentos')
            self.click('Acessar')
            self.wait()

            self.click('Assinar Termo de Consentimento')
            self.click('Enviar')

            self.click('Sala Virtual')
            self.enter('S - subjetivo', 'Subjetivo....')
            self.enter('O - objetivo', 'Objetivo....')
            self.enter('A - avaliação', 'Avaliação....')
            self.enter('P - Plano', 'Plano....')
            self.enter('Comentário', 'Comentário....')
            self.enter('Encaminhamento', 'Encaminhamento....')
            self.enter('Conduta', 'Conduta....')
            self.click('Enviar')
            self.click('Anexos')
            self.click('Encaminhamentos')
            self.logout('385.895.870-02')

        # Acessando tele-interconsulta como profissional de saúde
        if self.step('13'):
            self.login('779.067.860-41', '123')
            self.look_at('Próximos Atendimentos')
            self.click('Acessar')

            self.click('Assinar Termo de Consentimento')
            self.click('Enviar')

            self.click('Sala Virtual')
            self.enter('S - subjetivo', 'Subjetivo....')
            self.enter('O - objetivo', 'Objetivo....')
            self.enter('A - avaliação', 'Avaliação....')
            self.enter('P - Plano', 'Plano....')
            self.enter('Comentário', 'Comentário....')
            self.enter('Encaminhamento', 'Encaminhamento....')
            self.enter('Conduta', 'Conduta....')
            self.click('Enviar')
            self.click('Anexos')
            self.click('Encaminhamentos')
            self.click('Finalizar Atendimento')
            self.click('Enviar')
            self.logout('779.067.860-41')

        # Acessando como gestor de núcleo para consultar as estatísticas
        if self.step('14'):
            self.login('466.778.160-28', '123')
            self.click('Painel de Monitoramento')
            self.logout('466.778.160-28')
