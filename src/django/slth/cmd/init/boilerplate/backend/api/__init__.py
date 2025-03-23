from slth.application import Application


class ApiApplication(Application):
    def __init__(self):
        super().__init__()
        self.groups.add(administrador="Administrador", operador="Operador")
        self.dashboard.usermenu.add(
            "dev.icons",
            "user.users",
            "log.logs",
            "email.emails",
            "pushsubscription.pushsubscriptions",
            "job.jobs",
            "deletion.deletions",
            "settings.settings",
            "auth.logout",
        )
        self.dashboard.boxes.add("user.users")
        self.dashboard.actions.add()
        self.dashboard.toolbar.add()
        self.dashboard.top.add()
        self.dashboard.center.add()
        self.dashboard.search.add()
        self.dashboard.adder.add()
        self.dashboard.tools.add()
        self.dashboard.settings.add()
        self.menu.add({"Sair": "auth.logout"})
