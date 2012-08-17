#

import dbf
import tempfile

from sqlalchemy import Table
from sqlalchemy import Column
# Column Types
from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Unicode

from kotti import DBSession
from kotti import metadata

from kotti.util import _
from kotti.util import title_to_name

from kotti_rdbt.resources import RDBTableColumn



def create_columns(context, request):
    if context.mimetype == 'application/x-dbf':
        tmp = tempfile.NamedTemporaryFile(suffix='.dbf')
        tmp.file.write(context.data)
        tmp.file.flush()
        dbt = dbf.Table(tmp.name)
        for fieldname in dbt.field_names:
            fieldinfo = dbt.field_info(fieldname)
            column_type = None
            column_lenght = 0
            if fieldinfo[0] in ['N', 'F', 'B', 'Y']:
                column_type = 'Float'
                if fieldinfo[2]==0:
                    column_type = 'Integer'
            elif fieldinfo[0] in ['I',]:
                column_type = 'Integer'
            elif fieldinfo[0] in ['C']:
                column_type = 'String'
                column_lenght = fieldinfo[1]
            elif fieldinfo[0] in ['D']:
                column_type = 'Date'
            elif fieldinfo[0] in ['T']:
                column_type = 'DateTime'
            elif fieldinfo[0] in ['L']:
                column_type = 'Boolean'
            if column_type:
                name = title_to_name(fieldname,
                            blacklist=context.keys())
                column = RDBTableColumn(parent= context,
                                    name= name,
                                    title=fieldname,
                                    src_column_name=fieldname,
                                    dest_column_name=fieldname,
                                    column_type=column_type,
                                    column_lenght=column_lenght,
                                    is_pk=False)
                DBSession.add(column)
        request.session.flash(u'Table columns created')


def define_column(col):
    name = col.dest_column_name
    if col.column_type == 'String':
        if col.column_lenght:
           return Column(name, Unicode(col.column_lenght), primary_key=col.is_pk)
        else:
            return Column(name, Unicode(), primary_key=col.is_pk)
    elif col.column_type == 'Integer':
        return Column(name, Integer(), primary_key=col.is_pk)
    elif col.column_type == 'Float':
        return Column(name, Unicode(), primary_key=col.is_pk)
    elif col.column_type == 'Float':
        return Column(name, Date(), primary_key=col.is_pk)
    elif col.column_type == 'DateTime':
        return Column(name, DateTime(), primary_key=col.is_pk)
    else:
        raise TypeError('Unsupported Type %s' % col.column_type)

def create_rdb_table(context, request):
    columns = []
    for col in context.children:
        if col.type == 'rdb_table_column':
            columns.append(define_column(col))
    if columns:
        new_table = Table(context.table_name, metadata,
                    *columns)
        engine = DBSession.connection().engine
        metadata.create_all(engine) # create the table
        context.is_created = True
        request.session.flash(u'Table created')
    else:
        request.session.flash(u'No columns defined, no table created')

def populate_rdb_table(context, request):
    if context.is_created:
        table = Table(context.table_name, metadata, autoload=True)
    else:
        request.session.flash(u'No table created')
        return
    mapping = {}
    for col in context.children:
        if col.type == 'rdb_table_column':
            mapping[col.dest_column_name] = col.src_column_name
    if context.mimetype == 'application/x-dbf':
        tmp = tempfile.NamedTemporaryFile(suffix='.dbf')
        tmp.file.write(context.data)
        tmp.file.flush()
        dbt = dbf.Table(tmp.name)
        dbt.open()
        for record in dbt:
            insert = {}
            for dest, src in mapping.iteritems():
                insert[dest] = record[src]
            print insert
            table.insert().values(**insert).execute()


