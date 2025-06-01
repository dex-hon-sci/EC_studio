#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  8 07:12:42 2023

@author: dexter
"""

from flask import Blueprint, render_template, request

views = Blueprint("views", __name__)

@views.route("/")
def base():
    return #render_template('home.html')

@views.route("/home", methods=['GET'])
def home():
    return #render_template('index2.html')


@views.route("/risk")
def blog():
    return #render_template('blog3.html')


@views.route("/blog_index")
def blog_index():
    return #render_template('blog_index.html')

@views.route("/blog1")
def blog1():
    return #render_template('blog_content1.html')
