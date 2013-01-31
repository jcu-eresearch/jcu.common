from __future__ import absolute_import
from json import JSONEncoder

class SQLAlchemyJSONEncoder(JSONEncoder):
    """JSON encoder for mapped SQLAlchemy models.
    """

    def default(self, obj):
        """Return default implementation if not mapped class, else return
        only mapped fields and values.
        """
        if not hasattr(obj, '__mapper__'):
            return super(SQLAlchemyJSONEncoder, self).default(obj)
        else:
            mapped = obj.__mapper__.columns.keys()
            return {key: value for key, value in vars(obj).iteritems() \
                    if key in mapped}


