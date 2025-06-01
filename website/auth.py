#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 12:56:46 2023

@author: dexter
"""

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required
from .models import User

auth = Blueprint("auth", __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")

@auth.route('/sign-up', methods=['GET', 'POST'])
def sigh_up():
    username = request.form.get('username')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')
    print(username)
    return render_template("signup.html")

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("views.home"))