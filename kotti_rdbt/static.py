# -*- coding: utf-8 -*-
from fanstatic import Group
from fanstatic import Library
from fanstatic import Resource
from js.jquery import jquery

lib = Library("kotti_rdbt", "static")

flexigrid_css = Resource(
    lib,
    "flexigrid.css",
    minified="flexigrid.pack.css")

flexigrid_js = Resource(
    lib,
    "flexigrid.js",
    depends=[jquery, ],
    minified="flexigrid.pack.js")

css = Group([flexigrid_css, ])
js = Group([flexigrid_js, ])

kotti_rdbt_resources = Group([css, js])
