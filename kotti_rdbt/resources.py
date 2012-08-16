from kotti.resources import Content
from kotti.resources import File
from kotti.resources import IDefaultWorkflow
from kotti.util import JsonType
from kotti_rdbt import _
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from zope.interface import implements
from zope.interface import Interface

class IRDBTable(Interface):
    pass

class RDBTable(File):
    implements(IRDBTable, IDefaultWorkflow)
    id = Column('id', Integer, ForeignKey('files.id'), primary_key=True)
    table_name = Column(String(80), nullable=False)
    #XXX + more table metadata


    type_info = Content.type_info.copy(
        name=u'Table',
        title=_(u'Table'),
        add_view=u'add_table',
        addable_to=[u'Document'],
        )

    def __init__(self, table_name=None, **kwargs):
        super(RDBTable, self).__init__(**kwargs)
        self.table_name = table_name





class RDBTableColumn(Content):
    id = Column(Integer, ForeignKey('contents.id'), primary_key=True)
    src_column_name = Column(Unicode(80), nullable=False)
    dest_column_name = Column(Unicode(80), nullable=False)
    column_type = Column(Unicode(10), nullable=False)
    column_lenght = Column(Integer)



    type_info = Content.type_info.copy(
        name=u'Column',
        title=_(u'Column'),
        add_view=u'add_column',
        addable_to=[u'Table'],
        )

    def __init__(self, src_column_name=None, dest_column_name=None,
                    column_type=None, column_lenght=0,
                    in_navigation=False, **kwargs):
        super(RDBTableColumn, self).__init__(in_navigation=in_navigation, **kwargs)
        self.src_column_name = src_column_name
        self.dest_column_name = dest_column_name
        self.column_type = column_type
        self.column_lenght = column_lenght
