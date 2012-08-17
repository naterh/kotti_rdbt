from kotti.resources import Content
from kotti.resources import File
from kotti.resources import IDefaultWorkflow
from kotti.util import camel_case_to_name
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
    table_name = Column(String(80), nullable=False, unique=True)
    is_created = Column(Boolean(), nullable=False)
    #XXX + more table metadata


    type_info = Content.type_info.copy(
        name=u'Table',
        title=_(u'Table'),
        add_view=u'add_table',
        addable_to=[u'Document'],
        )

    def __init__(self, table_name=None, **kwargs):
        super(RDBTable, self).__init__(**kwargs)
        if table_name:
            self.table_name = camel_case_to_name(table_name.split('.')[0])
        else:
            self.table_name = camel_case_to_name(self.filename.split('.')[0])
        self.is_created = False





class RDBTableColumn(Content):
    id = Column(Integer, ForeignKey('contents.id'), primary_key=True)
    src_column_name = Column(Unicode(80), nullable=False)
    dest_column_name = Column(Unicode(80), nullable=False)
    column_type = Column(Unicode(10), nullable=False)
    column_lenght = Column(Integer)
    is_pk = Column(Boolean(), nullable=False)



    type_info = Content.type_info.copy(
        name=u'Column',
        title=_(u'Column'),
        add_view=u'add_column',
        addable_to=[u'Table'],
        )

    def __init__(self, src_column_name=None, dest_column_name=None,
                    column_type=None, column_lenght=None, is_pk=False,
                    in_navigation=False, **kwargs):
        super(RDBTableColumn, self).__init__(in_navigation=in_navigation, **kwargs)
        self.src_column_name = src_column_name
        self.dest_column_name = dest_column_name
        self.column_type = column_type
        self.column_lenght = column_lenght
        self.is_pk = is_pk

