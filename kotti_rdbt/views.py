import re

try:
    import simplejson as json
except ImportError:
    import json

import colander
import deform

from sqlalchemy import Table
# Column Types
from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Unicode

from sqlalchemy.exc import NoSuchTableError, InvalidRequestError

from pyramid.response import Response

from kotti import DBSession
from kotti import metadata

from kotti.views.form import ContentSchema
from kotti.views.edit import generic_add
from kotti.views.edit import generic_edit
from kotti.views.view import view_node
from kotti.views.util import ensure_view_selector
from kotti.views.file import EditFileFormView
from kotti.views.file import AddFileFormView
from kotti.views.file import FileUploadTempStore

from kotti_rdbt.resources import RDBTable
from kotti_rdbt.resources import RDBTableColumn
from kotti_rdbt import _
from kotti_rdbt.utils import create_columns, create_rdb_table
from kotti_rdbt.utils import populate_rdb_table, define_table_columnns

#try:
import geoalchemy2
SPATIAL = True
#except:
#    SPATIAL = False


regex = r"^[a-z]+[a-z0-9_]*[a-z0-9]+$"
check_name = re.compile(regex).match

def validate_name(node, value):
    if value is not None:
        if check_name(value) is None:
            msg = _('Table and column names must consist of lowercase letters, _ and numbers only')
            raise colander.Invalid(node, msg)


class EditDBTableFormView(EditFileFormView):
    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)

        class TableFileSchema(ContentSchema):
            file = colander.SchemaNode(
                deform.FileData(),
                title=_(u'File'),
                missing=colander.null,
                widget=deform.widget.FileUploadWidget(tmpstore),
                #validator=validate_file_size_limit,
                )
            table_name = colander.SchemaNode(
                colander.String(),
                title=_(u"Table Name"),
                validator=validate_name,
                )
        return TableFileSchema()

    def edit(self, **appstruct):
        self.context.title = appstruct['title']
        self.context.description = appstruct['description']
        self.context.tags = appstruct['tags']
        if not self.context.is_created:
            if appstruct['table_name']:
                self.context.table_name = appstruct['table_name']
            if appstruct['file']:
                buf = appstruct['file']['fp'].read()
                self.context.data = buf
                self.context.filename = appstruct['file']['filename']
                self.context.mimetype = appstruct['file']['mimetype']
                self.context.size = len(buf)


class AddRDBTableFormView(AddFileFormView):
    item_type = _(u"Table")
    item_class = RDBTable

    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)

        class TableFileSchema(ContentSchema):
            file = colander.SchemaNode(
                deform.FileData(),
                title=_(u'File'),
                widget=deform.widget.FileUploadWidget(tmpstore),
                #validator=validate_file_size_limit,
                )
            table_name = colander.SchemaNode(
                colander.String(),
                title=_(u"Table Name"),
                validator=validate_name,
                missing=None,
                )
        return TableFileSchema()


    def add(self, **appstruct):
        buf = appstruct['file']['fp'].read()
        return self.item_class(
            title=appstruct['title'],
            table_name=appstruct['table_name'],
            description=appstruct['description'],
            data=buf,
            filename=appstruct['file']['filename'],
            mimetype=appstruct['file']['mimetype'],
            size=len(buf),
            tags=appstruct['tags'],
            )


def view_rdb_table(context, request):
    if request.POST.get('create-columns') == 'extract-columns':
        create_columns(context, request)
    elif request.POST.get("create-table") == "create-and-populate":
        create_rdb_table(context, request)
        populate_rdb_table(context, request)
    result = {'columns': [], 'values': []}
    if context.is_created:
        try:
            columns, is_spatial = define_table_columnns(context)
            try:
                my_table = Table(context.table_name, metadata,
                    *columns,  autoload=True)
            except InvalidRequestError:
                my_table = Table(context.table_name, metadata, autoload=True)
            for item in my_table.columns.items():
                if type(item[1].type) in [Boolean, Date,
                                    DateTime, Integer, Unicode]:
                    result['columns'].append(item[0])
            rp = my_table.select(limit=10).execute()
            for row in rp:
                values = []
                for c in result['columns']:
                    values.append(row[c])
                result['values'].append(values)
        except NoSuchTableError:
            context.is_created = False
            request.session.flash(u'Table not found, marked as not created')
    return result



