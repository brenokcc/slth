from ..roles import role

def meta(verbose_name):
    def decorate(function):
        function.verbose_name = verbose_name
        return function
    return decorate
