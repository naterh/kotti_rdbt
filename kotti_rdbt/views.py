import colander
from kotti import DBSession
from kotti.views.edit import ContentSchema
from kotti.views.edit import generic_add
from kotti.views.edit import generic_edit
from kotti.views.view import view_node
from kotti.views.util import ensure_view_selector
from kotti_rdbt.resources import RDBTable
from kotti_rdbt.resources import RDBTableColumn
from kotti_rdbt import _

class RDBTableSchema(ContentSchema):
    pass


class RDBTableColumnSchema(ContentSchema):
    column_name = colander.SchemaNode(
        colander.String(),
        title=_(u"Name"),
        missing=None,
        )
    column_type = colander.SchemaNode(
        colander.String(),
        title=_(u"Type"),
        missing=None,
        )
    column_lenght = colander.SchemaNode(
        colander.Integer(),
        title=_(u"Lenght"),
        missing=None,
        )


@ensure_view_selector
def edit_table(context, request):
    return generic_edit(context, request, RDBTableSchema())


def add_table(context, request):
    return generic_add(context, request, RDBTableSchema(), RDBTable, u'table')


@ensure_view_selector
def edit_column(context, request):
    return generic_edit(context, request, RDBTableColumnSchema())


def add_column(context, request):
    return generic_add(context, request, RDBTableColumnSchema(), RDBTableColumn, u'column')


def includeme_edit(config):
    config.add_view(
        edit_table,
        context=RDBTable,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        add_table,
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