def view_rdbtable_json(context, request):
    #json_result= {"page":form.get('page', '1') ,
    #              "total":len(results),
    #              "rows":[]}
    result={ 'rows':[]}
    columns =[]
    try:
        columns, is_spatial = define_table_columnns(context)
        try:
            my_table = Table(context.table_name, metadata,
                *columns,  autoload=True)
        except InvalidRequestError:
            my_table = Table(context.table_name, metadata, autoload=True)
        cols =[]
        for item in my_table.columns.items():
            if type(item[1].type) in [Boolean, Date,
                                DateTime, Integer, Unicode]:
                cols.append(item[0])
        rp = my_table.select().execute()
        pk = my_table.primary_key
        for row in rp:
            cell = []
            ids = []
            for c in cols:
                cell.append(row[c])
            for c in pk.columns.keys():
                 ids.append(row[c])
            id = ':'.join(str(ids))
            result['rows'].append(
                {"id":id,"cell":cell})
        return Response(json.dumps(result))
    except NoSuchTableError:
        return Response('[]')





column_type_values = [('String','String (varchar)'),
                ('Integer','Integer'),
                ('Float','Float'),
                ('Date', 'Date'),
                ('DateTime', 'Date & Time'),
                ('Boolean', 'Boolean')]

if SPATIAL:
    column_type_values += [('Point', 'Geometry (Point)'),
            ('LineString', 'Geometry (LineString)'),
            ('Polygon', 'Geometry (Polygon)')]


valid_column_types = [v[0] for v in column_type_values]

class RDBTableColumnSchema(ContentSchema):
    src_column_name = colander.SchemaNode(
        colander.String(),
        title=_(u"Source Name"),
        description = _('Column Name in the uploaded table'),
        missing=None,
        )
    dest_column_name = colander.SchemaNode(
        colander.String(),
        title=_(u"Destination Name"),
        description = _('Column Name in the table to be created in the DB'),
        validator=validate_name,
        )
    column_type = colander.SchemaNode(
        colander.String(),
        title=_(u"Type"),
        missing=None,
        validator=colander.OneOf(valid_column_types),
        widget = deform.widget.SelectWidget(
                values=tuple(column_type_values)
                )
        )
    column_lenght = colander.SchemaNode(
        colander.Integer(),
        title=_(u"Lenght"),
        missing=0,
        )
    is_pk = colander.SchemaNode(
        colander.Boolean(),
        title=_(u"Primary Key"),
        )

@ensure_view_selector
def edit_column(context, request):
    if context.__parent__.is_created:
        return generic_edit(context, request, ContentSchema())
    else:
        return generic_edit(context, request, RDBTableColumnSchema())


def add_column(context, request):
    return generic_add(context, request, RDBTableColumnSchema(), RDBTableColumn, u'column')


def includeme_edit(config):

    config.add_view(
        EditDBTableFormView,
        context=RDBTable,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        AddRDBTableFormView,
        name=RDBTable.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )


    config.add_view(
        edit_column,
        context=RDBTableColumn,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        add_column,
        name=RDBTableColumn.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )

def includeme_view(config):

    config.add_view(
        view_rdb_table,
        context=RDBTable,
        name='view',
        permission='view',
        renderer='templates/table-view.pt',
        )

    config.add_view(
        view_node,
        context=RDBTableColumn,
        name='view',
        permission='view',
        renderer='templates/column-view.pt',
        )


    config.add_view(
        view_rdbtable_json,
        context=RDBTable,
        name='json',
        permission='view',
        )



def includeme(config):
    includeme_edit(config)
    includeme_view(config)
