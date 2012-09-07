# -*- coding: utf-8 -*-
import logging

import dbf
import tempfile
import tarfile, zipfile
import mimetypes

from sqlalchemy import Table
from sqlalchemy import Column
# Column Types
from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Integer
# -*- coding: utf-8 -*-
from sqlalchemy import Unicode

from kotti import DBSession
from kotti import metadata

from kotti.util import _
from kotti.util import title_to_name

from kotti_rdbt.resources import RDBTableColumn

#try:
from geo_ko.utils import extract_geometry_info
from geo_ko.utils import define_geo_column, populate_geo_table
SPATIAL = True
#except:
#    SPATIAL = False



logger = logging.getLogger('kotti_rbt')


def create_columns_from_dbf(data, context):
    tmp = tempfile.NamedTemporaryFile(suffix='.dbf')
    tmp.file.write(data)
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
        elif fieldinfo[0] in ['P']:
             logger.warn('Picture type not suppported')
        if column_type:
            name = title_to_name(fieldname,
                        blacklist=context.keys())
            if fieldname.endswith('_'):
                destname = fieldname[:-1]
            else:
                destname = fieldname
            if len(destname) < 2:
                destname = destname + '0'
            column = RDBTableColumn(parent= context,
                                name= name,
                                title=fieldname,
                                src_column_name=fieldname,
                                dest_column_name=destname,
                                column_type=column_type,
                                column_lenght=column_lenght,
                                is_pk=False)
            DBSession.add(column)
        else:
            raise TypeError(u'Unsupported type %s' % fieldinfo[0])
    dbt.close()
    tmp.close()

def extract_from_archive(data, context):
    tmp = tempfile.NamedTemporaryFile()
    tmp.file.write(data)
    tmp.file.flush()
    if tarfile.is_tarfile(tmp.name):
        tmptf = tarfile.open(tmp.name)
        for ti in tmptf.getmembers():
            if ti.isfile() and ti.size > 0 :
                tf = tmptf.extractfile(ti)
                import ipdb; ipdb.set_trace()
                tf.close()
        tmptf.close()
    elif zipfile.is_zipfile(tmp.name):
        tmpzip = zipfile.ZipFile(tmp.file)
        extensions = []
        for zi in tmpzip.infolist():
            tz = tmpzip.open(zi)
            extensions.append(zi.filename[-4:])
            #mimetypes.guess_type(filename, strict=False)
            if zi.filename.endswith('.dbf'):
                create_columns_from_dbf(tz.read(), context)
            tz.close()
        if (('.dbf' in extensions) and ('.shp' in extensions)
                                    and ('.shx' in extensions)):
            if SPATIAL:
                nfo = extract_geometry_info(data)
                column = RDBTableColumn(parent= context,
                                name='geometry',
                                title='Geometry',
                                src_column_name=None,
                                dest_column_name=nfo['name'],
                                column_type= nfo['geometry'],
                                column_lenght=2, #XXX dimensions 2 or 3
                                is_pk=False)
                DBSession.add(column)
        tmpzip.close()
    tmp.close()


def create_columns(context, request):
    if context.mimetype == 'application/x-dbf':
        create_columns_from_dbf(context.data, context)
        request.session.flash(u'Table columns created')
    elif context.mimetype in ['application/x-bzip-compressed-tar',
                            'application/x-compressed-tar',
                            #'application/x-gzip',
                            #'application/x-bzip', 'application/x-bzip2',
                            'application/zip',
                            'application/x-zip-compressed']:
        extract_from_archive(context.data, context)

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
    elif col.column_type == 'Date':
        return Column(name, Date(), primary_key=col.is_pk)
    elif col.column_type == 'DateTime':
        return Column(name, DateTime(), primary_key=col.is_pk)
    elif col.column_type in ['Point', 'LineString', 'Polygon']:
        if SPATIAL:
            return define_geo_column(col)
        else:
            logger.error('Geometry not supported, skipping column definition')
    else:
        raise TypeError('Unsupported Type %s' % col.column_type)

def define_table_columnns(context):
    columns = []
    is_spatial = False
    for col in context.children:
        if col.type == 'rdb_table_column':
            column = define_column(col)
            if column is not None:
                columns.append(column)
                if col.column_type in ['Point', 'LineString', 'Polygon']:
                    is_spatial = True
    return columns, is_spatial


def create_rdb_table(context, request):

    columns, is_spatial = define_table_columnns(context)
    if columns:
        new_table = Table(context.table_name, metadata,
                    *columns)
        engine = DBSession.connection().engine
        # create the table
        #metadata.create_all(engine)
        new_table.create(engine)
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
            if col.src_column_name:
                mapping[col.dest_column_name] = {'name': col.src_column_name,
                                                'type': col.column_type,
                                                'length': col.column_lenght}
    if context.mimetype == 'application/x-dbf':
        tmp = tempfile.NamedTemporaryFile(suffix='.dbf')
        tmp.file.write(context.data)
        tmp.file.flush()
        dbt = dbf.Table(tmp.name)
        dbt.open()
        for record in dbt:
            insert = {}
            for dest, src in mapping.iteritems():
                insert[dest] = record[src['name']]
            table.insert().values(**insert).execute()
        dbt.close()
        tmp.close()
    elif context.mimetype in ['application/zip',
                            'application/x-zip-compressed'] and SPATIAL:
        populate_geo_table(table, context.data, mapping)



