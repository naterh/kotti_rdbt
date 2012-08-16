import colander
import deform
from kotti import DBSession
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
from kotti_rdbt.utils import create_columns



class EditDBTableFormView(EditFileFormView):
    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)

        class TableFileSchema(ContentSchema):
            file = SchemaNode(
                FileData(),
                title=_(u'File'),
                missing=null,
                widget=deform.widget.FileUploadWidget(tmpstore),
                #validator=validate_file_size_limit,
                )
        return TableFileSchema()

    def edit(self, **appstruct):
        self.context.title = appstruct['title']
        self.context.description = appstruct['description']
        self.context.tags = appstruct['tags']
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
    return {}







class RDBTableColumnSchema(ContentSchema):
    src_column_name = colander.SchemaNode(
        colander.String(),
        title=_(u"Source Name"),
        description = _('Column Name in the uploaded table'),
        )
    dest_column_name = colander.SchemaNode(
        colander.String(),
        title=_(u"Destination Name"),
        description = _('Column Name in the table to be created in the DB'),
        )
    column_type = colander.SchemaNode(
        colander.String(),
        title=_(u"Type"),
        missing=None,
        validator=colander.OneOf(['String', 'Integer', 'Float', 'Date', 'DateTime']),
        widget = deform.widget.SelectWidget(
                values=(('String','String (varchar)'),
                        ('Integer','Integer'),
                        ('Float','Float'),
                        ('Date', 'Date'),
                        ('DateTime', 'Date & Time'),
                        ('Boolean', 'Boolean'),)
                )
        )
    column_lenght = colander.SchemaNode(
        colander.Integer(),
        title=_(u"Lenght"),
        missing=0,
        )


@ensure_view_selector
def edit_column(context, request):
    return generic_edit(context, request, RDBTableColumnSchema())


def add_column(context, request):
    return generic_add(context, request, RDBTableColumnSchema(), RDBTableColumn, u'column')


def includeme_edit(config):

    config.add_view(
        EditFileFormView,
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



def includeme(config):
    includeme_edit(config)
    includeme_view(config)
