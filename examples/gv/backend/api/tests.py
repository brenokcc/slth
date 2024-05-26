from slth.selenium import SeleniumTestCase
class IntegrationTestCase(SeleniumTestCase):
    
    def test(self):
        if self.step("1"):
            self.create_superuser('admin', '123')
            self.login('admin', '123')
            self.click('Administradores')
            self.click('Cadastrar')
            self.enter('CPF', '000.000.000-00')
            self.enter('Nome', 'Carlos André')
            self.click('Enviar')
            self.logout('admin')
        
        if self.step("2"):
            self.login('000.000.000-00', '123')
            self.click('Cadastros Gerais')
            self.click('Estados')

            self.click('Cadastrar')
            self.enter('Sigla', 'RN')
            self.enter('Nome', 'Rio Grande do Norte')
            self.click('Enviar')

            self.click('Cadastrar')
            self.enter('Sigla', 'PB')
            self.enter('Nome', 'Paraíba')
            self.click('Enviar')

            self.click('Prioridades')
            self.click('Cadastrar')
            self.enter('Descrição', 'Baixa')
            self.enter('Cor', '#00F900')
            self.enter('Prazo para Resposta', '24')
            self.click('Enviar')

            self.click('Cadastrar')
            self.enter('Descrição', 'Alta')
            self.enter('Cor', '#ea4025')
            self.enter('Prazo para Resposta', '6')
            self.click('Enviar')
            self.logout('000.000.000-00')
        
        if self.step("3"):
            self.login('000.000.000-00', '123')
            self.click('Base de Conhecimento')
            self.click('Assuntos')
            self.click('Cadastrar')
            self.enter('Descrição', 'Licitação')
            self.click('Enviar')
            self.click('Visualizar')
            self.click('Cadastrar')
            self.enter('Descrição', 'Inexigibilidade')
            self.click('Enviar')
            self.click('Visualizar')
            self.click('Cadastrar')
            self.enter('Nome', 'Legislação Atual')
            self.enter('Arquivo', 'tests/arquivo.txt')
            self.click('Enviar')
            self.logout('000.000.000-00')

        if self.step("4"):
            self.login('000.000.000-00', '123')
            self.click('Base de Conhecimento')
            self.click('Especialistas')
            self.click('Cadastrar')
            self.enter('Nome', 'Mario Farias')
            self.enter('CPF', '111.111.111-11')
            self.choose('Estados', 'RN')
            self.choose('Assuntos', 'Licitação')
            self.click('Enviar')
            self.logout('000.000.000-00')

        if self.step("4"):
            self.login('000.000.000-00', '123')
            self.click('Base de Conhecimento')
            self.click('Perguntas Frequêntes')
            self.click('Cadastrar')
            self.choose('Tópico', 'Inexigibilidade')
            self.enter('Pergunta', 'O que é inexigibilidade de licitação?')
            self.click('Enviar')
            self.logout('000.000.000-00')

        if self.step("5"):
            self.login('000.000.000-00', '123')
            self.click('Clientes')
            self.click('Cadastrar')
            self.enter('Nome', 'Prefeitura de Natal')
            self.enter('CPF/CNPJ', '11.111.111/1111-11')
            self.enter('Telefone', '(99) 99999-9999')
            self.enter('Nome do Responsável', 'Maria Souza')
            self.enter('CPF do Responsável', '222.222.222-22')
            self.enter('Cargo do Responsável', 'Secretária')
            self.enter('E-mail', 'maria.souza@mail.com')
            self.choose('Estado', 'RN')
            self.choose('Assuntos', 'Licitação')
            self.click('Enviar')
            self.click('Visualizar')
            self.click('Consultantes')
            self.click('Editar')
            self.click('Enviar')
            self.logout('000.000.000-00')

        if self.step("6"):
            self.login('222.222.222-22', '123')
            self.click('Consultar')
            self.choose('Prioridade', 'Alta')
            self.choose('Tópico', 'Inexigibilidade')
            self.enter('Pergunta', 'O que é inexigibilidade de licitação?')
            self.click('Enviar')
            self.logout('222.222.222-22')

        if self.step("7"):
            self.login('111.111.111-11', '123')
            self.click('Visualizar')
            self.click('Assumir Consulta')
            self.click('Enviar')
            self.click('Consultar I.A.')
            self.click('Enviar')
            self.click('Enviar Resposta')
            self.click('Enviar')
            self.logout('111.111.111-11')

        if self.step("8"):
            self.login('222.222.222-22', '123')
            self.click('Visualizar')
            self.see('Resposta teste.')
            self.click('Início')
            self.click('Não-Respondidas')
            self.see('Nenhum registro encontrado.')
            self.logout('222.222.222-22')

