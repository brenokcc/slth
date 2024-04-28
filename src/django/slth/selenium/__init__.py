import os
import signal
import warnings
from subprocess import DEVNULL, check_call

from django.apps import apps
from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.contrib.staticfiles.testing import LiveServerTestCase
from django.core.cache import cache
from django.core.management import call_command
from django.core.servers.basehttp import WSGIServer
from django.db import connection
from django.http import HttpResponse
from django.core.management import call_command
from django.contrib.auth.models import User

from .browser import Browser

WSGIServer.handle_error = lambda *args, **kwargs: None


class ContextManager:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TestStaticFilesHandler(StaticFilesHandler):
    def _middleware_chain(self, request):
        return HttpResponse()


class SeleniumTestCase(LiveServerTestCase):
    SAVE_STEP = cache.get("SAVE_STEP")
    FROM_STEP = cache.get("FROM_STEP")
    NOBUILD = cache.get("NOBUILD")
    HEADLESS = cache.get("HEADLESS", True)
    RESTORE = cache.get("RESTORE")
    LOG_ACTION = cache.get("LOG_ACTION", False)

    FRONTEND_HOST_URL = None
    FRONTEND_PROJECT_DIR = None
    FRONTEND_PROCESS_PID = None

    static_handler = TestStaticFilesHandler

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_count = 0
        self.current_username = None
        warnings.filterwarnings("ignore")

        self._url = "/app/login/"
        self._execute = 1
        self._step = 0
        self._adverb = 0

    @classmethod
    def setUpClass(cls):
        call_command("sync")
        cls.host = os.environ.get('BACKEND_HOST', '127.0.0.1')
        cls.port = int(os.environ.get('BACKEND_PORT', '8000'))
        super().setUpClass()
        print(cls.live_server_url)
        cache.clear()
        # url = "http://{}:{}".format(
        #     os.environ.get('FRONTEND_HOST', '127.0.0.1'),
        #     os.environ.get('FRONTEND_PORT', '5173')
        # )
        cls.browser = Browser(cls.live_server_url, slowly=False, headless=SeleniumTestCase.HEADLESS)
        for app_label in settings.INSTALLED_APPS:
            app_module = __import__(app_label)
            app_dir = os.path.dirname(app_module.__file__)
            fixture_path = os.path.join(app_dir, "fixtures", "test.json")
            if os.path.exists(fixture_path):
                call_command("loaddata", fixture_path)
        settings.DEBUG = True

    def create_superuser(self, username, password):
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, password=password)

    def wait(self, seconds=1):
        self.browser.wait(seconds)

    def open(self, url="/"):
        self.browser.open(url)
        self._url = url

    def login(self, username, password):
        self.open('/app/login/')
        self.enter('Username', username)
        self.enter('Senha', password)
        self.click('Enviar')

    def logout(self, username):
        self.click(username)
        self.click('Sair')

    def slow(self, slowly=False):
        self.browser.slow(slowly)

    def reload(self):
        self.browser.reload()

    def enter(self, name, value, submit=False, count=5):
        self.browser.enter(name, value, submit, count)

    def choose(self, name, value, count=5):
        self.browser.choose(name, value, count)

    def see(self, text, flag=True, count=5):
        self.browser.see(text, flag, count)

    def look_at(self, text, count=5):
        self.browser.look_at(text, count)
        return ContextManager()

    def click(self, text):
        self.browser.click(text)

    def step(self, description=None):
        if not SeleniumTestCase.FROM_STEP and not SeleniumTestCase.SAVE_STEP:
            return True
        if self._step > 1 and self._execute:
            self.save()
        if SeleniumTestCase.RESTORE and self.step_file_exists(SeleniumTestCase.RESTORE) and self._execute:
            print(f"Creating development database from existing step {SeleniumTestCase.RESTORE}")
            self.create_dev_database(self.step_file_exists(SeleniumTestCase.RESTORE))
            self._execute = 0
            return False
        self._step += 1
        if SeleniumTestCase.FROM_STEP:
            if self._step == SeleniumTestCase.FROM_STEP:
                self.load(self._step)
                self._execute = 2
                return False
            else:
                self._execute = 2 if self._execute > 1 else 0

        if self._execute:
            description = "Executando passo {}{}".format(self._step, f" ({description})" if description else "")
            print(description)
        return self._execute

    def tearDown(self):
        self.save()
        if SeleniumTestCase.LOG_ACTION:
            SeleniumTestCase.LOG_ACTION = 2
            self.reload()
            input("Logging the actions in the terminal. Type any key to exit!\n\n")
        return super().tearDown()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        try:
            if cls.FRONTEND_PROCESS_PID:
                os.killpg(os.getpgid(cls.FRONTEND_PROCESS_PID), signal.SIGTERM)
        except ProcessLookupError:
            pass

        cls.browser.close()

    def postgres_parameters(self):
        dbhost = settings.DATABASES["default"]["HOST"]
        dbuser = settings.DATABASES["default"]["USER"]
        dbport = settings.DATABASES["default"]["PORT"]
        dbparam = f"-U {dbuser} -h {dbhost} -p {dbport}"
        return dbparam

    def create_dev_database(self, fname=None):
        dbname = settings.DATABASES["default"]["NAME"]
        if "sqlite3" in settings.DATABASES["default"]["ENGINE"]:
            if os.path.exists("db.sqlite3"):
                os.unlink("db.sqlite3")
            os.system('sqlite3 db.sqlite3 "VACUUM;"')
            if fname:
                os.system(f"cat {fname} | sqlite3 db.sqlite3")
            else:
                os.system(f'sqlite3 {dbname} ".dump" | sqlite3 db.sqlite3')
        elif "postgresql" in settings.DATABASES["default"]["ENGINE"]:
            dbparam = self.postgres_parameters()
            dbname2 = dbname[5:]
            os.system(f"dropdb {dbparam} --if-exists {dbname2}")
            os.system(f"createdb {dbparam} {dbname2}")
            if fname:
                os.system(f"pg_dump {dbparam} --schema-only -d {dbname} | psql {dbparam} -q -d {dbname2} > /dev/null")
                os.system(f"cat {fname} | psql {dbparam} -q -d {dbname2} > /dev/null")
            else:
                os.system(f"pg_dump {dbparam} -d {dbname} | psql {dbparam} -q -d {dbname2} > /dev/null")

    def save(self):
        if not SeleniumTestCase.SAVE_STEP:
            return
        if SeleniumTestCase.RESTORE == self._step:
            print(f"Creating development database from step {self._step}")
            self.create_dev_database()
            self._execute = 0
        if self._execute:
            print(f"Saving step {self._step}")
            os.makedirs(".steps", exist_ok=True)
            dbname = settings.DATABASES["default"]["NAME"]
            fname = "{}.sql".format(os.path.join(".steps", str(self._step)))
            if "sqlite3" in settings.DATABASES["default"]["ENGINE"]:
                cmd = f'sqlite3 {dbname} ".dump" > {fname}'
                if "memory" not in cmd:
                    os.system(cmd)
            elif "postgresql" in settings.DATABASES["default"]["ENGINE"]:
                cmd = "pg_dump {} -d {} --inserts --data-only --no-owner -f {}".format(
                    self.postgres_parameters(), dbname, fname
                )
                check_call(cmd.split(), stdout=DEVNULL, stderr=DEVNULL)

    def step_file_exists(self, step):
        fname = "{}.sql".format(os.path.join(".steps", str(step)))
        return fname if os.path.exists(fname) else False

    def load(self, step):
        fname = "{}.sql".format(os.path.join(".steps", str(self._step)))
        print(f"Loading step {step}")
        dbname = settings.DATABASES["default"]["NAME"]
        if "sqlite3" in settings.DATABASES["default"]["ENGINE"]:
            cmd = f"""sqlite3 {dbname} \"PRAGMA writable_schema = 1;
                    delete from sqlite_master where type in ('table', 'index', 'trigger');
                    PRAGMA writable_schema = 0;VACUUM;PRAGMA integrity_check;\""""
            os.system(cmd)
            cmd = f"cat {fname} | sqlite3 {dbname}"
            os.system(cmd)
        else:
            cursor = connection.cursor()
            tables = [m._meta.db_table for c in apps.get_app_configs() for m in c.get_models()]
            for table in tables:
                cursor.execute(f"truncate table {table} cascade;")
            cmd = f"psql {self.postgres_parameters()} -d {dbname} --file={fname}"
            check_call(cmd.split(), stdout=DEVNULL, stderr=DEVNULL)

    def loaddata(self, fixture_path):
        call_command("loaddata", "--skip-checks", fixture_path)
