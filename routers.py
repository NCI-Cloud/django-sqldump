# see https://docs.djangoproject.com/en/1.8/topics/db/multi-db/
# this is a bit messy because 'stats' is a hard-coded string from settings.py

class DumpRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'dump':
            return 'stats'
        return None

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'dump':
            return 'stats'
        return None

    def allow_relation(self, o1, o2, **hints):
        if o1._meta.app_label == 'dump' or o2._meta.app_label == 'dump':
            return True
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        if app_label == 'dump':
            return db == 'stats'
        return None
