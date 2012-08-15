import colander
import deform
from kotti import DBSession
from kotti.views.edit import ContentSchema
from kotti.views.edit import generic_add
from kotti.views.edit import generic_edit
from kotti.views.view import view_node
from kotti.views.util import ensure_view_selector
from kotti.views.file import EditFileFormView
from kotti.views.file import AddFileFormView

from kotti_rdbt.resources import RDBTable
from kotti_rdbt.resources import RDBTableColumn
from kotti_rdbt import _


class AddRDBTableFormView(AddFileFormView):
    item_type = _(u"Table")
    item_class = RDBTable




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
        validator=colander.OneOf(['String', 'Integer', 'Float', ]),
        widget = deform.widget.SelectWidget(
                values=(('String','String (varchar)'),
                        ('Integer','Integer'),
                        ('Float','Float'),)
                ),
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




def includeme(config):
    includeme_edit(config)
    #includeme_view(config)
